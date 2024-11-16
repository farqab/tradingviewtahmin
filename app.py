import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Sayfa yapılandırması
st.set_page_config(page_title="Yatırım Portföyü Oluşturucu", layout="wide")

# Ana başlık
st.title("Kişisel Yatırım Portföyü Oluşturucu")

# Borsa verilerini çekme fonksiyonu
@st.cache_data(ttl=3600)  # 1 saat cache
def get_stock_data(ticker, period='1y'):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            st.warning(f"{ticker} için veri bulunamadı.")
            return None
        return hist
    except Exception as e:
        st.error(f"Veri çekilirken hata oluştu: {e}")
        return None

# BIST ve global endeksleri tanımlama
INDICES = {
    'BIST 100': '^XU100.IS',
    'S&P 500': '^GSPC',
    'NASDAQ': '^IXIC',
    'DAX': '^GDAXI'
}

# Popüler Türk hisseleri
TURKISH_STOCKS = {
    'Garanti Bankası': 'GARAN.IS',
    'Koç Holding': 'KCHOL.IS',
    'Ereğli Demir Çelik': 'EREGL.IS',
    'Türk Hava Yolları': 'THYAO.IS',
    'Aselsan': 'ASELS.IS'
}

# Yan panel - Kullanıcı bilgileri
with st.sidebar:
    st.header("Kişisel Bilgiler")
    
    # Yatırım tutarı
    yatirim_tutari = st.number_input(
        "Toplam Yatırım Tutarı (TL)",
        min_value=1000,
        value=100000
    )
    
    # Risk toleransı
    risk_toleransi = st.slider(
        "Risk Toleransı",
        min_value=1,
        max_value=10,
        value=5,
        help="1: En düşük risk, 10: En yüksek risk"
    )
    
    # Yatırım vadesi
    yatirim_vadesi = st.selectbox(
        "Yatırım Vadesi",
        options=["Kısa Vade (0-2 yıl)", "Orta Vade (2-5 yıl)", "Uzun Vade (5+ yıl)"]
    )
    
    # Yatırım hedefi
    yatirim_hedefi = st.selectbox(
        "Yatırım Hedefi",
        options=["Sermaye Koruma", "Dengeli Büyüme", "Agresif Büyüme"]
    )

# Portföy oluşturma fonksiyonu (unchanged)
def portfoy_olustur(risk_toleransi, yatirim_vadesi, yatirim_hedefi):
    # ... (keep existing implementation)
    pass

# Ana panel - Piyasa Durumu
st.header("Güncel Piyasa Durumu")
col_market1, col_market2 = st.columns(2)

with col_market1:
    st.subheader("Önemli Endeksler")
    for name, ticker in INDICES.items():
        data = get_stock_data(ticker, '5d')
        if data is not None and not data.empty and len(data) >= 2:
            son_fiyat = data['Close'].iloc[-1]
            onceki_fiyat = data['Close'].iloc[-2]
            degisim = ((son_fiyat - onceki_fiyat) / onceki_fiyat) * 100
            col1, col2 = st.columns([2, 1])
            col1.metric(name, f"{son_fiyat:,.2f}", f"{degisim:+.2f}%")
        else:
            st.warning(f"{name} için yeterli veri bulunamadı.")

with col_market2:
    st.subheader("Popüler Türk Hisseleri")
    for name, ticker in TURKISH_STOCKS.items():
        data = get_stock_data(ticker, '5d')
        if data is not None and not data.empty and len(data) >= 2:
            son_fiyat = data['Close'].iloc[-1]
            onceki_fiyat = data['Close'].iloc[-2]
            degisim = ((son_fiyat - onceki_fiyat) / onceki_fiyat) * 100
            col1, col2 = st.columns([2, 1])
            col1.metric(name, f"{son_fiyat:,.2f} TL", f"{degisim:+.2f}%")
        else:
            st.warning(f"{name} için yeterli veri bulunamadı.")

# Rest of the code remains the same, but apply similar data validation
# when accessing price data in other sections...
# (Keep the remaining code but add similar checks for data.empty and len(data))
