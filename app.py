import streamlit as st
import pandas as pd
import numpy as np
from binance.client import Client
import ta
import asyncio
import aiohttp
import concurrent.futures

# api_key ve api_secret'ı şu şekilde değiştirin:
api_key = st.secrets["binance_api_key"]
api_secret = st.secrets["binance_api_secret"]

client = Client(api_key, api_secret)

# Veri çekme fonksiyonu
async def get_binance_data(session, symbol, interval, limit=100):
    url = f'https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}'
    try:
        async with session.get(url) as response:
            data = await response.json()
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df[['close', 'open', 'high', 'low', 'volume']] = df[['close', 'open', 'high', 'low', 'volume']].astype(float)
            return df
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {e}")
        return None

# İndikatörler
def calculate_indicators(df, params):
    try:
        if 'SMA' in params:
            df['SMA'] = ta.trend.SMAIndicator(close=df['close'], window=params['SMA']).sma_indicator()
        if 'EMA' in params:
            df['EMA'] = ta.trend.EMAIndicator(close=df['close'], window=params['EMA']).ema_indicator()
        if 'RSI' in params:
            df['RSI'] = ta.momentum.RSIIndicator(close=df['close'], window=params['RSI']).rsi()
        if 'MACD' in params:
            macd = ta.trend.MACD(close=df['close'], window_slow=params['MACD_slow'], window_fast=params['MACD_fast'], window_sign=params['MACD_sign'])
            df['MACD'] = macd.macd()
            df['MACD Signal'] = macd.macd_signal()
        if 'Stochastic' in params:
            stochastic = ta.momentum.StochasticOscillator(high=df['high'], low=df['low'], close=df['close'], window=params['Stochastic'])
            df['Stochastic'] = stochastic.stoch()
        if 'ADX' in params:
            df['ADX'] = ta.trend.ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=params['ADX']).adx()
        if 'CCI' in params:
            df['CCI'] = ta.trend.CCIIndicator(high=df['high'], low=df['low'], close=df['close'], window=params['CCI']).cci()
        if 'Williams %R' in params:
            df['Williams %R'] = ta.momentum.WilliamsRIndicator(high=df['high'], low=df['low'], close=df['close'], lbp=params['Williams %R']).williams_r()
        if 'ROC' in params:
            df['ROC'] = ta.momentum.ROCIndicator(close=df['close'], window=params['ROC']).roc()
        if 'Ultimate Oscillator' in params:
            df['Ultimate Oscillator'] = ta.momentum.UltimateOscillator(high=df['high'], low=df['low'], close=df['close'], window1=params['Ultimate Oscillator_short'], window2=params['Ultimate Oscillator_medium'], window3=params['Ultimate Oscillator_long']).ultimate_oscillator()
        if 'Bollinger Bands' in params:
            bb = ta.volatility.BollingerBands(close=df['close'], window=params['BB_Period'], window_dev=params['BB_Multiplier'])
            df['BB_High'] = bb.bollinger_hband()
            df['BB_Low'] = bb.bollinger_lband()
        return df
    except Exception as e:
        st.error(f"Error calculating indicators: {e}")
        return None

