import streamlit as st
import pandas as pd
import numpy as np
import requests
import ta
import time
from datetime import datetime, timedelta
import yfinance as yf

def get_coingecko_data(symbol, days=30):
    """CoinGecko'dan kripto verisi çeker"""
    try:
        # Symbol düzenleme (BTCUSDT -> bitcoin)
        coin_map = {
            'BTCUSDT': 'bitcoin',
            'ETHUSDT': 'ethereum',
            'BNBUSDT': 'binancecoin',
            'ADAUSDT': 'cardano',
            'DOGEUSDT': 'dogecoin',
            'XRPUSDT': 'ripple',
            # Diğer coinler buraya eklenebilir
        }
        
        coin_id = coin_map.get(symbol, 'bitcoin')  # Varsayılan olarak bitcoin
        
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'hourly'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            st.error(f"CoinGecko API Hatası: {response.status_code}")
            return None
            
        data = response.json()
        
        # Veriyi DataFrame'e dönüştür
        prices = data['prices']
        volumes = data['total_volumes']
        
        df = pd.DataFrame(prices, columns=['timestamp', 'close'])
        df['volume'] = pd.DataFrame(volumes, columns=['timestamp', 'volume'])['volume']
        
        # Timestamp düzenleme
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # OHLC verisi oluştur (CoinGecko sadece kapanış fiyatı veriyor)
        df['open'] = df['close'].shift(1)
        df['high'] = df['close']
        df['low'] = df['close']
        
        return df.dropna()
        
    except Exception as e:
        st.error(f"Veri çekme hatası: {e}")
        return None

def get_yahoo_data(symbol, period="1mo", interval="1h"):
    """Yahoo Finance'dan kripto verisi çeker"""
    try:
        # Symbol düzenleme (BTCUSDT -> BTC-USD)
        yahoo_symbol = symbol.replace('USDT', '-USD')
        
        ticker = yf.Ticker(yahoo_symbol)
        df = ticker.history(period=period, interval=interval)
        
        # DataFrame düzenleme
        df = df.reset_index()
        df.columns = df.columns.str.lower()
        df = df.rename(columns={'date': 'timestamp'})
        
        return df
        
    except Exception as e:
        st.error(f"Yahoo Finance veri çekme hatası: {e}")
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
    st.set_page_config(page_title="Kripto Analiz Paneli", layout="wide")
    
    st.title('Kripto Analiz Paneli')
    
    # Sidebar ayarları
    with st.sidebar:
        st.header('Ayarlar')
        symbol = st.text_input('Trading Pair', 'BTCUSDT')
        data_source = st.radio('Veri Kaynağı', ['CoinGecko', 'Yahoo Finance'])
        if data_source == 'Yahoo Finance':
            period = st.selectbox('Periyod', 
                                options=['1d', '5d', '1mo', '3mo', '6mo', '1y'],
                                index=2)
            interval = st.selectbox('Interval',
                                  options=['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d'],
                                  index=7)
        else:
            days = st.slider('Gün Sayısı', 1, 365, 30)
            
        update_seconds = st.slider('Güncelleme Sıklığı (saniye)', 30, 300, 60)

    # Ana panel
    status_container = st.empty()
    chart_container = st.container()
    metrics_container = st.container()
    
    while True:
        try:
            with st.spinner('Veri güncelleniyor...'):
                if data_source == 'CoinGecko':
                    df = get_coingecko_data(symbol, days)
                else:
                    df = get_yahoo_data(symbol, period, interval)
                
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
