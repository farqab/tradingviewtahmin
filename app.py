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

# Veri önbelleği dekoratörü
@st.cache_data(ttl=3600)
def get_stock_data(ticker, period='1y'):
    try:
        if ticker.endswith('.IS'):
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            if hist.empty:
                alternative_ticker = ticker.replace('.IS', '.TI')
                stock = yf.Ticker(alternative_ticker)
                hist = stock.history(period=period)
            
            if not hist.empty:
                return hist, stock.info
        else:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            if not hist.empty:
                return hist, stock.info
        
        return None, None
    except Exception as e:
        st.warning(f"{ticker} için veri çekilirken hata oluştu: {str(e)}")
        return None, None

# Sabit veriler
INDICES = {
    'BIST 100': 'XU100.IS',
    'S&P 500': '^GSPC',
    'NASDAQ': '^IXIC',
    'DAX': '^GDAXI'
}

TURKISH_STOCKS = {
    'Garanti Bankası': 'GARAN.IS',
    'Koç Holding': 'KCHOL.IS',
    'Ereğli Demir Çelik': 'EREGL.IS',
    'Türk Hava Yolları': 'THYAO.IS',
    'Aselsan': 'ASELS.IS',
    # Diğer hisseler...
}

# Teknik analiz göstergeleri
def calculate_technical_indicators(data):
    df = data.copy()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # Bollinger Bands
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['20dSTD'] = df['Close'].rolling(window=20).std()
    df['Upper_Band'] = df['MA20'] + (df['20dSTD'] * 2)
    df['Lower_Band'] = df['MA20'] - (df['20dSTD'] * 2)
    
    return df

def create_portfolio(risk_tolerance, investment_period, investment_goal):
    # Temel dağılım
    if investment_period in ["Günlük Trade", "Haftalık"]:
        stock_ratio = min(0.8, risk_tolerance / 10)
        bond_ratio = 0.05
        gold_ratio = 0.1
        cash_ratio = 1 - (stock_ratio + bond_ratio + gold_ratio)
    else:
        stock_ratio = min(0.6 * (risk_tolerance / 10), 0.8)
        bond_ratio = max(0.2 * ((10 - risk_tolerance) / 10), 0.1)
        gold_ratio = 0.15
        cash_ratio = 1 - (stock_ratio + bond_ratio + gold_ratio)
    
    return {
        "Hisse Senetleri": stock_ratio,
        "Tahvil/Bono": bond_ratio,
        "Altın": gold_ratio,
        "Nakit": cash_ratio
    }

def main():
    st.title("Kişisel Yatırım Portföyü Oluşturucu")
    
    # Sidebar
    with st.sidebar:
        investment_amount = st.number_input(
            "Toplam Yatırım Tutarı (TL)",
            min_value=1000,
            value=100000
        )
        
        risk_tolerance = st.slider(
            "Risk Toleransı",
            min_value=1,
            max_value=10,
            value=5,
            help="1: En düşük risk, 10: En yüksek risk"
        )
        
        investment_period = st.selectbox(
            "Yatırım Vadesi",
            ["Günlük Trade", "Haftalık", "Aylık", "Kısa Vade (0-2 yıl)", 
             "Orta Vade (2-5 yıl)", "Uzun Vade (5+ yıl)"]
        )
        
        investment_goal = st.selectbox(
            "Yatırım Hedefi",
            ["Sermaye Koruma", "Dengeli Büyüme", "Agresif Büyüme"]
        )
    
    # Ana panel
    col1, col2 = st.columns(2)
    
    with col1:
        portfolio = create_portfolio(risk_tolerance, investment_period, investment_goal)
        
        fig = go.Figure(data=[go.Pie(
            labels=list(portfolio.keys()),
            values=list(portfolio.values()),
            hole=.3
        )])
        fig.update_layout(title="Varlık Dağılımı")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Portföy Detayları")
        df_portfolio = pd.DataFrame({
            'Varlık Sınıfı': portfolio.keys(),
            'Oran (%)': [f"{v*100:.1f}%" for v in portfolio.values()],
            'Tutar (TL)': [f"{v*investment_amount:,.0f} TL" for v in portfolio.values()]
        })
        st.dataframe(df_portfolio, hide_index=True)
    
    # Teknik Analiz Bölümü
    st.header("Teknik Analiz")
    selected_stock = st.selectbox(
        "Hisse Seçimi",
        list(TURKISH_STOCKS.keys())
    )
    
    if selected_stock:
        data, info = get_stock_data(TURKISH_STOCKS[selected_stock])
        if data is not None:
            technical_data = calculate_technical_indicators(data)
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close']
            ))
            
            fig.update_layout(title=f"{selected_stock} Fiyat Grafiği")
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