# İndikatör sinyal kontrol fonksiyonu
def check_indicator_signal(df, indicator, params):
    try:
        if indicator == 'Bollinger Bands':
            if params['BB_Type'] == 'Alt Band':
                if df['close'].iloc[-1] < df['BB_Low'].iloc[-1] and df['close'].iloc[-2] >= df['BB_Low'].iloc[-2]:
                    return "Al"
                elif df['close'].iloc[-1] > df['BB_High'].iloc[-1] and df['close'].iloc[-2] <= df['BB_High'].iloc[-2]:
                    return "Sat"
            else:
                if df['close'].iloc[-1] > df['BB_High'].iloc[-1] and df['close'].iloc[-2] <= df['BB_High'].iloc[-2]:
                    return "Sat"
                elif df['close'].iloc[-1] < df['BB_Low'].iloc[-1] and df['close'].iloc[-2] >= df['BB_Low'].iloc[-2]:
                    return "Al"
        elif indicator == 'SMA':
            if df['close'].iloc[-1] > df['SMA'].iloc[-1] and df['close'].iloc[-2] <= df['SMA'].iloc[-2]:
                return "Al"
            elif df['close'].iloc[-1] < df['SMA'].iloc[-1] and df['close'].iloc[-2] >= df['SMA'].iloc[-2]:
                return "Sat"
        elif indicator == 'EMA':
            if df['close'].iloc[-1] > df['EMA'].iloc[-1] and df['close'].iloc[-2] <= df['EMA'].iloc[-2]:
                return "Al"
            elif df['close'].iloc[-1] < df['EMA'].iloc[-1] and df['close'].iloc[-2] >= df['EMA'].iloc[-2]:
                return "Sat"
        elif indicator == 'RSI':
            if df['RSI'].iloc[-1] < params['RSI_Lower'] and df['RSI'].iloc[-2] >= params['RSI_Lower']:
                return "Al"
            elif df['RSI'].iloc[-1] > params['RSI_Upper'] and df['RSI'].iloc[-2] <= params['RSI_Upper']:
                return "Sat"
        elif indicator == 'MACD':
            if params['MACD_Type'] == 'Üst Kesişim':
                if df['MACD'].iloc[-1] > df['MACD Signal'].iloc[-1] and df['MACD'].iloc[-2] <= df['MACD Signal'].iloc[-2]:
                    return "Al"
                elif df['MACD'].iloc[-1] < df['MACD Signal'].iloc[-1] and df['MACD'].iloc[-2] >= df['MACD Signal'].iloc[-2]:
                    return "Sat"
            else:
                if df['MACD'].iloc[-1] < df['MACD Signal'].iloc[-1] and df['MACD'].iloc[-2] >= df['MACD Signal'].iloc[-2]:
                    return "Sat"
                elif df['MACD'].iloc[-1] > df['MACD Signal'].iloc[-1] and df['MACD'].iloc[-2] <= df['MACD Signal'].iloc[-2]:
                    return "Al"
        elif indicator == 'Stochastic':
            if params['Stochastic_Type'] == 'Üst Kesişim':
                if df['Stochastic'].iloc[-1] > params['Stochastic_Upper'] and df['Stochastic'].iloc[-2] <= params['Stochastic_Upper']:
                    return "Al"
                elif df['Stochastic'].iloc[-1] < params['Stochastic_Lower'] and df['Stochastic'].iloc[-2] >= params['Stochastic_Lower']:
                    return "Sat"
            else:
                if df['Stochastic'].iloc[-1] < params['Stochastic_Lower'] and df['Stochastic'].iloc[-2] >= params['Stochastic_Lower']:
                    return "Al"
                elif df['Stochastic'].iloc[-1] > params['Stochastic_Upper'] and df['Stochastic'].iloc[-2] <= params['Stochastic_Upper']:
                    return "Sat"
        elif indicator == 'ADX':
            if df['ADX'].iloc[-1] > params['ADX_Threshold'] and df['ADX'].iloc[-2] <= params['ADX_Threshold']:
                return "Al"
            elif df['ADX'].iloc[-1] < params['ADX_Threshold'] and df['ADX'].iloc[-2] >= params['ADX_Threshold']:
                return "Sat"
        elif indicator == 'CCI':
            if df['CCI'].iloc[-1] < params['CCI_Lower'] and df['CCI'].iloc[-2] >= params['CCI_Lower']:
                return "Al"
            elif df['CCI'].iloc[-1] > params['CCI_Upper'] and df['CCI'].iloc[-2] <= params['CCI_Upper']:
                return "Sat"
        elif indicator == 'Williams %R':
            if df['Williams %R'].iloc[-1] < params['Williams %R_Lower'] and df['Williams %R'].iloc[-2] >= params['Williams %R_Lower']:
                return "Al"
            elif df['Williams %R'].iloc[-1] > params['Williams %R_Upper'] and df['Williams %R'].iloc[-2] <= params['Williams %R_Upper']:
                return "Sat"
        elif indicator == 'ROC':
            if df['ROC'].iloc[-1] > 0 and df['ROC'].iloc[-2] <= 0:
                return "Al"
            elif df['ROC'].iloc[-1] < 0 and df['ROC'].iloc[-2] >= 0:
                return "Sat"
        elif indicator == 'Ultimate Oscillator':
            if df['Ultimate Oscillator'].iloc[-1] < params['Ultimate Oscillator_Lower'] and df['Ultimate Oscillator'].iloc[-2] >= params['Ultimate Oscillator_Lower']:
                return "Al"
            elif df['Ultimate Oscillator'].iloc[-1] > params['Ultimate Oscillator_Upper'] and df['Ultimate Oscillator'].iloc[-2] <= params['Ultimate Oscillator_Upper']:
                return "Sat"
    except Exception as e:
        st.error(f"Error checking signal for {indicator}: {e}")
    return None

