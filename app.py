import streamlit as st
import pandas as pd
import numpy as np
import requests
import ta
import time
from datetime import datetime

# Konfigürasyon sabitleri
SPOT_BASE_URL = "https://api.binance.com"
FUTURES_BASE_URL = "https://fapi.binance.com"
DEFAULT_TIMEOUT = 10

def check_api_status():
    """API bağlantı durumunu kontrol eder"""
    try:
        response = requests.get(f"{SPOT_BASE_URL}/api/v3/time", timeout=DEFAULT_TIMEOUT)
        return response.status_code == 200
    except:
        return False

def get_binance_data(symbol, interval, use_futures=False, limit=1000):
    """
    Binance'den kline verilerini çeker
    
    Parameters:
    -----------
    symbol : str
        Trading pair (örn. 'BTCUSDT')
    interval : str
        Zaman aralığı (örn. '1h', '4h')
    use_futures : bool
        Futures API kullanılıp kullanılmayacağı
    limit : int
        Çekilecek veri sayısı
    """
    base_url = FUTURES_BASE_URL if use_futures else SPOT_BASE_URL
    endpoint = f"{base_url}/{'fapi' if use_futures else 'api'}/v{'1' if use_futures else '3'}/klines"
    
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit
    }
    
    try:
        st.write(f"Veri çekiliyor: {endpoint}")
        
        response = requests.get(endpoint, params=params, timeout=DEFAULT_TIMEOUT)
        
        # Hata kontrolü
        if response.status_code == 451:
            st.error("Bölgesel kısıtlama nedeniyle erişim engellendi. Spot piyasa verilerine geçiş yapılıyor...")
            if use_futures:
                return get_binance_data(symbol, interval, use_futures=False, limit=limit)
            return None
        
        if response.status_code != 200:
            st.error(f"API Hatası: Status Code {response.status_code}")
            st.write(f"API Yanıtı: {response.text}")
            return None
            
        data = response.json()
        
        if not data or len(data) == 0:
            st.error(f"Veri bulunamadı: {symbol}")
            return None
        
        # DataFrame oluşturma
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                       'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                                       'taker_buy_quote', 'ignore'])
        
        # Veri tipleri dönüşümü
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        df[numeric_columns] = df[numeric_columns].astype(float)
        
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

def calculate_technical_indicators(df):
    """Teknik indikatörleri hesaplar"""
    if df is None or df.empty:
        return None
        
    try:
        # RSI
        df['RSI'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        
        # MACD
        macd = ta.trend.MACD(df['close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Hist'] = macd.macd_diff()
        
        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(df['close'])
        df['BB_H'] = bollinger.bollinger_hband()
        df['BB_M'] = bollinger.bollinger_mavg()
        df['BB_L'] = bollinger.bollinger_lband()
        
        # EMA'lar
        df['EMA_9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
        df['EMA_20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
        df['EMA_50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
        
        return df
    except Exception as e:
        st.error(f"İndikatör hesaplama hatası: {e}")
        return None

def display_metrics(df):
    """Metrik panelini gösterir"""
    if df is None or df.empty:
        return
        
    current_price = df['close'].iloc[-1]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if not pd.isna(df['RSI'].iloc[-1]):
            rsi_value = df['RSI'].iloc[-1]
            rsi_color = 'red' if rsi_value > 70 else 'green' if rsi_value < 30 else 'normal'
            st.metric("RSI", f"{rsi_value:.2f}", delta_color=rsi_color)
        else:
            st.metric("RSI", "N/A")
            
    with col2:
        if not pd.isna(df['MACD'].iloc[-1]):
            macd_value = df['MACD'].iloc[-1]
            macd_signal = df['MACD_Signal'].iloc[-1]
            macd_diff = macd_value - macd_signal
            st.metric("MACD", f"{macd_value:.2f}", f"{macd_diff:+.2f}")
        else:
            st.metric("MACD", "N/A")
            
    with col3:
        if not pd.isna(df['BB_M'].iloc[-1]):
            bb_middle = df['BB_M'].iloc[-1]
            distance = ((current_price - bb_middle) / bb_middle) * 100
            st.metric("BB Orta Bant Uzaklığı", f"{distance:.2f}%")
        else:
            st.metric("BB Orta Bant Uzaklığı", "N/A")
            
    with col4:
        price_change = ((current_price / df['close'].iloc[-2]) - 1) * 100
        st.metric("Son Fiyat", f"{current_price:.2f}", f"{price_change:+.2f}%")

def main():
    st.set_page_config(page_title="Binance Analiz Paneli", layout="wide")
    
    st.title('Binance Analiz Paneli')
    
    # Sidebar ayarları
    with st.sidebar:
        st.header('Ayarlar')
        symbol = st.text_input('Trading Pair', 'BTCUSDT')
        interval = st.selectbox('Zaman Aralığı', 
                              options=['1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d'],
                              index=4)
        use_futures = st.checkbox('Futures Verisi Kullan', value=False)
        update_seconds = st.slider('Güncelleme Sıklığı (saniye)', 1, 60, 5)

    # Ana panel
    status_container = st.empty()
    chart_container = st.container()
    metrics_container = st.container()
    
    while True:
        try:
            if not check_api_status():
                status_container.error("Binance API'ye erişilemiyor. Bağlantı kontrol ediliyor...")
                time.sleep(5)
                continue
                
            with st.spinner('Veri güncelleniyor...'):
                df = get_binance_data(symbol, interval, use_futures)
                
                if df is not None and not df.empty:
                    df = calculate_technical_indicators(df)
                    
                    with chart_container:
                        st.subheader('Fiyat Grafiği')
                        price_chart = pd.DataFrame({
                            'Fiyat': df['close'],
                            'EMA 9': df['EMA_9'],
                            'EMA 20': df['EMA_20'],
                            'EMA 50': df['EMA_50']
                        }, index=df['timestamp'])
                        st.line_chart(price_chart)
                    
                    with metrics_container:
                        st.subheader('Teknik İndikatörler')
                        display_metrics(df)
                    
                    status_container.success(f"Son güncelleme: {datetime.now().strftime('%H:%M:%S')}")
                else:
                    status_container.warning("Veri alınamadı. Yeniden deneniyor...")
                    
            time.sleep(update_seconds)
            
        except Exception as e:
            status_container.error(f"Hata oluştu: {e}")
            time.sleep(update_seconds)

if __name__ == "__main__":
    main()
