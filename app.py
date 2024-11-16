import streamlit as st
import pandas as pd
import numpy as np
import ta
from binance.client import Client

# Binance API anahtarları (dummy değerlerle değiştirin)
API_KEY = "2cQLCcQB3XCXNasp5VCt3n5qe5GeSw7F3S2aUhJJPzjfUiQLyX9xtpwCt10O57AP"
API_SECRET = "lMkmtovUAwTJpTon919pAtxubvffWJE1ZKxNpiWRKY1NL3zo1J8k1jn6KLYqzRla"

client = Client(API_KEY, API_SECRET)

# Kripto veri alma fonksiyonu
@st.cache
def get_crypto_data(symbol, interval):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval)
        df = pd.DataFrame(klines, columns=[
            'Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 
            'Close time', 'Quote asset volume', 'Number of trades',
            'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'
        ])
        df['Close'] = df['Close'].astype(float)
        df['Volume'] = df['Volume'].astype(float)
        df['Open time'] = pd.to_datetime(df['Open time'], unit='ms')
        return df
    except Exception as e:
        st.error(f"Veri çekilirken hata oluştu: {e}")
        return None

# Göstergeleri hesaplama
def calculate_indicators(df, ema_period):
    try:
        df['EMA'] = ta.trend.ema_indicator(df['Close'], window=ema_period)
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        return df
    except Exception as e:
        st.error(f"Göstergeler hesaplanırken hata oluştu: {e}")
        return None

# Arayüz Başlangıcı
st.title("Kripto Para Filtreleme ve Analiz Aracı")
st.sidebar.header("Filtre Ayarları")

# Kullanıcıdan filtreleme seçeneklerini al
use_rsi = st.sidebar.checkbox("RSI Kullan", value=True)
use_ema = st.sidebar.checkbox("EMA Kullan", value=True)
use_macd = st.sidebar.checkbox("MACD Kullan", value=False)

if use_rsi:
    rsi_lower = st.sidebar.slider("RSI Alt Limit", 0, 100, 20)
    rsi_upper = st.sidebar.slider("RSI Üst Limit", 0, 100, 80)

if use_ema:
    ema_period = st.sidebar.number_input("EMA Periyodu", min_value=5, max_value=200, value=50)

# Binance zaman aralığı
period_options = {
    "1 dakika": "1m",
    "5 dakika": "5m",
    "15 dakika": "15m",
    "1 saat": "1h",
    "1 gün": "1d"
}
selected_period = st.sidebar.selectbox("Zaman Aralığı", list(period_options.keys()))

# İzlenecek kripto paraları seç
crypto_list = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]
filtered_cryptos = []

# Veri çekme ve filtreleme
for symbol in crypto_list:
    df = get_crypto_data(symbol, period_options[selected_period])
    if df is not None:
        df = calculate_indicators(df, ema_period)
        if df is not None:
            last_close = df['Close'].iloc[-1]
            last_rsi = df['RSI'].iloc[-1] if 'RSI' in df else None
            ema_value = df['EMA'].iloc[-1] if 'EMA' in df else None
            macd = df['MACD'].iloc[-1] if 'MACD' in df else None
            signal = df['MACD_Signal'].iloc[-1] if 'MACD_Signal' in df else None

            meets_criteria = True

            # RSI Filtresi
            if use_rsi and (pd.isna(last_rsi) or not (rsi_lower <= last_rsi <= rsi_upper)):
                meets_criteria = False

            # EMA Filtresi
            if use_ema and meets_criteria and (pd.isna(ema_value) or not (last_close > ema_value)):
                meets_criteria = False

            # MACD Filtresi
            if use_macd and meets_criteria and (pd.isna(macd) or macd <= signal):
                meets_criteria = False

            # Filtreleme sonuçları
            if meets_criteria:
                filtered_cryptos.append({
                    "Sembol": symbol,
                    "Fiyat": last_close,
                    "RSI": last_rsi,
                    "EMA": ema_value,
                    "MACD": macd
                })

# Filtrelenen sonuçları göster
if filtered_cryptos:
    st.success("Filtreye uygun kripto paralar bulundu:")
    st.table(filtered_cryptos)
else:
    st.warning("Filtrelere uygun kripto para bulunamadı.")