# Futures USDT sembollerini çekme
def get_futures_usdt_symbols():
    try:
        info = client.futures_exchange_info()
        symbols = [s['symbol'] for s in info['symbols'] if 'USDT' in s['symbol']]
        return symbols
    except Exception as e:
        st.error(f"Error fetching futures symbols: {e}")
        return []

# Streamlit kullanıcı arayüzü
st.title("Binance Futures İndikatör Analiz Aracı")
st.sidebar.header("İndikatör Ayarları")

interval = st.sidebar.selectbox("Zaman Dilimi Seçin:", ["1m", "5m", "15m", "30m", "1h", "4h", "1d"])

indicators = {
    'SMA': st.sidebar.checkbox('SMA'),
    'EMA': st.sidebar.checkbox('EMA'),
    'RSI': st.sidebar.checkbox('RSI'),
    'MACD': st.sidebar.checkbox('MACD'),
    'Stochastic': st.sidebar.checkbox('Stochastic'),
    'ADX': st.sidebar.checkbox('ADX'),
    'CCI': st.sidebar.checkbox('CCI'),
    'Williams %R': st.sidebar.checkbox('Williams %R'),
    'ROC': st.sidebar.checkbox('ROC'),
    'Ultimate Oscillator': st.sidebar.checkbox('Ultimate Oscillator'),
    'Bollinger Bands': st.sidebar.checkbox('Bollinger Bands')
}

params = {}
if indicators['SMA']:
    params['SMA'] = st.sidebar.slider('SMA Periyodu:', min_value=5, max_value=200, value=20)
if indicators['EMA']:
    params['EMA'] = st.sidebar.slider('EMA Periyodu:', min_value=5, max_value=200, value=20)
if indicators['RSI']:
    params['RSI'] = st.sidebar.slider('RSI Periyodu:', min_value=5, max_value=200, value=14)
    params['RSI_Lower'] = st.sidebar.slider('RSI Alt Limit:', min_value=0, max_value=100, value=30)
    params['RSI_Upper'] = st.sidebar.slider('RSI Üst Limit:', min_value=0, max_value=100, value=70)
if indicators['MACD']:
    params['MACD_slow'] = st.sidebar.slider('MACD Yavaş Periyodu:', min_value=5, max_value=200, value=26)
    params['MACD_fast'] = st.sidebar.slider('MACD Hızlı Periyodu:', min_value=5, max_value=200, value=12)
    params['MACD_sign'] = st.sidebar.slider('MACD Sinyal Periyodu:', min_value=5, max_value=200, value=9)
    params['MACD_Type'] = st.sidebar.selectbox('MACD Tipi:', ['Üst Kesişim', 'Alt Kesişim'])
if indicators['Stochastic']:
    params['Stochastic'] = st.sidebar.slider('Stochastic Periyodu:', min_value=5, max_value=200, value=14)
    params['Stochastic_Upper'] = st.sidebar.slider('Stochastic Üst Limit:', min_value=0, max_value=100, value=80)
    params['Stochastic_Lower'] = st.sidebar.slider('Stochastic Alt Limit:', min_value=0, max_value=100, value=20)
    params['Stochastic_Type'] = st.sidebar.selectbox('Stochastic Tipi:', ['Üst Kesişim', 'Alt Kesişim'])
