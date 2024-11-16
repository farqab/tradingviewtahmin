import streamlit as st
import pandas as pd
import numpy as np
import requests
import ta
import time

def get_binance_data(symbol, interval, limit=1000):
    # URL'yi futures endpointi olarak değiştirelim
    base_url = "https://fapi.binance.com"
    endpoint = f"{base_url}/fapi/v1/klines"
    
    params = {
        "symbol": symbol.upper(),  # Symbol'ü büyük harfe çevirelim
        "interval": interval,
        "limit": limit
    }
    
    try:
        # Debug için request URL'sini yazdıralım
        st.write(f"Requesting: {endpoint}")
        
        response = requests.get(endpoint, params=params, timeout=10)
        
        # HTTP durumunu kontrol edelim
        if response.status_code != 200:
            st.error(f"API Hatası: Status Code {response.status_code}")
            st.write(f"API Yanıtı: {response.text}")
            return None
            
        data = response.json()
        
        if not data or len(data) == 0:
            st.error(f"Veri bulunamadı: {symbol}")
            return None
            
        # DataFrame oluşturmadan önce veriyi kontrol edelim
        st.write(f"Alınan veri sayısı: {len(data)}")
        
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                       'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                                       'taker_buy_quote', 'ignore'])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        # Debug için DataFrame'in ilk birkaç satırını gösterelim
        st.write("DataFrame örnek veri:")
        st.write(df.head())
            
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Bağlantı hatası: {e}")
        return None
    except ValueError as e:
        st.error(f"Veri işleme hatası: {e}")
        return None
    except Exception as e:
        st.error(f"Beklenmeyen hata: {e}")
        return None

st.title('Binance Futures Analiz Paneli')

with st.sidebar:
    st.header('Ayarlar')
    symbol = st.text_input('Trading Pair', 'BTCUSDT')
    interval = st.selectbox('Zaman Aralığı', 
                          options=['1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d'],
                          index=4)
    update_seconds = st.slider('Güncelleme Sıklığı (saniye)', 1, 60, 5)

# Durum göstergesi ekleyelim
status_container = st.empty()

while True:
    try:
        with st.spinner('Veri güncelleniyor...'):
            df = get_binance_data(symbol, interval)
            
            if df is not None and not df.empty:
                # Mevcut grafik ve metrikler kodu...
                
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
                    if not pd.isna(df['RSI'].iloc[-1]):
                        st.metric("RSI", f"{df['RSI'].iloc[-1]:.2f}")
                    else:
                        st.metric("RSI", "N/A")
                        
                with col2:
                    if not pd.isna(df['MACD'].iloc[-1]):
                        st.metric("MACD", f"{df['MACD'].iloc[-1]:.2f}")
                    else:
                        st.metric("MACD", "N/A")
                        
                with col3:
                    current_price = df['close'].iloc[-1]
                    bb_middle = df['BB_M'].iloc[-1]
                    if not pd.isna(bb_middle) and bb_middle != 0:
                        distance_to_middle = ((current_price - bb_middle) / bb_middle) * 100
                        st.metric("BB Orta Bandına Uzaklık", f"{distance_to_middle:.2f}%")
                    else:
                        st.metric("BB Orta Bandına Uzaklık", "N/A")
                
                # Son güncelleme zamanını göster
                status_container.success(f"Son güncelleme: {pd.Timestamp.now().strftime('%H:%M:%S')}")
            else:
                status_container.warning("Veri alınamadı. Yeniden deneniyor...")
                
        time.sleep(update_seconds)
        
    except Exception as e:
        status_container.error(f"Hata oluştu: {e}")
        time.sleep(update_seconds)
