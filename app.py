import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import ta
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Cache fonksiyonu
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

# Sayfa yapılandırması
st.set_page_config(
    page_title="Kripto Tarayıcı",
    page_icon="📊",
    layout="wide"
)

# Ana başlık
st.title("📊 Kripto Para Teknik Analiz Platformu")

# Zaman aralıkları
period_options = {
    # Dakikalık
    "1 Dakika": "1m",
    "5 Dakika": "5m",
    "15 Dakika": "15m",
    "30 Dakika": "30m",
    # Saatlik
    "1 Saat": "1h",
    "2 Saat": "2h",
    "4 Saat": "4h",
    "6 Saat": "6h",
    "12 Saat": "12h",
    # Günlük ve üzeri
    "1 Gün": "1d",
    "3 Gün": "3d",
    "1 Hafta": "7d",
    "2 Hafta": "14d",
    "1 Ay": "1mo",
    "3 Ay": "3mo",
    "6 Ay": "6mo",
    "1 Yıl": "1y"
}

# Sidebar oluşturma
with st.sidebar:
    st.header("Filtre Ayarları")
    
    # Zaman aralığı seçimi
    selected_period = st.selectbox("Zaman Aralığı", list(period_options.keys()))
    
    # İşlem hacmi filtresi
    use_volume = st.checkbox("Hacim Filtresi", False)
    if use_volume:
        min_volume = st.number_input("Minimum Hacim (USD)", value=1000000, step=1000000)
    
    # Fiyat filtresi
    use_price = st.checkbox("Fiyat Filtresi", False)
    if use_price:
        min_price = st.number_input("Minimum Fiyat (USD)", value=0.1, step=0.1)
        max_price = st.number_input("Maximum Fiyat (USD)", value=1000000.0, step=100.0)
    
    # Volatilite filtresi
    use_volatility = st.checkbox("Volatilite Filtresi", False)
    if use_volatility:
        volatility_period = st.slider("Volatilite Periyodu (gün)", 1, 30, 14)
        min_volatility = st.slider("Minimum Volatilite (%)", 0, 100, 20)
    
    st.subheader("Teknik Göstergeler")
    
    # RSI ayarları
    use_rsi = st.checkbox("RSI Filtresi", True)
    if use_rsi:
        rsi_period = st.slider("RSI Periyodu", 1, 30, 14)
        rsi_lower = st.slider("RSI Alt Limit", 0, 100, 30)
        rsi_upper = st.slider("RSI Üst Limit", 0, 100, 70)
    
    # EMA ayarları
    use_ema = st.checkbox("EMA Filtresi", True)
    if use_ema:
        ema_period = st.selectbox("EMA Periyodu", [9, 20, 50, 200], index=1)
    else:
        ema_period = 20  # Varsayılan değer
    
    # Bollinger Bands filtresi
    use_bbands = st.checkbox("Bollinger Bands Filtresi", False)
    if use_bbands:
        bb_length = st.slider("BB Periyodu", 5, 50, 20)
        bb_std = st.slider("BB Standart Sapma", 1, 5, 2)
    
    # MACD ayarları
    use_macd = st.checkbox("MACD Filtresi", True)
    if use_macd:
        macd_fast = st.slider("MACD Hızlı Periyod", 5, 30, 12)
        macd_slow = st.slider("MACD Yavaş Periyod", 10, 50, 26)
        macd_signal = st.slider("MACD Sinyal Periyodu", 1, 20, 9)

def calculate_indicators(df, ema_period):
    """Teknik göstergeleri hesaplama"""
    if df is None or df.empty:
        return None
    
    try:
        # RSI
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=rsi_period).rsi()
        
        # EMA
        df[f'EMA_{ema_period}'] = ta.trend.EMAIndicator(df['Close'], window=ema_period).ema_indicator()
        
        # MACD
        if use_macd:
            macd = ta.trend.MACD(df['Close'], 
                                window_fast=macd_fast,
                                window_slow=macd_slow,
                                window_sign=macd_signal)
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
        
        # Bollinger Bands
        if use_bbands:
            bollinger = ta.volatility.BollingerBands(df['Close'], window=bb_length, window_dev=bb_std)
            df['BB_Upper'] = bollinger.bollinger_hband()
            df['BB_Lower'] = bollinger.bollinger_lband()
            df['BB_Middle'] = bollinger.bollinger_mavg()
        
        # Volatilite
        if use_volatility:
            df['Volatility'] = df['Close'].pct_change().rolling(window=volatility_period).std() * 100
        
        return df
    except Exception as e:
        st.error(f"Göstergeler hesaplanırken hata oluştu: {str(e)}")
        return None

