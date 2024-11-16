import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import ta
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Cache fonksiyonu ekleyelim
@st.cache_data(ttl=300)  # 5 dakika cache
def get_crypto_data(symbol, period):
    """Kripto para verilerini çekme fonksiyonu"""
    try:
        ticker = yf.Ticker(f"{symbol}-USD")
        data = ticker.history(period=period)
        return data if not data.empty else None
    except Exception as e:
        st.error(f"Veri çekilirken hata oluştu: {str(e)}")
        return None

# Sayfanın genel ayarlarını yapılandırma
st.set_page_config(
    page_title="Kripto Tarayıcı",
    page_icon="📊",
    layout="wide"
)

# Ana başlık
st.title("📊 Kripto Para Teknik Analiz Platformu")

# Sidebar oluşturma
with st.sidebar:
    st.header("Filtre Ayarları")
    
    # Zaman aralığı seçimi
    period_options = {
        "1 Gün": "1d",
        "1 Hafta": "7d",
        "1 Ay": "1mo",
        "3 Ay": "3mo"
    }
    selected_period = st.selectbox("Zaman Aralığı", list(period_options.keys()))

    # Teknik gösterge filtreleri
    st.subheader("Teknik Göstergeler")

    # RSI ayarları
    use_rsi = st.checkbox("RSI Filtresi", True)
    if use_rsi:
        rsi_lower = st.slider("RSI Alt Limit", 0, 100, 30)
        rsi_upper = st.slider("RSI Üst Limit", 0, 100, 70)

    # EMA ayarları
    use_ema = st.checkbox("EMA Filtresi", True)
    if use_ema:
        ema_period = st.selectbox("EMA Periyodu", [9, 20, 50, 200], index=1)

    # MACD ayarları
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
            yaxis_title="Fiyat (USD)",
            xaxis_title="Tarih",
            height=600,
            template="plotly_dark"
        )
        
        return fig
    except Exception as e:
        st.error(f"Grafik oluşturulurken hata oluştu: {str(e)}")
        return None

# Genişletilmiş kripto listesi
crypto_list = [
    # Major Cryptocurrencies
    "BTC", "ETH", "USDT", "BNB", "SOL", "XRP", "USDC", "ADA", "AVAX", "DOGE",
    # DeFi Tokens
    "UNI", "LINK", "AAVE", "MKR", "CRV", "SNX", "COMP", "YFI", "SUSHI", "BAL",
    # Layer 1 & 2 Solutions
    "MATIC", "DOT", "ATOM", "NEAR", "FTM", "ONE", "ALGO", "EGLD", "HBAR", "ETC",
    # Exchange Tokens
    "CRO", "FTT", "KCS", "HT", "LEO", "OKB", "GT", "BNX", "WOO", "CAKE",
    # Gaming & Metaverse
    "SAND", "MANA", "AXS", "GALA", "ENJ", "ILV", "THETA", "CHZ", "FLOW", "IMX",
    # Storage & Computing
    "FIL", "STX", "AR", "SC", "STORJ", "RLC", "GLM", "NMR", "OCEAN", "LPT",
    # Privacy Coins
    "XMR", "ZEC", "DASH", "SCRT", "ROSE", "KEEP", "NYM", "PRE", "PPC", "FIRO",
    # Infrastructure
    "GRT", "API3", "BAND", "TRB", "REN", "KP3R", "ROOK", "ANKR", "FET", "NEST",
    # Stablecoins & Related
    "DAI", "FRAX", "TUSD", "USDP", "RSR", "FXS", "MIM", "TRIBE", "BAG", "OUSD",
    # Others
    "LTC", "XLM", "VET", "LUNA", "MIOTA", "EOS", "XTZ", "NEO", "WAVES", "ZIL"
]


# Ana bölüm
st.header("Kripto Para Taraması")

if st.button("Taramayı Başlat"):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    filtered_cryptos = []
    
    for i, symbol in enumerate(crypto_list):
        status_text.text(f"Taranan: {symbol}")
        progress_bar.progress((i + 1) / len(crypto_list))
        
        df = get_crypto_data(symbol, period_options[selected_period])
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
                        '24s Değişim (%)': ((last_close - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100).round(2),
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
            df = get_crypto_data(selected_crypto, period_options[selected_period])
            if df is not None:
                df = calculate_indicators(df)
                if df is not None:
                    fig = create_chart(df, selected_crypto)
                    if fig is not None:
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Metrikler
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Fiyat (USD)", f"${df['Close'].iloc[-1]:,.2f}")
                        with col2:
                            st.metric("RSI", f"{df['RSI'].iloc[-1]:.2f}")
                        with col3:
                            st.metric("24s Değişim (%)", f"{((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100):.2f}%")
                        with col4:
                            st.metric("Hacim", f"{df['Volume'].iloc[-1]:,.0f}")
    else:
        st.warning("Filtrelere uygun kripto para bulunamadı.")
