import streamlit as st
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import plotly.graph_objects as go
from binance.client import Client
from binance.exceptions import BinanceAPIException
import time

# Initialize session state for Binance client
if 'binance_client' not in st.session_state:
    try:
        st.session_state.binance_client = Client(None, None)
    except Exception as e:
        st.error(f"Failed to initialize Binance client. Please try again later. Error: {str(e)}")
        st.stop()

@st.cache_data(ttl=300)
def get_crypto_data(symbol, interval, lookback):
    """Fetch crypto data from Binance with retry mechanism"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            klines = st.session_state.binance_client.get_historical_klines(
                symbol=f"{symbol}USDT",
                interval=interval,
                start_str=f"{lookback} days ago UTC"
            )
            
            if not klines:
                return None
                
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df[numeric_columns] = df[numeric_columns].astype(float)
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except BinanceAPIException as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            st.warning(f"Could not fetch data for {symbol}: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Unexpected error while fetching {symbol} data: {str(e)}")
            return None
    
    return None

# Time interval options
period_options = {
    "1 Minute": "1m",
    "3 Minutes": "3m",
    "5 Minutes": "5m",
    "15 Minutes": "15m",
    "30 Minutes": "30m",
    "1 Hour": "1h",
    "2 Hours": "2h",
    "4 Hours": "4h",
    "6 Hours": "6h",
    "8 Hours": "8h",
    "12 Hours": "12h",
    "1 Day": "1d",
    "3 Days": "3d",
    "1 Week": "1w",
    "1 Month": "1M"
}

# Lookback period settings
lookback_options = {
    "1 Day": 1,
    "3 Days": 3,
    "1 Week": 7,
    "2 Weeks": 14,
    "1 Month": 30,
    "3 Months": 90,
    "6 Months": 180,
    "1 Year": 365
}

# Streamlit interface
st.set_page_config(page_title="Crypto Scanner", page_icon="📊", layout="wide")
st.title("📊 Crypto Technical Analysis Platform")

# Sidebar configuration
with st.sidebar:
    st.header("Filter Settings")
    
    # Time interval selection
    selected_period = st.selectbox("Candle Interval", list(period_options.keys()))
    selected_lookback = st.selectbox("Historical Data Period", list(lookback_options.keys()))
    
    # Technical indicator filters
    st.subheader("Technical Indicators")
    
    use_rsi = st.checkbox("RSI Filter", True)
    if use_rsi:
        rsi_lower = st.slider("RSI Lower Limit", 0, 100, 30)
        rsi_upper = st.slider("RSI Upper Limit", 0, 100, 70)
    
    use_ema = st.checkbox("EMA Filter", True)
    if use_ema:
        ema_period = st.selectbox("EMA Period", [9, 20, 50, 200], index=1)
    
    use_macd = st.checkbox("MACD Filter", True)

def calculate_indicators(df):
    """Calculate technical indicators"""
    if df is None or df.empty:
        return None
    
    try:
        # RSI
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        
        # EMA
        if use_ema:
            df[f'EMA_{ema_period}'] = ta.trend.EMAIndicator(
                df['Close'], 
                window=ema_period
            ).ema_indicator()
        
        # MACD
        if use_macd:
            macd = ta.trend.MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
        
        return df
    except Exception as e:
        st.error(f"Error calculating indicators: {str(e)}")
        return None

def create_chart(df, symbol):
    """Create interactive chart"""
    if df is None or df.empty:
        return None
    
    try:
        fig = go.Figure()
        
        # Candlestick chart
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=symbol
        ))
        
        # EMA
        if use_ema and f'EMA_{ema_period}' in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df[f'EMA_{ema_period}'],
                name=f'EMA {ema_period}',
                line=dict(width=1)
            ))
        
        fig.update_layout(
            title=f"{symbol} Technical Analysis Chart",
            yaxis_title="Price (USDT)",
            xaxis_title="Date",
            height=600,
            template="plotly_dark"
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")
        return None

# Popular cryptocurrencies traded on Binance
crypto_list = [
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "MATIC",
    "DOT", "LINK", "UNI", "ATOM", "LTC", "DOGE", "SHIB", "TRX"
]

# Main section
st.header("Crypto Scanner")

if st.button("Start Scan"):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    filtered_cryptos = []
    interval = period_options[selected_period]
    lookback = lookback_options[selected_lookback]
    
    for i, symbol in enumerate(crypto_list):
        status_text.text(f"Scanning: {symbol}")
        progress_bar.progress((i + 1) / len(crypto_list))
        
        df = get_crypto_data(symbol, interval, lookback)
        if df is not None:
            df = calculate_indicators(df)
            if df is not None and not df.empty:
                last_close = df['Close'].iloc[-1]
                
                # Initialize criteria checking
                meets_criteria = True
                
                # RSI check
                if use_rsi and 'RSI' in df.columns:
                    last_rsi = df['RSI'].iloc[-1]
                    meets_criteria &= rsi_lower <= last_rsi <= rsi_upper
                
                # EMA check
                if use_ema and meets_criteria and f'EMA_{ema_period}' in df.columns:
                    meets_criteria &= last_close > df[f'EMA_{ema_period}'].iloc[-1]
                
                # MACD check
                if use_macd and meets_criteria and 'MACD' in df.columns and 'MACD_Signal' in df.columns:
                    last_macd = df['MACD'].iloc[-1]
                    last_signal = df['MACD_Signal'].iloc[-1]
                    meets_criteria &= last_macd > last_signal
                
                if meets_criteria:
                    filtered_cryptos.append({
                        'Symbol': symbol,
                        'Price': last_close,
                        'RSI': df['RSI'].iloc[-1] if 'RSI' in df.columns else None,
                        'Change (%)': ((last_close - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100).round(2),
                        'Volume': df['Volume'].iloc[-1]
                    })
    
    status_text.text("Scan Complete!")
    
    if filtered_cryptos:
        st.subheader("Filtered Cryptocurrencies")
        result_df = pd.DataFrame(filtered_cryptos)
        st.dataframe(result_df)
        
        # Detailed analysis for selected crypto
        selected_crypto = st.selectbox("Select Cryptocurrency for Detailed Analysis", result_df['Symbol'])
        if selected_crypto:
            df = get_crypto_data(selected_crypto, interval, lookback)
            if df is not None:
                df = calculate_indicators(df)
                if df is not None:
                    fig = create_chart(df, selected_crypto)
                    if fig is not None:
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Metrics display
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Price (USDT)", f"${df['Close'].iloc[-1]:,.2f}")
                        with col2:
                            if 'RSI' in df.columns:
                                st.metric("RSI", f"{df['RSI'].iloc[-1]:.2f}")
                        with col3:
                            st.metric("24h Change (%)", 
                                    f"{((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100):.2f}%")
                        with col4:
                            st.metric("Volume", f"{df['Volume'].iloc[-1]:,.0f}")
    else:
        st.warning("No cryptocurrencies found matching the current filters.")
