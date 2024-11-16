import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression

# Sayfa düzeni
st.set_page_config(page_title="Kripto Analiz Platformu", layout="wide")

# Ana başlık
st.title("🚀 Kripto Para Analiz Platformu")

# Yan panel ayarları
st.sidebar.header("📊 Analiz Parametreleri")

# Zaman dilimi seçimi
time_options = {
    "1 Gün": "1d",
    "1 Hafta": "7d",
    "1 Ay": "1mo",
    "3 Ay": "3mo",
    "1 Yıl": "1y"
}
selected_time = st.sidebar.selectbox("Zaman Dilimi", list(time_options.keys()))

# API'den kripto verilerini çekme fonksiyonu
@st.cache_data(ttl=300)  # 5 dakika cache
def fetch_crypto_data():
    # Yatex.ai API endpoint (ücretsiz)
    api_url = "https://api.yatex.ai/v1/market/tickers"
    response = requests.get(api_url)
    data = response.json()
    
    # DataFrame oluşturma
    df = pd.DataFrame(data)
    return df

# Basit fiyat tahmini için fonksiyon
def predict_price(prices, days=1):
    scaler = MinMaxScaler()
    scaled_prices = scaler.fit_transform(prices.reshape(-1, 1))
    
    # Veri hazırlama
    X = np.array(range(len(prices))).reshape(-1, 1)
    y = scaled_prices
    
    # Model eğitimi
    model = LinearRegression()
    model.fit(X, y)
    
    # Tahmin
    future_X = np.array(range(len(prices), len(prices) + days)).reshape(-1, 1)
    future_scaled = model.predict(future_X)
    future_prices = scaler.inverse_transform(future_scaled)
    
    return future_prices[0][0]

# Ana veri çekme ve işleme
try:
    df = fetch_crypto_data()
    
    # Filtreleme seçenekleri
    min_price = st.sidebar.number_input("Minimum Fiyat ($)", value=0.0)
    max_price = st.sidebar.number_input("Maksimum Fiyat ($)", value=float(df['price'].max()))
    min_volume = st.sidebar.number_input("Minimum Hacim ($)", value=0.0)
    
    # Veriyi filtreleme
    filtered_df = df[
        (df['price'] >= min_price) &
        (df['price'] <= max_price) &
        (df['volume_24h'] >= min_volume)
    ]
    
    # Ana panel düzeni
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Fiyat Grafikleri")
        selected_coin = st.selectbox("Kripto Para Seçin", filtered_df['symbol'].unique())
        
        # Seçilen coin için detaylı veri çekme
        coin_data = yf.download(f"{selected_coin}-USD", 
                              period=time_options[selected_time],
                              interval="1h")
        
        # Grafik oluşturma
        fig = go.Figure(data=[go.Candlestick(x=coin_data.index,
                                            open=coin_data['Open'],
                                            high=coin_data['High'],
                                            low=coin_data['Low'],
                                            close=coin_data['Close'])])
        fig.update_layout(title=f"{selected_coin} Fiyat Grafiği",
                         xaxis_title="Tarih",
                         yaxis_title="Fiyat ($)")
        st.plotly_chart(fig, use_container_width=True)
        
        # Fiyat tahmini
        if len(coin_data) > 30:  # Minimum veri gereksinimi
            prices = coin_data['Close'].values
            pred_price = predict_price(prices)
            
            st.subheader("🔮 Fiyat Tahmini")
            st.write(f"24 Saat Sonrası İçin Tahmini Fiyat: ${pred_price:.2f}")
            
            # Trend analizi
            current_price = prices[-1]
            price_change = ((pred_price - current_price) / current_price) * 100
            
            if price_change > 5:
                st.success("📈 Yükseliş Trendi: Güçlü alım fırsatı olabilir")
            elif price_change < -5:
                st.error("📉 Düşüş Trendi: Dikkatli olunmalı")
            else:
                st.info("↔️ Yatay Trend: Stabil seyir bekleniyor")
    
    with col2:
        st.subheader("📊 Piyasa Özeti")
        
        # Temel metrikleri gösterme
        selected_coin_data = filtered_df[filtered_df['symbol'] == selected_coin].iloc[0]
        
        metrics = {
            "Güncel Fiyat": f"${selected_coin_data['price']:.2f}",
            "24s Hacim": f"${selected_coin_data['volume_24h']:,.0f}",
            "24s Değişim": f"{selected_coin_data['price_change_24h']:.2f}%",
            "Piyasa Değeri": f"${selected_coin_data['market_cap']:,.0f}"
        }
        
        for metric, value in metrics.items():
            st.metric(metric, value)
        
        # En çok işlem gören coinler
        st.subheader("🏆 En Çok İşlem Görenler")
        top_volume = filtered_df.nlargest(5, 'volume_24h')[['symbol', 'price', 'volume_24h']]
        st.dataframe(top_volume)
        
        # RSI Hesaplama
        st.subheader("📊 Teknik Göstergeler")
        if len(coin_data) > 14:
            delta = coin_data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            st.metric("RSI (14)", f"{current_rsi:.2f}")
            
            if current_rsi > 70:
                st.warning("⚠️ Aşırı Alım Bölgesi")
            elif current_rsi < 30:
                st.warning("⚠️ Aşırı Satım Bölgesi")
            else:
                st.success("✅ Normal Bölge")

except Exception as e:
    st.error(f"Veri çekerken bir hata oluştu: {str(e)}")
    st.info("Lütfen internet bağlantınızı kontrol edin ve sayfayı yenileyin.")

# Footer
st.markdown("---")
st.markdown("### 📚 Kullanım Kılavuzu")
st.markdown("""
- Sol menüden zaman dilimi ve filtreleme seçeneklerini ayarlayın
- İstediğiniz kripto parayı seçin
- Fiyat grafiğini inceleyin ve tahminleri görün
- Piyasa özetini ve teknik göstergeleri takip edin
""")

# Güvenlik uyarısı
st.warning("⚠️ Bu uygulama sadece bilgilendirme amaçlıdir. Yatırım tavsiyesi değildir.")
