import ccxt
import pandas as pd
import streamlit as st

# Başlık ve bilgi
st.title("Anlık Kripto Para Verileri")
st.write("Binance borsasından halka açık anlık kripto para verilerini çekebilirsiniz.")

# Kullanıcıdan girişler
symbol = st.text_input("Kripto Çifti (ör: BTC/USDT):", "BTC/USDT")
timeframe = st.selectbox(
    "Zaman Aralığı Seçin",
    ["1m", "5m", "15m", "1h", "4h", "1d"],
    index=5
)
limit = st.slider("Kaç veri noktası çekilsin?", min_value=10, max_value=500, value=100)

# Veriyi çekme işlemi
if st.button("Verileri Çek"):
    st.write(f"Veriler çekiliyor: {symbol} - {timeframe}")

    try:
        # Binance borsasına bağlanma
        exchange = ccxt.binance()
        
        # Veriyi çekme
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        # Veri çerçevesine dönüştürme
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")  # Zaman damgasını düzenleme
        
        # Verileri gösterme
        st.write(f"{symbol} için {timeframe} zaman diliminde son {limit} veri:")
        st.write(df)

        # Grafik oluşturma
        st.line_chart(df[["timestamp", "close"]].set_index("timestamp"), use_container_width=True)

    except Exception as e:
        st.error(f"Bir hata oluştu: {str(e)}")
