import streamlit as st
import pandas as pd
import numpy as np
import requests
import ta
import time

def get_binance_data(symbol, interval, limit=1000):
    """
    Binance'den historical kline data çeker
    """
    url = f"https://fapi.binance.com/fapi/v1/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # DataFrame oluştur
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                       'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                                       'taker_buy_quote', 'ignore'])
        
        # Veri tiplerini düzenle
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
            
        return df
    except Exception as e:
        st.error(f"Veri çekerken hata oluştu: {e}")
        return None

# Streamlit arayüzü
st.title('Binance Futures Analiz Paneli')

# Yan panel ayarları
with st.sidebar:
    st.header('Ayarlar')
    symbol = st.text_input('Trading Pair', 'BTCUSDT')
    interval = st.selectbox('Zaman Aralığı', 
                          options=['1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d'],
                          index=4)
    update_seconds = st.slider('Güncelleme Sıklığı (saniye)', 1, 60, 5)

# Ana panel
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time() - update_seconds

# Veriyi çek ve göster
if time.time() - st.session_state.last_update >= update_seconds:
    df = get_binance_data(symbol, interval)
    st.session_state.last_update = time.time()
    
    if df is not None:
        # Fiyat grafiği
        st.subheader('Fiyat Grafiği')
        price_chart = pd.DataFrame({
            'Zaman': df['timestamp'],
            'Fiyat': df['close']
        }).set_index('Zaman')
        st.line_chart(price_chart)
        
        # Teknik indikatörler
        st.subheader('Teknik İndikatörler')
        
        # RSI
        df['RSI'] = ta.momentum.RSIIndicator(df['close']).rsi()
        
        # MACD
        macd = ta.trend.MACD(df['close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        
        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(df['close'])
        df['BB_H'] = bollinger.bollinger_hband()
        df['BB_M'] = bollinger.bollinger_mavg()
        df['BB_L'] = bollinger.bollinger_lband()
        
        # Son değerleri göster
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("RSI", f"{df['RSI'].iloc[-1]:.2f}")
        with col2:
            st.metric("MACD", f"{df['MACD'].iloc[-1]:.2f}")
        with col3:
            current_price = df['close'].iloc[-1]
            bb_middle = df['BB_M'].iloc[-1]
            distance_to_middle = ((current_price - bb_middle) / bb_middle) * 100
            st.metric("BB Orta Bandına Uzaklık", f"{distance_to_middle:.2f}%")
        
        # İstatistikler
        st.subheader('İstatistikler')
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            price_change = ((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100
            st.metric("Fiyat Değişimi", f"{price_change:.2f}%")
        with col2:
            st.metric("24s Hacim", f"{df['volume'].sum():,.0f}")
        with col3:
            st.metric("En Yüksek", f"{df['high'].max():,.2f}")
        with col4:
            st.metric("En Düşük", f"{df['low'].min():,.2f}")
        
        # Son işlemler tablosu
        st.subheader('Son İşlemler')
        last_trades = df.tail(5)[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        last_trades.columns = ['Zaman', 'Açılış', 'Yüksek', 'Düşük', 'Kapanış', 'Hacim']
        st.dataframe(last_trades)

# Otomatik yenileme için
st.empty()
time.sleep(update_seconds)
st.experimental_rerun()
