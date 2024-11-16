import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

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

# Fiyat tahmini için LSTM modeli
def create_lstm_model(data):
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data.reshape(-1, 1))
    
    # Veri hazırlama
    X, y = [], []
    for i in range(60, len(scaled_data)):
        X.append(scaled_data[i-60:i, 0])
        y.append(scaled_data[i, 0])
    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))
    
    # Model oluşturma
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(60, 1)),
        LSTM(50, return_sequences=False),
        Dense(25),
        Dense(1)
    ])
    
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X, y, batch_size=32, epochs=20, verbose=0)
    
    return model, scaler

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
        
        # LSTM ile fiyat tahmini
        if len(coin_data) > 60:  # Minimum veri gereksinimi
            prices = coin_data['Close'].values
            model, scaler = create_lstm_model(prices)
            
            # Gelecek tahmin
            last_60_days = prices[-60:]
            scaled_data = scaler.transform(last_60_days.reshape(-1, 1))
            X_test = np.array([scaled_data])
            X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))
            
            pred = model.predict(X_test)
            pred_price = scaler.inverse_transform(pred)[0][0]
            
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

except Exception as e:
    st.error(f"Veri çekerken bir hata oluştu: {str(e)}")
    st.info("Lütfen internet bağlantınızı kontrol edin ve sayfayı yenileyin.")

# Footer
st.markdown("---")
st.markdown("### 📚 Kullanım Kılavuzu")
st.markdown("""
- Sol menüden zaman dilimi ve filtreleme seçeneklerini ayarlayın
- İstediğiniz kripto parayı seçin
- Fiyat grafiğini inceleyin ve yapay zeka tahminlerini görün
- Piyasa özetini ve popüler coinleri takip edin
""")

# Güvenlik uyarısı
st.warning("⚠️ Bu uygulama sadece bilgilendirme amaçlıdır. Yatırım tavsiyesi değildir.")
