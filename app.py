import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from datetime import datetime
import plotly.graph_objects as go

# Cache fonksiyonu
@st.cache_data(ttl=300)  # 5 dakika önbellek
def get_crypto_data(symbol, period):
    """Kripto para verilerini çekme fonksiyonu."""
    try:
        ticker = yf.Ticker(f"{symbol}-USD")
        data = ticker.history(period=period)
        if not data.empty:
            data['Date'] = data.index
            return data
        else:
            return None
    except Exception as e:
        st.error(f"Veri çekilirken hata oluştu: {str(e)}")
        return None

# Teknik göstergeleri hesaplama
def calculate_indicators(df, ema_period):
    """Teknik göstergeleri hesaplama."""
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

# Grafik oluşturma
def create_chart(df, symbol, ema_period, use_ema):
    """Kripto para grafiği oluşturma."""
    if df is None or df.empty:
        st.warning(f"{symbol} için grafik oluşturulamadı. Veri eksik!")
        return None
    
    try:
        fig = go.Figure()
        
        # Mum grafiği
        fig.add_trace(go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name="Fiyat"
        ))
        
        # EMA
        if use_ema:
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df[f'EMA_{ema_period}'],
                name=f'EMA {ema_period}',
                line=dict(width=1, color='orange')
            ))
        
        fig.update_layout(
            title=f"{symbol} Teknik Analiz Grafiği",
            xaxis_title="Tarih",
            yaxis_title="Fiyat (USD)",
            height=600,
            template="plotly_dark"
        )
        return fig
    except Exception as e:
        st.error(f"Grafik oluşturulurken hata oluştu: {str(e)}")
        return None

# Sayfa yapılandırması
st.set_page_config(
    page_title="Kripto Teknik Analiz",
    page_icon="📊",
    layout="wide"
)

# Başlık
st.title("📊 Kripto Teknik Analiz Platformu")

# Sidebar
with st.sidebar:
    st.header("🔍 Filtre Ayarları")
    
    # Zaman aralığı seçenekleri
    period_options = {
        "1 Gün": "1d", "3 Gün": "3d", "1 Hafta": "7d", "2 Hafta": "14d",
        "1 Ay": "1mo", "3 Ay": "3mo", "6 Ay": "6mo", "1 Yıl": "1y"
    }
    selected_period = st.selectbox("Zaman Aralığı", list(period_options.keys()))
    
    # RSI filtresi
    use_rsi = st.checkbox("RSI Filtresi", True)
    if use_rsi:
        rsi_lower = st.slider("RSI Alt Limit", 0, 100, 30)
        rsi_upper = st.slider("RSI Üst Limit", 0, 100, 70)
    
    # EMA filtresi
    use_ema = st.checkbox("EMA Filtresi", True)
    ema_period = st.selectbox("EMA Periyodu", [9, 20, 50, 200]) if use_ema else 20
    
    # MACD filtresi
    use_macd = st.checkbox("MACD Filtresi", True)

# Ana bölüm
st.header("📈 Kripto Para Taraması")

# Kripto listesi
crypto_list = ["BTC", "ETH", "BNB", "XRP", "DOGE", "ADA", "SOL", "MATIC", "DOT", "LTC"]

if st.button("Taramayı Başlat"):
    st.write("🔄 Tarama başlatıldı...")
    progress_bar = st.progress(0)
    filtered_cryptos = []
    
    for i, symbol in enumerate(crypto_list):
        df = get_crypto_data(symbol, period_options[selected_period])
        if df is not None:
            df = calculate_indicators(df, ema_period)
            if df is not None:
                last_close = df['Close'].iloc[-1]
                last_rsi = df['RSI'].iloc[-1]
                meets_criteria = True
                
                if use_rsi:
                    meets_criteria &= rsi_lower <= last_rsi <= rsi_upper
                
                if use_ema and meets_criteria:
                    meets_criteria &= last_close > df[f'EMA_{ema_period}'].iloc[-1]
                
                if use_macd and meets_criteria:
                    macd_last = df['MACD'].iloc[-1]
                    macd_signal_last = df['MACD_Signal'].iloc[-1]
                    meets_criteria &= macd_last > macd_signal_last
                
                if meets_criteria:
                    filtered_cryptos.append({
                        "Sembol": symbol,
                        "Fiyat (USD)": round(last_close, 2),
                        "RSI": round(last_rsi, 2),
                        "24 Saat Değişim (%)": round(((last_close - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100, 2),
                        "Hacim": round(df['Volume'].iloc[-1])
                    })
        progress_bar.progress((i + 1) / len(crypto_list))
    
    progress_bar.empty()
    if filtered_cryptos:
        st.subheader("📋 Filtrelenmiş Kripto Paralar")
        result_df = pd.DataFrame(filtered_cryptos)
        st.dataframe(result_df)
        
        # Detaylı analiz
        selected_crypto = st.selectbox("Detaylı Analiz için Kripto Seçin", result_df['Sembol'])
        if selected_crypto:
            df = get_crypto_data(selected_crypto, period_options[selected_period])
            if df is not None:
                df = calculate_indicators(df, ema_period)
                fig = create_chart(df, selected_crypto, ema_period, use_ema)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Filtrelere uygun kripto para bulunamadı.")
