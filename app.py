import streamlit as st
import pandas as pd
import numpy as np
from binance.client import Client
import ta
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Binance client oluşturma (API key olmadan da çalışır)
client = Client()

@st.cache_data(ttl=300)
def get_crypto_data(symbol, interval, lookback):
    """Kripto para verilerini Binance'den çekme fonksiyonu"""
    try:
        # Binance kline intervals: 1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w,1M
        klines = client.get_historical_klines(
            symbol=f"{symbol}USDT",
            interval=interval,
            start_str=f"{lookback} days ago UTC"
        )
        
        # DataFrame oluşturma
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # Veri tiplerini düzenleme
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df[numeric_columns] = df[numeric_columns].astype(float)
        
        # Index'i timestamp yapma
        df.set_index('timestamp', inplace=True)
        
        return df
    except Exception as e:
        st.error(f"Veri çekilirken hata oluştu: {str(e)}")
        return None

# Zaman aralığı seçeneklerini güncelleme
period_options = {
    # Dakikalık
    "1 Dakika": "1m",
    "3 Dakika": "3m",
    "5 Dakika": "5m",
    "15 Dakika": "15m",
    "30 Dakika": "30m",
    # Saatlik
    "1 Saat": "1h",
    "2 Saat": "2h",
    "4 Saat": "4h",
    "6 Saat": "6h",
    "8 Saat": "8h",
    "12 Saat": "12h",
    # Günlük ve üzeri
    "1 Gün": "1d",
    "3 Gün": "3d",
    "1 Hafta": "1w",
    "1 Ay": "1M"
}

# Lookback period ayarları
lookback_options = {
    "1 Gün": 1,
    "3 Gün": 3,
    "1 Hafta": 7,
    "2 Hafta": 14,
    "1 Ay": 30,
    "3 Ay": 90,
    "6 Ay": 180,
    "1 Yıl": 365
}

# Streamlit arayüzü
st.set_page_config(page_title="Kripto Tarayıcı", page_icon="📊", layout="wide")
st.title("📊 Kripto Para Teknik Analiz Platformu")

# Sidebar
with st.sidebar:
    st.header("Filtre Ayarları")
    
    # Zaman aralığı seçimi
    selected_period = st.selectbox("Mum Aralığı", list(period_options.keys()))
    selected_lookback = st.selectbox("Geçmiş Veri Süresi", list(lookback_options.keys()))
    
    # Teknik gösterge filtreleri
    st.subheader("Teknik Göstergeler")
    
    use_rsi = st.checkbox("RSI Filtresi", True)
    if use_rsi:
        rsi_lower = st.slider("RSI Alt Limit", 0, 100, 30)
        rsi_upper = st.slider("RSI Üst Limit", 0, 100, 70)
    
    use_ema = st.checkbox("EMA Filtresi", True)
    if use_ema:
        ema_period = st.selectbox("EMA Periyodu", [9, 20, 50, 200], index=1)
    
    use_macd = st.checkbox("MACD Filtresi", True)

def calculate_indicators(df):
    """Teknik göstergeleri hesaplama"""
    if df is None or df.empty:
        return None
    
    try:
        # RSI
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        
        # EMA
        df[f'EMA_{ema_period}'] = ta.trend.EMAIndicator(df['Close'], window=ema_period).ema_indicator()
        
        # MACD
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        
        return df
    except Exception as e:
        st.error(f"Göstergeler hesaplanırken hata oluştu: {str(e)}")
        return None

def create_chart(df, symbol):
    """Grafik oluşturma"""
    if df is None or df.empty:
        return None
    
    try:
        fig = go.Figure()
        
        # Mum grafiği
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=symbol
        ))
        
        # EMA
        if use_ema:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df[f'EMA_{ema_period}'],
                name=f'EMA {ema_period}',
                line=dict(width=1)
            ))
        
        fig.update_layout(
            title=f"{symbol} Teknik Analiz Grafiği",
            yaxis_title="Fiyat (USDT)",
            xaxis_title="Tarih",
            height=600,
            template="plotly_dark"
        )
        
        return fig
    except Exception as e:
        st.error(f"Grafik oluşturulurken hata oluştu: {str(e)}")
        return None

# Binance'de işlem gören popüler kriptolar
crypto_list = [
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "MATIC",
    "DOT", "LINK", "UNI", "ATOM", "LTC", "DOGE", "SHIB", "TRX",
    "ETC", "FIL", "NEAR", "ALGO", "VET", "SAND", "MANA", "AXS"
]

# Ana bölüm
st.header("Kripto Para Taraması")

if st.button("Taramayı Başlat"):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    filtered_cryptos = []
    interval = period_options[selected_period]
    lookback = lookback_options[selected_lookback]
    
    for i, symbol in enumerate(crypto_list):
        status_text.text(f"Taranan: {symbol}")
        progress_bar.progress((i + 1) / len(crypto_list))
        
        df = get_crypto_data(symbol, interval, lookback)
        if df is not None:
            df = calculate_indicators(df)
            if df is not None:
                last_close = df['Close'].iloc[-1]
                last_rsi = df['RSI'].iloc[-1]
                
                # Filtreleme mantığı
                meets_criteria = True
                
                if use_rsi:
                    meets_criteria &= rsi_lower <= last_rsi <= rsi_upper
                
                if use_ema and meets_criteria:
                    meets_criteria &= last_close > df[f'EMA_{ema_period}'].iloc[-1]
                
                if use_macd and meets_criteria:
                    last_macd = df['MACD'].iloc[-1]
                    last_signal = df['MACD_Signal'].iloc[-1]
                    meets_criteria &= last_macd > last_signal
                
                if meets_criteria:
                    filtered_cryptos.append({
                        'Symbol': symbol,
                        'Price': last_close,
                        'RSI': last_rsi,
                        'Son Değişim (%)': ((last_close - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100).round(2),
                        'Hacim': df['Volume'].iloc[-1]
                    })
    
    status_text.text("Tarama Tamamlandı!")
    
    if filtered_cryptos:
        st.subheader("Filtrelenmiş Kripto Paralar")
        result_df = pd.DataFrame(filtered_cryptos)
        st.dataframe(result_df)
        
        # Seçilen kripto için detaylı analiz
        selected_crypto = st.selectbox("Detaylı Analiz için Kripto Seçin", result_df['Symbol'])
        if selected_crypto:
            df = get_crypto_data(selected_crypto, interval, lookback)
            if df is not None:
                df = calculate_indicators(df)
                if df is not None:
                    fig = create_chart(df, selected_crypto)
                    if fig is not None:
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Metrikler
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Fiyat (USDT)", f"${df['Close'].iloc[-1]:,.2f}")
                        with col2:
                            st.metric("RSI", f"{df['RSI'].iloc[-1]:.2f}")
                        with col3:
                            st.metric("Son Değişim (%)", 
                                    f"{((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100):.2f}%")
                        with col4:
                            st.metric("Hacim", f"{df['Volume'].iloc[-1]:,.0f}")
    else:
        st.warning("Filtrelere uygun kripto para bulunamadı.")
