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
        coin_map = {
            'BTCUSDT': 'bitcoin',
            'ETHUSDT': 'ethereum',
            'BNBUSDT': 'binancecoin',
            'ADAUSDT': 'cardano',
            'DOGEUSDT': 'dogecoin',
            'XRPUSDT': 'ripple',
            'SOLUSDT': 'solana',
            'MATICUSDT': 'matic-network',
            'DOTUSDT': 'polkadot',
            'LINKUSDT': 'chainlink'
        }
        
        coin_id = coin_map.get(symbol, 'bitcoin')
        
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
        df = pd.DataFrame(data['prices'], columns=['date', 'close'])
        df['volume'] = [x[1] for x in data['total_volumes']]
        
        # Timestamp düzenleme
        df['date'] = pd.to_datetime(df['date'], unit='ms')
        
        # OHLC verisi oluştur (yaklaşık değerler)
        df['open'] = df['close'].shift(1)
        df['high'] = df.groupby(df['date'].dt.date)['close'].transform('max')
        df['low'] = df.groupby(df['date'].dt.date)['close'].transform('min')
        
        if len(df) < 2:
            st.warning("Yetersiz veri alındı")
            return None
            
        return df.dropna()

    except Exception as e:
        st.error(f"Veri çekme hatası: {str(e)}")
        return None

def get_yahoo_data(symbol, period="1mo", interval="1h"):
    """Yahoo Finance'dan kripto verisi çeker"""
    try:
        yahoo_symbol = symbol.replace('USDT', '-USD')
        
        ticker = yf.Ticker(yahoo_symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty or len(df) < 2:
            st.warning("Yetersiz veri alındı")
            return None
            
        df = df.reset_index()
        df.columns = df.columns.str.lower()
        
        # date sütununu datetime'a çevir
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        elif 'datetime' in df.columns:
            df['date'] = pd.to_datetime(df['datetime'])
            df = df.drop('datetime', axis=1)
            
        return df

    except Exception as e:
        st.error(f"Yahoo Finance veri çekme hatası: {str(e)}")
        return None

def calculate_technical_indicators(df):
    """Teknik indikatörleri hesaplar"""
    if df is None or df.empty or len(df) < 2:
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
        
        return df.dropna()
        
    except Exception as e:
        st.error(f"İndikatör hesaplama hatası: {str(e)}")
        return None

def display_metrics(df):
    """Metrik panelini gösterir"""
    if df is None or df.empty or len(df) < 2:
        st.warning("Yetersiz veri: Metrikler gösterilemiyor")
        return

    try:
        current_price = df['close'].iloc[-1]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'RSI' in df.columns and not pd.isna(df['RSI'].iloc[-1]):
                rsi_value = df['RSI'].iloc[-1]
                rsi_color = 'red' if rsi_value > 70 else 'green' if rsi_value < 30 else 'off'
                st.metric("RSI", f"{rsi_value:.2f}", delta_color=rsi_color)
            else:
                st.metric("RSI", "N/A")

        with col2:
            if all(col in df.columns for col in ['MACD', 'MACD_Signal']) and \
               not pd.isna(df['MACD'].iloc[-1]) and not pd.isna(df['MACD_Signal'].iloc[-1]):
                macd_value = df['MACD'].iloc[-1]
                macd_signal = df['MACD_Signal'].iloc[-1]
                macd_diff = macd_value - macd_signal
                st.metric("MACD", f"{macd_value:.2f}", f"{macd_diff:+.2f}")
            else:
                st.metric("MACD", "N/A")

        with col3:
            if 'BB_M' in df.columns and not pd.isna(df['BB_M'].iloc[-1]):
                bb_middle = df['BB_M'].iloc[-1]
                distance = ((current_price - bb_middle) / bb_middle) * 100
                st.metric("BB Orta Bant Uzaklığı", f"{distance:.2f}%")
            else:
                st.metric("BB Orta Bant Uzaklığı", "N/A")

        with col4:
            if len(df) >= 2:
                prev_price = df['close'].iloc[-2]
                if prev_price != 0:  # Sıfıra bölme hatasını önle
                    price_change = ((current_price / prev_price) - 1) * 100
                    st.metric("Son Fiyat", f"{current_price:.2f}", f"{price_change:+.2f}%")
                else:
                    st.metric("Son Fiyat", f"{current_price:.2f}", "N/A")
            else:
                st.metric("Son Fiyat", f"{current_price:.2f}", "N/A")

    except Exception as e:
        st.error(f"Metrik hesaplama hatası: {str(e)}")

def display_chart(df):
    """Fiyat ve indikatör grafiklerini gösterir"""
    if df is None or df.empty or len(df) < 2:
        st.warning("Yetersiz veri: Grafikler gösterilemiyor")
        return

    try:
        # Fiyat ve EMA grafiği
        st.subheader('Fiyat ve EMA Grafiği')
        price_chart = pd.DataFrame({
            'Fiyat': df['close'],
            'EMA 9': df['EMA_9'],
            'EMA 20': df['EMA_20'],
            'EMA 50': df['EMA_50']
        }, index=df['date'])
        st.line_chart(price_chart)
        
        # RSI grafiği
        st.subheader('RSI Grafiği')
        rsi_chart = pd.DataFrame({
            'RSI': df['RSI']
        }, index=df['date'])
        st.line_chart(rsi_chart)
        
        # MACD grafiği
        st.subheader('MACD Grafiği')
        macd_chart = pd.DataFrame({
            'MACD': df['MACD'],
            'Signal': df['MACD_Signal'],
            'Histogram': df['MACD_Hist']
        }, index=df['date'])
        st.line_chart(macd_chart)

    except Exception as e:
        st.error(f"Grafik oluşturma hatası: {str(e)}")

def main():
    st.set_page_config(page_title="Kripto Analiz Paneli", layout="wide")
    
    st.title('Kripto Analiz Paneli')
    
    # Sidebar ayarları
    with st.sidebar:
        st.header('Ayarlar')
        symbol = st.text_input('Trading Pair', 'BTCUSDT').upper()
        data_source = st.radio('Veri Kaynağı', ['CoinGecko', 'Yahoo Finance'])
        
        if data_source == 'Yahoo Finance':
            period = st.selectbox('Periyod',
                                options=['1d', '5d', '1mo', '3mo', '6mo', '1y'],
                                index=2)
            interval = st.selectbox('Interval',
                                  options=['1h', '1d'],
                                  index=0)
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
                # Veri çek
                if data_source == 'CoinGecko':
                    df = get_coingecko_data(symbol, days)
                else:
                    df = get_yahoo_data(symbol, period, interval)
                
                if df is None:
                    status_container.warning("Veri alınamadı. Yeniden deneniyor...")
                    time.sleep(update_seconds)
                    continue
                    
                if len(df) < 2:
                    status_container.warning("Yetersiz veri. Yeniden deneniyor...")
                    time.sleep(update_seconds)
                    continue
                
                # İndikatörleri hesapla
                df = calculate_technical_indicators(df)
                
                if df is not None and not df.empty:
                    # Grafikleri göster
                    with chart_container:
                        display_chart(df)
                    
                    # Metrikleri göster
                    with metrics_container:
                        st.subheader('Teknik İndikatörler')
                        display_metrics(df)
                    
                    status_container.success(f"Son güncelleme: {datetime.now().strftime('%H:%M:%S')}")
                
            time.sleep(update_seconds)
            
        except Exception as e:
            status_container.error(f"Beklenmeyen hata: {str(e)}")
            time.sleep(update_seconds)

if __name__ == "__main__":
    main()