def create_chart(df, symbol, ema_period):
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
                line=dict(width=1, color='orange')
            ))
        
        # Bollinger Bands
        if use_bbands:
            fig.add_trace(go.Scatter(
                x=df.index, y=df['BB_Upper'],
                name='BB Upper',
                line=dict(width=1, color='gray', dash='dash')
            ))
            fig.add_trace(go.Scatter(
                x=df.index, y=df['BB_Lower'],
                name='BB Lower',
                line=dict(width=1, color='gray', dash='dash'),
                fill='tonexty'
            ))
        
        # MACD Alt Grafik
        if use_macd:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['MACD'],
                name='MACD',
                yaxis="y2",
                line=dict(width=1, color='blue')
            ))
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['MACD_Signal'],
                name='Signal',
                yaxis="y2",
                line=dict(width=1, color='red')
            ))
        
        # Grafik düzeni
        fig.update_layout(
            title=f"{symbol} Teknik Analiz Grafiği",
            yaxis_title="Fiyat (USD)",
            xaxis_title="Tarih",
            height=800,  # Yükseklik artırıldı
            template="plotly_dark",
            yaxis2=dict(
                title="MACD",
                overlaying="y",
                side="right",
                showgrid=False
            ),
            showlegend=True
        )
        
        return fig
    except Exception as e:
        st.error(f"Grafik oluşturulurken hata oluştu: {str(e)}")
        return None

# Kripto listesi
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
            df = calculate_indicators(df, ema_period)
            if df is not None:
                last_close = df['Close'].iloc[-1]
                last_rsi = df['RSI'].iloc[-1]
                
                # Filtreleme mantığı
                meets_criteria = True
                
                # Temel filtreler
                if use_rsi:
                    meets_criteria &= rsi_lower <= last_rsi <= rsi_upper
                
                if use_ema:
                    meets_criteria &= last_close > df[f'EMA_{ema_period}'].iloc[-1]
                
                if use_macd:
                    last_macd = df['MACD'].iloc[-1]
                    last_signal = df['MACD_Signal'].iloc[-1]
                    meets_criteria &= last_macd > last_signal
                
                # Ek filtreler
                if use_volume:
                    meets_criteria &= df['Volume'].iloc[-1] >= min_volume
                
                if use_price:
                    meets_criteria &= min_price <= last_close <= max_price
                
                if use_volatility:
                    last_volatility = df['Volatility'].iloc[-1]
                    meets_criteria &= last_volatility >= min_volatility
                
                if use_bbands:
                    last_bb_lower = df['BB_Lower'].iloc[-1]
                    last_bb_upper = df['BB_Upper'].iloc[-1]
                    meets_criteria &= (last_close <= last_bb_lower) or (last_close >= last_bb_upper)
                
                if meets_criteria:
                    crypto_data = {
                        'Symbol': symbol,
                        'Price': last_close,
                        'RSI': last_rsi,
                        '24s Değişim (%)': ((last_close - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100).round(2),
                        'Hacim': df['Volume'].iloc[-1]
                    }
                    
                    # Ek metrikler
                    if use_volatility:
                        crypto_data['Volatilite (%)'] = df['Volatility'].iloc[-1]
                    if use_macd:
                        crypto_data['MACD'] = last_macd
                        crypto_data['MACD Signal'] = last_signal
                    if use_bbands:
                        crypto_data['BB Üst'] = last_bb_upper
                        crypto_data['BB Alt'] = last_bb_lower
                    
                    filtered_cryptos.append(crypto_data)
    
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
                df = calculate_indicators(df, ema_period)  # ema_period parametresi eklendi
                if df is not None:
                    fig = create_chart(df, selected_crypto, ema_period)  # ema_period parametresi eklendi
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
