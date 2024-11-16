import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import ta
from datetime import datetime, timedelta
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor

# Sayfanın genel ayarlarını yapılandırma
st.set_page_config(
    page_title="Crypto Scanner",
    page_icon="📊",
    layout="wide"
)

# Ana başlık
st.title("🚀 Kripto Para Tarayıcı ve Teknik Analiz Platformu")

# Sidebar oluşturma
st.sidebar.header("Filtre Ayarları")

# Zaman aralığı seçimi
time_periods = {
    "1 Gün": "1d",
    "1 Hafta": "7d",
    "1 Ay": "1mo",
    "3 Ay": "3mo",
    "6 Ay": "6mo",
    "1 Yıl": "1y"
}
selected_period = st.sidebar.selectbox("Zaman Aralığı", list(time_periods.keys()))

# Teknik gösterge filtreleri
st.sidebar.subheader("Teknik Göstergeler")

# RSI filtreleri
use_rsi = st.sidebar.checkbox("RSI Filtresi", True)
if use_rsi:
    rsi_lower = st.sidebar.slider("RSI Alt Limit", 0, 100, 30)
    rsi_upper = st.sidebar.slider("RSI Üst Limit", 0, 100, 70)

# MACD filtreleri
use_macd = st.sidebar.checkbox("MACD Filtresi", True)
if use_macd:
    macd_signal = st.sidebar.radio("MACD Sinyali", ["Kesişim Yok", "Altın Kesişim", "Ölüm Kesişimi"])

# EMA filtreleri
use_ema = st.sidebar.checkbox("EMA Filtresi", True)
if use_ema:
    ema_periods = st.sidebar.multiselect(
        "EMA Periyotları",
        [9, 20, 50, 200],
        default=[20, 50]
    )

# Bollinger Bands filtresi
use_bb = st.sidebar.checkbox("Bollinger Bantları", True)
if use_bb:
    bb_signal = st.sidebar.radio("Bollinger Sinyali", ["Bant İçi", "Üst Bant Üstü", "Alt Bant Altı"])

def get_crypto_data(symbol, period):
    """Kripto para verilerini çekme fonksiyonu"""
    try:
        data = yf.download(f"{symbol}-USD", period=time_periods[period], interval="1d")
        return data
    except:
        return None

def calculate_indicators(df):
    """Teknik göstergeleri hesaplama fonksiyonu"""
    if df is None or df.empty:
        return None
    
    # RSI hesaplama
    df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
    
    # MACD hesaplama
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    
    # EMA hesaplama
    for period in [9, 20, 50, 200]:
        df[f'EMA_{period}'] = ta.trend.EMAIndicator(df['Close'], period).ema_indicator()
    
    # Bollinger Bands hesaplama
    bollinger = ta.volatility.BollingerBands(df['Close'])
    df['BB_Upper'] = bollinger.bollinger_hband()
    df['BB_Lower'] = bollinger.bollinger_lband()
    df['BB_Middle'] = bollinger.bollinger_mavg()
    
    return df