if indicators['ADX']:
    params['ADX'] = st.sidebar.slider('ADX Periyodu:', min_value=5, max_value=200, value=14)
    params['ADX_Threshold'] = st.sidebar.slider('ADX Eşik Değeri:', min_value=0, max_value=100, value=25)
if indicators['CCI']:
    params['CCI'] = st.sidebar.slider('CCI Periyodu:', min_value=5, max_value=200, value=20)
    params['CCI_Lower'] = st.sidebar.slider('CCI Alt Limit:', min_value=-200, max_value=0, value=-100)
    params['CCI_Upper'] = st.sidebar.slider('CCI Üst Limit:', min_value=0, max_value=200, value=100)
if indicators['Williams %R']:
    params['Williams %R'] = st.sidebar.slider('Williams %R Periyodu:', min_value=5, max_value=200, value=14)
    params['Williams %R_Lower'] = st.sidebar.slider('Williams %R Alt Limit:', min_value=-100, max_value=0, value=-80)
    params['Williams %R_Upper'] = st.sidebar.slider('Williams %R Üst Limit:', min_value=-100, max_value=0, value=-20)
if indicators['ROC']:
    params['ROC'] = st.sidebar.slider('ROC Periyodu:', min_value=5, max_value=200, value=12)
if indicators['Ultimate Oscillator']:
    params['Ultimate Oscillator_short'] = st.sidebar.slider('Ultimate Oscillator Kısa Periyodu:', min_value=1, max_value=200, value=7)
    params['Ultimate Oscillator_medium'] = st.sidebar.slider('Ultimate Oscillator Orta Periyodu:', min_value=1, max_value=200, value=14)
    params['Ultimate Oscillator_long'] = st.sidebar.slider('Ultimate Oscillator Uzun Periyodu:', min_value=1, max_value=200, value=28)
    params['Ultimate Oscillator_Lower'] = st.sidebar.slider('Ultimate Oscillator Alt Limit:', min_value=0, max_value=100, value=30)
    params['Ultimate Oscillator_Upper'] = st.sidebar.slider('Ultimate Oscillator Üst Limit:', min_value=0, max_value=100, value=70)
if indicators['Bollinger Bands']:
    params['BB_Period'] = st.sidebar.slider('Bollinger Bandı Periyodu:', min_value=5, max_value=200, value=20)
    params['BB_Multiplier'] = st.sidebar.slider('Bollinger Bandı Çarpanı:', min_value=1.0, max_value=5.0, value=2.0)
    params['BB_Type'] = st.sidebar.selectbox('Bollinger Bandı Tipi:', ['Alt Band', 'Üst Band'])

st.write("Seçili İndikatörler ve Parametreler:", params)

if st.button("Analiz Başlat"):
    symbols = get_futures_usdt_symbols()
    if symbols:
        results = []
        async def analyze_symbols():
            async with aiohttp.ClientSession() as session:
                tasks = []
                for symbol in symbols:
                    task = asyncio.ensure_future(get_binance_data(session, symbol, interval))
                    tasks.append(task)
                responses = await asyncio.gather(*tasks)
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = []
                    for df, symbol in zip(responses, symbols):
                        if df is not None:
                            df = calculate_indicators(df, params)
                            if df is not None:
                                for indicator in params.keys():
                                    signal = check_indicator_signal(df, indicator, params)
                                    if signal:
                                        futures.append(executor.submit(lambda p: p.append((symbol, indicator, signal)), results))
                    concurrent.futures.wait(futures)
        asyncio.run(analyze_symbols())

        if results:
            result_df = pd.DataFrame(results, columns=['Sembol', 'İndikatör', 'Sinyal'])
            st.write(result_df)
        else:
            st.write("Analiz sonucunda sinyal bulunamadı.")
    else:
        st.write("Futures sembolleri çekilemedi.")
