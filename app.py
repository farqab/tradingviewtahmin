import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import ta
from datetime import datetime, timedelta
import plotly.graph_objects as go

@st.cache_data(ttl=300)
def get_crypto_data(symbol, period):
    """Kripto para verilerini çekme fonksiyonu"""
    try:
        ticker = yf.Ticker(f"{symbol}-USD")
        data = ticker.history(period=period)
        if data.empty:
            return None
        # Son candleın tamamlanmamış olma ihtimaline karşı kontrol
        if (datetime.now() - data.index[-1]).seconds < 3600:  # Son mum 1 saatten yeniyse
            data = data[:-1]  # Son mumu çıkar
        return data
    except Exception as e:
        st.error(f"Veri çekilirken hata oluştu ({symbol}): {str(e)}")
        return None

def calculate_indicators(df, ema_period):
    """Teknik göstergeleri hesaplama"""
    if df is None or df.empty or len(df) < 50:  # Minimum veri noktası kontrolü
        return None
    
    try:
        # RSI
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        
        # EMA
        df[f'EMA_{ema_period}'] = ta.trend.EMAIndicator(df['Close'], window=ema_period).ema_indicator()
        
        # MACD
        macd = ta.trend.MACD(df['Close'], 
                            window_slow=26,
                            window_fast=12, 
                            window_sign=9)
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Hist'] = macd.macd_diff()  # MACD Histogramı
        
        # Trend belirleyiciler
        df['EMA_Trend'] = df['Close'] > df[f'EMA_{ema_period}']
        df['MACD_Trend'] = df['MACD'] > df['MACD_Signal']
        
        # Son n periyottaki RSI değişimi
        n = 3  # Son 3 periyot
        if len(df) >= n:
            df['RSI_Change'] = df['RSI'].diff(n)
        
        return df
    except Exception as e:
        st.error(f"Göstergeler hesaplanırken hata oluştu: {str(e)}")
        return None

def check_filtering_criteria(df, use_rsi, rsi_lower, rsi_upper, use_ema, use_macd):
    """Geliştirilmiş filtreleme kriterleri kontrolü"""
    if df is None or df.empty:
        return False
    
    try:
        last_idx = -1
        meets_criteria = True
        
        if use_rsi:
            current_rsi = df['RSI'].iloc[last_idx]
            rsi_change = df['RSI_Change'].iloc[last_idx]
            
            # RSI koşulları
            if rsi_lower <= current_rsi <= rsi_upper:
                # Aşırı alım/satım bölgelerinde trend teyidi
                if current_rsi < 30 and rsi_change > 0:  # Aşırı satım + yukarı dönüş
                    meets_criteria &= True
                elif current_rsi > 70 and rsi_change < 0:  # Aşırı alım + aşağı dönüş
                    meets_criteria &= False
                else:
                    meets_criteria &= True
            else:
                meets_criteria = False
        
        if use_ema and meets_criteria:
            # Son 3 mumdaki EMA trendi kontrol
            recent_ema_trend = df['EMA_Trend'].iloc[-3:].all()
            meets_criteria &= recent_ema_trend
        
        if use_macd and meets_criteria:
            # MACD sinyali ve trend kontrolü
            recent_macd_cross = (df['MACD_Hist'].iloc[-2] < 0 and df['MACD_Hist'].iloc[-1] > 0)
            recent_macd_trend = df['MACD_Trend'].iloc[-3:].all()
            meets_criteria &= (recent_macd_cross or recent_macd_trend)
        
        return meets_criteria
    
    except Exception as e:
        st.error(f"Filtreleme kriterleri kontrol edilirken hata oluştu: {str(e)}")
        return False

def create_chart(df, symbol, ema_period):
    """Geliştirilmiş grafik oluşturma"""
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
        if 'EMA_' + str(ema_period) in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df[f'EMA_{ema_period}'],
                name=f'EMA {ema_period}',
                line=dict(color='orange', width=1)
            ))
        
        # MACD sinyalleri
        if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['MACD'],
                name='MACD',
                line=dict(color='blue', width=1),
                yaxis="y2"
            ))
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['MACD_Signal'],
                name='Signal',
                line=dict(color='red', width=1),
                yaxis="y2"
            ))
        
        fig.update_layout(
            title=f"{symbol} Teknik Analiz Grafiği",
            yaxis_title="Fiyat (USD)",
            yaxis2=dict(
                title="MACD",
                overlaying="y",
                side="right"
            ),
            xaxis_title="Tarih",
            height=800,
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

# Filtreleme kısmında yapılacak değişiklik
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
            if df is not None and len(df) > 0:
                meets_criteria = check_filtering_criteria(
                    df, 
                    use_rsi, 
                    rsi_lower, 
                    rsi_upper, 
                    use_ema, 
                    use_macd
                )
                
                if meets_criteria:
                    last_close = df['Close'].iloc[-1]
                    last_rsi = df['RSI'].iloc[-1]
                    
                    filtered_cryptos.append({
                        'Symbol': symbol,
                        'Price': last_close,
                        'RSI': last_rsi,
                        'RSI Trend': "Yükseliş" if df['RSI_Change'].iloc[-1] > 0 else "Düşüş",
                        '24s Değişim (%)': ((last_close - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100).round(2),
                        'Hacim': df['Volume'].iloc[-1],
                        'EMA Trend': "Üzerinde" if df['EMA_Trend'].iloc[-1] else "Altında",
                        'MACD Sinyal': "Al" if df['MACD_Trend'].iloc[-1] else "Sat"
                    })
    
    status_text.text("Tarama Tamamlandı!")
