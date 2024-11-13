import streamlit as st
from binance.client import Client
import pandas as pd
import ta
import numpy as np
import threading

class CryptoScanner:
    def __init__(self):
        self.client = Client()
        self.setup_ui()

    def setup_ui(self):
        st.title("Crypto Scanner")

        # Interval seçimi
        self.interval = st.selectbox("Interval", ["1m", "5m", "15m", "30m", "1h", "4h", "1d"], index=4)

        # SMA Ayarları
        self.use_sma = st.checkbox("SMA Kullan")
        if self.use_sma:
            self.sma_period = st.number_input("SMA Period", value=50)
            self.sma_position = st.selectbox("SMA Pozisyonu", ["Above", "Below"])

        # RSI Ayarları
        self.use_rsi = st.checkbox("RSI Kullan")
        if self.use_rsi:
            self.rsi_period = st.number_input("RSI Period", value=14)
            self.rsi_condition = st.selectbox("RSI Condition", ["Overbought", "Oversold"])
            self.rsi_threshold = st.number_input("RSI Threshold", value=70)

        # Tarama Butonu
        if st.button("Tara"):
            st.write("Tarama başlatılıyor...")
            self.scan_coins()

    def scan_coins(self):
        futures = self.client.futures_exchange_info()
        symbols = [symbol['symbol'] for symbol in futures['symbols'] if symbol['status'] == 'TRADING']

        results = []
        for symbol in symbols:
            result = self.analyze_coin(symbol)
            if result:
                results.append(result)

        # Sonuçları göster
        if results:
            st.write("\n".join(results))
        else:
            st.write("Hiçbir eşleşme bulunamadı.")

    def analyze_coin(self, symbol):
        interval = self.interval
        klines = self.client.futures_klines(symbol=symbol, interval=interval)
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df['close'] = df['close'].astype(float)

        conditions = []

        # SMA Analizi
        if self.use_sma:
            df['SMA'] = ta.trend.sma_indicator(df['close'], window=self.sma_period)
            if self.sma_position == "Above":
                conditions.append(df['close'].iloc[-1] > df['SMA'].iloc[-1])
            else:
                conditions.append(df['close'].iloc[-1] < df['SMA'].iloc[-1])

        # RSI Analizi
        if self.use_rsi:
            df['RSI'] = ta.momentum.rsi(df['close'], window=self.rsi_period)
            if self.rsi_condition == "Overbought":
                conditions.append(df['RSI'].iloc[-1] > self.rsi_threshold)
            else:
                conditions.append(df['RSI'].iloc[-1] < self.rsi_threshold)

        if all(conditions):
            return f"{symbol}: Fiyat: {df['close'].iloc[-1]}"

# Uygulamayı başlat
scanner = CryptoScanner()