def apply_filters(df):
    """Filtreleri uygulama fonksiyonu"""
    if df is None or df.empty:
        return False
    
    signals = []
    
    # RSI filtresi
    if use_rsi:
        last_rsi = df['RSI'].iloc[-1]
        if rsi_lower <= last_rsi <= rsi_upper:
            signals.append(True)
        else:
            return False
    
    # MACD filtresi
    if use_macd:
        macd_last = df['MACD'].iloc[-2:]
        signal_last = df['MACD_Signal'].iloc[-2:]
        
        if macd_signal == "Altın Kesişim":
            if macd_last.iloc[0] < signal_last.iloc[0] and macd_last.iloc[1] > signal_last.iloc[1]:
                signals.append(True)
            else:
                return False
        elif macd_signal == "Ölüm Kesişimi":
            if macd_last.iloc[0] > signal_last.iloc[0] and macd_last.iloc[1] < signal_last.iloc[1]:
                signals.append(True)
            else:
                return False
        else:
            signals.append(True)
    
    # EMA filtresi
    if use_ema:
        close_price = df['Close'].iloc[-1]
        ema_conditions = []
        for period in ema_periods:
            ema_value = df[f'EMA_{period}'].iloc[-1]
            ema_conditions.append(close_price > ema_value)
        if any(ema_conditions):
            signals.append(True)
        else:
            return False
    
    # Bollinger Bands filtresi
    if use_bb:
        close_price = df['Close'].iloc[-1]
        upper_band = df['BB_Upper'].iloc[-1]
        lower_band = df['BB_Lower'].iloc[-1]
        
        if bb_signal == "Üst Bant Üstü" and close_price > upper_band:
            signals.append(True)
        elif bb_signal == "Alt Bant Altı" and close_price < lower_band:
            signals.append(True)
        elif bb_signal == "Bant İçi" and lower_band < close_price < upper_band:
            signals.append(True)
        else:
            return False
    
    return len(signals) > 0

def create_chart(df, symbol):
    """Grafik oluşturma fonksiyonu"""
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
    
    # EMA çizgileri
    if use_ema:
        for period in ema_periods:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df[f'EMA_{period}'],
                name=f'EMA {period}',
                line=dict(width=1)
            ))
    
    # Bollinger Bands
    if use_bb:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['BB_Upper'],
            name='BB Üst',
            line=dict(width=1, dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['BB_Lower'],
            name='BB Alt',
            line=dict(width=1, dash='dash')
        ))
    
    fig.update_layout(
        title=f"{symbol} Teknik Analiz Grafiği",
        yaxis_title="Fiyat",
        xaxis_title="Tarih",
        height=600
    )
    
    return fig

# Ana kripto para listesi
crypto_list = [
    "BTC", "ETH", "BNB", "XRP", "ADA", "DOGE", "DOT", "UNI", "LINK", "LTC",
    "BCH", "MATIC", "XLM", "THETA", "VET", "TRX", "EOS", "XMR", "AAVE", "ATOM"
]

# Tarama işlemi
st.header("Kripto Para Taraması")

if st.button("Taramayı Başlat"):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    filtered_cryptos = []
    
    for i, symbol in enumerate(crypto_list):
        status_text.text(f"Taranan: {symbol}")
        progress_bar.progress((i + 1) / len(crypto_list))
        
        df = get_crypto_data(symbol, selected_period)
        if df is not None:
            df = calculate_indicators(df)
            if apply_filters(df):
                filtered_cryptos.append({
                    'Symbol': symbol,
                    'Price': df['Close'].iloc[-1],
                    'RSI': df['RSI'].iloc[-1],
                    'MACD': df['MACD'].iloc[-1],
                    'Volume': df['Volume'].iloc[-1]
                })
    
    status_text.text("Tarama Tamamlandı!")
    
    if filtered_cryptos:
        st.subheader("Filtrelenmiş Kripto Paralar")
        result_df = pd.DataFrame(filtered_cryptos)
        st.dataframe(result_df)
        
        # Seçilen kripto için detaylı analiz
        selected_crypto = st.selectbox("Detaylı Analiz için Kripto Seçin", result_df['Symbol'])
        if selected_crypto:
            df = get_crypto_data(selected_crypto, selected_period)
            if df is not None:
                df = calculate_indicators(df)
                fig = create_chart(df, selected_crypto)
                st.plotly_chart(fig, use_container_width=True)
                
                # Teknik gösterge değerleri
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("RSI", f"{df['RSI'].iloc[-1]:.2f}")
                with col2:
                    st.metric("MACD", f"{df['MACD'].iloc[-1]:.2f}")
                with col3:
                    st.metric("Hacim", f"{df['Volume'].iloc[-1]:,.0f}")
                with col4:
                    st.metric("Fiyat", f"${df['Close'].iloc[-1]:,.2f}")
    else:
        st.warning("Filtrelere uygun kripto para bulunamadı.")
