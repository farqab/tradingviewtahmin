import streamlit as st
import pandas as pd
import yfinance as yf
import ta
import plotly.graph_objects as go

# Streamlit sayfa ayarları
st.set_page_config(
    page_title="Kripto Para Teknik Analiz",
    page_icon="📊",
    layout="wide"
)

# Cache fonksiyonu ile veri çekme
@st.cache_data(ttl=300)
def get_crypto_data(symbol, period):
    """Kripto para verilerini yFinance üzerinden çeker."""
    try:
        ticker = yf.Ticker(f"{symbol}-USD")
        data = ticker.history(period=period)
        return data if not data.empty else None
    except Exception as e:
        st.error(f"Veri çekilirken hata oluştu: {e}")
        return None

# Teknik göstergeleri hesaplama
def calculate_indicators(df, ema_period):
    """RSI, EMA ve MACD hesaplayan fonksiyon."""
    if df is None or df.empty:
        return None
    try:
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        df[f'EMA_{ema_period}'] = ta.trend.EMAIndicator(df['Close'], window=ema_period).ema_indicator()
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        return df
    except Exception as e:
        st.error(f"Göstergeler hesaplanırken hata oluştu: {e}")
        return None

# Grafik oluşturma
def create_chart(df, symbol, ema_period, use_ema):
    """Mum grafiği ve EMA göstergesini içeren bir grafik oluşturur."""
    if df is None or df.empty:
        return None
    try:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name="Fiyat"
        ))
        if use_ema:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df[f'EMA_{ema_period}'],
                mode="lines",
                name=f"EMA {ema_period}",
                line=dict(color="orange", width=1)
            ))
        fig.update_layout(
            title=f"{symbol} Teknik Analiz Grafiği",
            xaxis_title="Tarih",
            yaxis_title="Fiyat (USD)",
            template="plotly_dark",
            height=600
        )
        return fig
    except Exception as e:
        st.error(f"Grafik oluşturulurken hata oluştu: {e}")
        return None

# Sidebar ve giriş seçenekleri
with st.sidebar:
    st.header("Filtre Ayarları")
    
    period_options = {
        "1 Dakika": "1m",
        "5 Dakika": "5m",
        "15 Dakika": "15m",
        "30 Dakika": "30m",
        "1 Saat": "1h",
        "4 Saat": "4h",
        "1 Gün": "1d",
        "1 Hafta": "7d",
        "1 Ay": "1mo"
    }
    selected_period = st.selectbox("Zaman Aralığı", list(period_options.keys()))

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

# Ana başlık
st.title("📊 Kripto Para Teknik Analiz Platformu")

# Kripto para listesi
crypto_list = ["BTC", "ETH", "BNB", "ADA", "SOL", "XRP", "DOGE", "MATIC", "DOT", "AVAX"]

# Taramayı başlat
if st.button("Taramayı Başlat"):
    progress_bar = st.progress(0)
    filtered_cryptos = []

    for i, symbol in enumerate(crypto_list):
        progress_bar.progress((i + 1) / len(crypto_list))
        df = get_crypto_data(symbol, period_options[selected_period])
        if df is not None:
            df = calculate_indicators(df, ema_period)
            if df is not None:
                last_close = df['Close'].iloc[-1]
                last_rsi = df['RSI'].iloc[-1] if 'RSI' in df else None
                
                meets_criteria = True
                if use_rsi:
                    meets_criteria &= rsi_lower <= last_rsi <= rsi_upper
                if use_ema and meets_criteria:
                    meets_criteria &= last_close > df[f'EMA_{ema_period}'].iloc[-1]
                if use_macd and meets_criteria:
                    macd, signal = df['MACD'].iloc[-1], df['MACD_Signal'].iloc[-1]
                    meets_criteria &= macd > signal
                
                if meets_criteria:
                    filtered_cryptos.append({
                        "Sembol": symbol,
                        "Fiyat": last_close,
                        "RSI": last_rsi,
                        "Hacim": df['Volume'].iloc[-1]
                    })

    progress_bar.empty()
    if filtered_cryptos:
        st.subheader("Filtrelenmiş Kripto Paralar")
        result_df = pd.DataFrame(filtered_cryptos)
        st.dataframe(result_df)
        selected_crypto = st.selectbox("Detaylı Analiz için Kripto Seçin", result_df['Sembol'])
        if selected_crypto:
            df = get_crypto_data(selected_crypto, period_options[selected_period])
            df = calculate_indicators(df, ema_period)
            if df is not None:
                chart = create_chart(df, selected_crypto, ema_period, use_ema)
                st.plotly_chart(chart, use_container_width=True)
    else:
        st.warning("Filtrelere uygun kripto para bulunamadı.")
