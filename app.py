import streamlit as st
import pandas as pd
import numpy as np
from binance.client import Client
import ta
import asyncio
import aiohttp
import concurrent.futures
import streamlit as st
from textblob import TextBlob
from newsapi import NewsApiClient
import tweepy


# Binance API anahtarlarınızı girin
api_key = '2cQLCcQB3XCXNasp5VCt3n5qe5GeSw7F3S2aUhJJPzjfUiQLyX9xtpwCt10O57AP'
api_secret = 'lMkmtovUAwTJpTon919pAtxubvffWJE1ZKxNpiWRKY1NL3zo1J8k1jn6KLYqzRla'

# Binance Client Global için TLD ayarı
try:
    client = Client(API_KEY, API_SECRET, tld="com")
except Exception as e:
    st.error(f"Binance Client oluşturulurken hata: {e}")
    st.stop()


# Fetch data function
async def get_binance_data(session, symbol, interval, limit=100):
    url = f'https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}'
        try:
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"  # Global Binance URL
        response = requests.get(url, timeout=10)  # 10 saniyelik timeout
        response.raise_for_status()  # HTTP hatalarını kontrol et
        data = response.json()
        symbols = [s['symbol'] for s in data['symbols'] if 'USDT' in s['symbol']]
        return symbols
    except requests.exceptions.RequestException as e:
        st.error(f"Futures sembolleri alınırken hata: {e}")
        return []
def calculate_pivot_points(df, method='Classic'):
    high = df['high']
    low = df['low']
    close = df['close']

    if method == 'Classic':
        pp = (high + low + close) / 3
        r1 = 2 * pp - low
        s1 = 2 * pp - high
        r2 = pp + (high - low)
        s2 = pp - (high - low)
        r3 = high + 2 * (pp - low)
        s3 = low - 2 * (high - pp)
    elif method == 'Fibonacci':
        pp = (high + low + close) / 3
        r1 = pp + (high - low) * 0.382
        s1 = pp - (high - low) * 0.382
        r2 = pp + (high - low) * 0.618
        s2 = pp - (high - low) * 0.618
        r3 = pp + (high - low) * 1.000
        s3 = pp - (high - low) * 1.000
    elif method == 'Woodie':
        pp = (high + low + 2 * close) / 4
        r1 = 2 * pp - low
        s1 = 2 * pp - high
        r2 = pp + (high - low)
        s2 = pp - (high - low)
    elif method == 'Camarilla':
        pp = (high + low + close) / 3
        r1 = close + (high - low) * 1.1 / 12
        s1 = close - (high - low) * 1.1 / 12
        r2 = close + (high - low) * 1.1 / 6
        s2 = close - (high - low) * 1.1 / 6
        r3 = close + (high - low) * 1.1 / 4
        s3 = close - (high - low) * 1.1 / 4
        r4 = close + (high - low) * 1.1 / 2
        s4 = close - (high - low) * 1.1 / 2
    elif method == 'DM':
        pp = (high + low + close) / 3
        r1 = high + (close - low) * 2 / 3
        s1 = low - (high - close) * 2 / 3
        r2 = high + (close - low) * 1 / 3
        s2 = low - (high - close) * 1 / 3
        r3 = pp + (high - low)
        s3 = pp - (high - low)

    df['Pivot'] = pp
    df['R1'] = r1
    df['S1'] = s1
    df['R2'] = r2
    df['S2'] = s2
    df['R3'] = r3
    df['S3'] = s3
    if method == 'Camarilla':
        df['R4'] = r4
        df['S4'] = s4

    return df
def calculate_sr_channels(df, pivot_period=10, channel_width_percent=5, min_strength=1, max_sr=6, loopback=290):
    def pivot_high_low(data, left, right):
        pivot_high = data['high'].rolling(window=left+right+1, center=True).apply(lambda x: x[left] == max(x), raw=True)
        pivot_low = data['low'].rolling(window=left+right+1, center=True).apply(lambda x: x[left] == min(x), raw=True)
        return pivot_high, pivot_low

    def get_sr_vals(pivot_vals, pivot_locs, index, cwidth):
        lo = pivot_vals[index]
        hi = lo
        numpp = 0
        for y in range(len(pivot_vals)):
            cpp = pivot_vals[y]
            wdth = hi - cpp if cpp <= hi else cpp - lo
            if wdth <= cwidth:
                if cpp <= hi:
                    lo = min(lo, cpp)
                else:
                    hi = max(hi, cpp)
                numpp += 20
        return hi, lo, numpp

    # Calculate pivot points
    df['pivot_high'], df['pivot_low'] = pivot_high_low(df, pivot_period, pivot_period)

    # Calculate maximum channel width
    highest = df['high'].rolling(300).max()
    lowest = df['low'].rolling(300).min()
    cwidth = (highest - lowest) * channel_width_percent / 100

    # Get pivot levels
    pivot_vals = []
    pivot_locs = []
    for i in range(len(df)):
        if df['pivot_high'].iloc[i] or df['pivot_low'].iloc[i]:
            pivot_vals.append(df['high'].iloc[i] if df['pivot_high'].iloc[i] else df['low'].iloc[i])
            pivot_locs.append(i)

    # Calculate SR channels
    sr_channels = []
    for i in range(len(pivot_vals)):
        hi, lo, strength = get_sr_vals(pivot_vals, pivot_locs, i, cwidth.iloc[i])
        sr_channels.append((strength, hi, lo))

    # Sort channels by strength
    sr_channels.sort(key=lambda x: x[0], reverse=True)

    # Keep only the strongest channels
    sr_channels = sr_channels[:max_sr]

    # Add channels to dataframe
    for i, (strength, hi, lo) in enumerate(sr_channels):
        df[f'SR_High_{i}'] = hi
        df[f'SR_Low_{i}'] = lo

    return df
# NewsAPI ve Twitter API anahtarlarınızı buraya ekleyin
newsapi = NewsApiClient(api_key='4a3314f246fb4adca9de6ebff258d36d')
twitter_auth = tweepy.OAuthHandler("5mgwbSkAZY8PMsv537WyjmwT7", "YrIxXPaIp48yJHWYkGBJOOFtiaRB8adTDFDwprQLiW1klpL4zW")
twitter_auth.set_access_token("1012298443241517056-Pp5SxaXl1151EXOxDvtwxZQQAK1184", "8ICGuoKmHsERJ0DT0b4aqBwtKwLdJiH0GDiSH8xI9f7lD")
twitter_api = tweepy.API(twitter_auth)

def get_news_sentiment(symbol):
    try:
        news = newsapi.get_everything(q=symbol, language='en', sort_by='relevancy', page_size=10)
        sentiment_scores = []
        for article in news['articles']:
            analysis = TextBlob(article['title'] + ' ' + article['description'])
            sentiment_scores.append(analysis.sentiment.polarity)
        return sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
    except Exception as e:
        st.error(f"Error fetching news for {symbol}: {e}")
        return 0

# Twitter API v2 için client oluşturma
twitter_client = tweepy.Client(bearer_token="AAAAAAAAAAAAAAAAAAAAAAUWuwEAAAAAa6dU%2BoXW1W1%2F%2Bx3tn2EThUf%2Bhy4%3DGbbQBehiI66hMdtKiDAhkjIuzaHE8WauElXqJOeVFglSTo3F2A",
                               consumer_key="5mgwbSkAZY8PMsv537WyjmwT7",
                               consumer_secret="YrIxXPaIp48yJHWYkGBJOOFtiaRB8adTDFDwprQLiW1klpL4zW",
                               access_token="1012298443241517056-EyBrJ0LMaVTLJSx0U7gH9ewXyKTXDW",
                               access_token_secret="5HtNDhxfy7j4LsCIdzfcnrczNl54k0O8cIv1yroajeNp4")

def get_twitter_sentiment(symbol):
    try:
        # Twitter API v2 kullanarak tweet arama
        tweets = twitter_client.search_recent_tweets(query=symbol, max_results=100)

        sentiment_scores = []
        for tweet in tweets.data:
            analysis = TextBlob(tweet.text)
            sentiment_scores.append(analysis.sentiment.polarity)

        return sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
    except Exception as e:
        st.error(f"Error fetching tweets for {symbol}: {e}")
        return 0

def get_overall_sentiment(symbol):
    news_sentiment = get_news_sentiment(symbol)
    twitter_sentiment = get_twitter_sentiment(symbol)
    overall_sentiment = (news_sentiment + twitter_sentiment) / 2

    if overall_sentiment > 0.05:
        return "Positive"
    elif overall_sentiment < -0.05:
        return "Negative"
    else:
        return "Neutral"


# Support and Resistance 2 hesaplama
def calculate_support_resistance(df, window):
    try:
        df['Support'] = df['low'].rolling(window=window).min()
        df['Resistance'] = df['high'].rolling(window=window).max()
        return df
    except Exception as e:
        st.error(f"Error calculating Support and Resistance: {e}")
        return None
check_candle_shadows = st.sidebar.checkbox("Check Candle Shadows", value=False)
def check_candle_shadows(df, threshold=0.5):
    open_price = df['open'].iloc[-1]
    close_price = df['close'].iloc[-1]
    high_price = df['high'].iloc[-1]
    low_price = df['low'].iloc[-1]

    body = abs(open_price - close_price)
    upper_shadow = high_price - max(open_price, close_price)
    lower_shadow = min(open_price, close_price) - low_price

    if upper_shadow > body * threshold and lower_shadow < body * threshold:
        return "Potential Reversal Down"
    elif lower_shadow > body * threshold and upper_shadow < body * threshold:
        return "Potential Reversal Up"
    return None


# Indicator calculation function
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
        if 'Pivot Point' in params:
            df = calculate_pivot_points(df, method=params['Pivot Point'])
        if 'SR Channels' in params:
             df = calculate_sr_channels(df,
                                   pivot_period=params['SR_PivotPeriod'],
                                   channel_width_percent=params['SR_ChannelWidth'],
                                   min_strength=params['SR_MinStrength'],
                                   max_sr=params['SR_MaxNumber'],
                                   loopback=params['SR_Loopback'])
        return df
    except Exception as e:
        st.error(f"Error calculating indicators: {e}")
        return None

def check_proximity(current_price, indicator_value, threshold):
    if pd.isna(indicator_value):
        return False
    percentage_difference = abs(current_price - indicator_value) / current_price * 100
    return percentage_difference <= threshold
def check_pivot_point_signal(df, params):
    try:
        if 'Pivot Point' in params:
            if df['close'].iloc[-1] > df['Pivot'].iloc[-1] and df['close'].iloc[-2] <= df['Pivot'].iloc[-2]:
                return "Buy"
            elif df['close'].iloc[-1] < df['Pivot'].iloc[-1] and df['close'].iloc[-2] >= df['Pivot'].iloc[-2]:
                return "Sell"
    except Exception as e:
        st.error(f"Error checking signal for Pivot Point: {e}")
    return None
def check_sr_channels_proximity(df, current_price, max_sr, threshold):
    for i in range(max_sr):
        high_col = f'SR_High_{i}'
        low_col = f'SR_Low_{i}'
        if high_col in df.columns and low_col in df.columns:
            high_value = df[high_col].iloc[-1]
            low_value = df[low_col].iloc[-1]
            if pd.notna(high_value) and pd.notna(low_value):
                high_diff = abs(current_price - high_value) / current_price * 100
                low_diff = abs(current_price - low_value) / current_price * 100
                if min(high_diff, low_diff) <= threshold:
                    return True
    return False


check_previous_candle = st.sidebar.checkbox("Check Previous Candle", value=False)

# Signal check function
def check_indicator_signal(df, indicator, params, check_previous=False, check_shadows=False, use_proximity=False, proximity_threshold=1.0):
    try:
        current_price = df['close'].iloc[-1]

        if use_proximity:
            if indicator == 'SMA' and check_proximity(current_price, df['SMA'].iloc[-1], proximity_threshold):
                return "Proximity"
            elif indicator == 'EMA' and check_proximity(current_price, df['EMA'].iloc[-1], proximity_threshold):
                return "Proximity"
            elif indicator == 'Bollinger Bands':
                if check_proximity(current_price, df['BB_High'].iloc[-1], proximity_threshold) or \
                   check_proximity(current_price, df['BB_Low'].iloc[-1], proximity_threshold):
                    return "Proximity"
            elif indicator == 'SR Channels':
                if check_sr_channels_proximity(df, current_price, params['SR_MaxNumber'], proximity_threshold):
                    return "Proximity"

        elif indicator == 'SR Channels':
            last_close = df['close'].iloc[-1]
            for i in range(params['SR_MaxNumber']):
                if f'SR_High_{i}' in df.columns and f'SR_Low_{i}' in df.columns:
                    last_high = df[f'SR_High_{i}'].iloc[-1]
                    last_low = df[f'SR_Low_{i}'].iloc[-1]
                    if pd.notna(last_high) and pd.notna(last_low):
                        if last_close > last_high:
                            return "Buy"
                        elif last_close < last_low:
                            return "Sell"
        if check_previous:
            current_index = -2
            previous_index = -3
        else:
            current_index = -1
            previous_index = -2

        if check_shadows:
            shadow_signal = check_candle_shadows(df)
            if shadow_signal:
                return shadow_signal

        if check_previous:
            current_index = -2
            previous_index = -3
        else:
            current_index = -1
            previous_index = -2


        if indicator == 'Bollinger Bands':
            if params['BB_Type'] == 'Alt Band':
                if df['close'].iloc[-1] < df['BB_Low'].iloc[-1] and df['close'].iloc[-2] >= df['BB_Low'].iloc[-2]:
                    return "Buy"
                elif df['close'].iloc[-1] > df['BB_High'].iloc[-1] and df['close'].iloc[-2] <= df['BB_High'].iloc[-2]:
                    return "Sell"
            else:
                if df['close'].iloc[-1] > df['BB_High'].iloc[-1] and df['close'].iloc[-2] <= df['BB_High'].iloc[-2]:
                    return "Sell"
                elif df['close'].iloc[-1] < df['BB_Low'].iloc[-1] and df['close'].iloc[-2] >= df['BB_Low'].iloc[-2]:
                    return "Buy"
        elif indicator == 'SMA':
            if df['close'].iloc[-1] > df['SMA'].iloc[-1] and df['close'].iloc[-2] <= df['SMA'].iloc[-2]:
                return "Buy"
            elif df['close'].iloc[-1] < df['SMA'].iloc[-1] and df['close'].iloc[-2] >= df['SMA'].iloc[-2]:
                return "Sell"
        elif indicator == 'EMA':
            if df['close'].iloc[-1] > df['EMA'].iloc[-1] and df['close'].iloc[-2] <= df['EMA'].iloc[-2]:
                return "Buy"
            elif df['close'].iloc[-1] < df['EMA'].iloc[-1] and df['close'].iloc[-2] >= df['EMA'].iloc[-2]:
                return "Sell"
        elif indicator == 'RSI':
            if df['RSI'].iloc[-1] < params['RSI_Lower'] and df['RSI'].iloc[-2] >= params['RSI_Lower']:
                return "Buy"
            elif df['RSI'].iloc[-1] > params['RSI_Upper'] and df['RSI'].iloc[-2] <= params['RSI_Upper']:
                return "Sell"
        elif indicator == 'MACD':
            if params['MACD_Type'] == 'Üst Kesişim':
                if df['MACD'].iloc[-1] > df['MACD Signal'].iloc[-1] and df['MACD'].iloc[-2] <= df['MACD Signal'].iloc[-2]:
                    return "Buy"
                elif df['MACD'].iloc[-1] < df['MACD Signal'].iloc[-1] and df['MACD'].iloc[-2] >= df['MACD Signal'].iloc[-2]:
                    return "Sell"
            else:
                if df['MACD'].iloc[-1] < df['MACD Signal'].iloc[-1] and df['MACD'].iloc[-2] >= df['MACD Signal'].iloc[-2]:
                    return "Sell"
                elif df['MACD'].iloc[-1] > df['MACD Signal'].iloc[-1] and df['MACD'].iloc[-2] <= df['MACD Signal'].iloc[-2]:
                    return "Buy"
        elif indicator == 'Stochastic':
            if params['Stochastic_Type'] == 'Üst Kesişim':
                if df['Stochastic'].iloc[-1] > params['Stochastic_Upper'] and df['Stochastic'].iloc[-2] <= params['Stochastic_Upper']:
                    return "Buy"
                elif df['Stochastic'].iloc[-1] < params['Stochastic_Lower'] and df['Stochastic'].iloc[-2] >= params['Stochastic_Lower']:
                    return "Sell"
            else:
                if df['Stochastic'].iloc[-1] < params['Stochastic_Lower'] and df['Stochastic'].iloc[-2] >= params['Stochastic_Lower']:
                    return "Buy"
                elif df['Stochastic'].iloc[-1] > params['Stochastic_Upper'] and df['Stochastic'].iloc[-2] <= params['Stochastic_Upper']:
                    return "Sell"
        elif indicator == 'ADX':
            if df['ADX'].iloc[-1] > params['ADX_Threshold'] and df['ADX'].iloc[-2] <= params['ADX_Threshold']:
                return "Buy"
            elif df['ADX'].iloc[-1] < params['ADX_Threshold'] and df['ADX'].iloc[-2] >= params['ADX_Threshold']:
                return "Sell"
        elif indicator == 'CCI':
            if df['CCI'].iloc[-1] < params['CCI_Lower'] and df['CCI'].iloc[-2] >= params['CCI_Lower']:
                return "Buy"
            elif df['CCI'].iloc[-1] > params['CCI_Upper'] and df['CCI'].iloc[-2] <= params['CCI_Upper']:
                return "Sell"
        elif indicator == 'Williams %R':
            if df['Williams %R'].iloc[-1] < params['Williams %R_Lower'] and df['Williams %R'].iloc[-2] >= params['Williams %R_Lower']:
                return "Buy"
            elif df['Williams %R'].iloc[-1] > params['Williams %R_Upper'] and df['Williams %R'].iloc[-2] <= params['Williams %R_Upper']:
                return "Sell"
        elif indicator == 'ROC':
            if df['ROC'].iloc[-1] > 0 and df['ROC'].iloc[-2] <= 0:
                return "Buy"
            elif df['ROC'].iloc[-1] < 0 and df['ROC'].iloc[-2] >= 0:
                return "Sell"
        elif indicator == 'Ultimate Oscillator':
            if df['Ultimate Oscillator'].iloc[-1] < params['Ultimate Oscillator_Lower'] and df['Ultimate Oscillator'].iloc[-2] >= params['Ultimate Oscillator_Lower']:
                return "Buy"
            elif df['Ultimate Oscillator'].iloc[-1] > params['Ultimate Oscillator_Upper'] and df['Ultimate Oscillator'].iloc[-2] <= params['Ultimate Oscillator_Upper']:
                return "Sell"
        elif indicator == 'Pivot Point':
            return check_pivot_point_signal(df, params)
        elif indicator == 'SR Channels':
              last_close = df['close'].iloc[-1]
              for i in range(params['SR_MaxNumber']):
                  if f'SR_High_{i}' in df.columns and f'SR_Low_{i}' in df.columns:
                    last_high = df[f'SR_High_{i}'].iloc[-1]
                    last_low = df[f'SR_Low_{i}'].iloc[-1]
                    if pd.notna(last_high) and pd.notna(last_low):
                       if last_close > last_high:
                          return "Buy"
                       elif last_close < last_low:
                          return "Sell"
    except Exception as e:
        st.error(f"Error checking signal for {indicator}: {e}")
    return None

# Fetch USDT symbols for futures trading
def get_futures_usdt_symbols():
    try:
        info = client.futures_exchange_info()
        symbols = [s['symbol'] for s in info['symbols'] if 'USDT' in s['symbol']]
        return symbols
    except Exception as e:
        st.error(f"Error fetching futures symbols: {e}")
        return []

# Streamlit UI
st.title("Binance Futures Indicator Analysis Tool")
st.sidebar.header("Indicator Settings")

# Streamlit UI bölümüne ekleyin
proximity_threshold = 1.0  # Varsayılan değer
use_proximity_sensor = st.sidebar.checkbox("Use Proximity Sensor")
if use_proximity_sensor:
    proximity_threshold = st.sidebar.slider("Proximity Threshold (%)", 0.1, 10.0, 1.0, 0.1)

valid_intervals = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
interval = st.sidebar.selectbox("Select Time Interval:", valid_intervals)
# Streamlit UI'da duygu analizi seçeneği ekleyelim
include_sentiment = st.sidebar.checkbox("Include Sentiment Analysis")


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
    'Bollinger Bands': st.sidebar.checkbox('Bollinger Bands'),
    'Pivot Point': st.sidebar.checkbox('Pivot Point')
}


params = {}
if indicators['Pivot Point']:
    params['Pivot Point'] = st.sidebar.selectbox('Pivot Point Type:', ['Classic', 'Fibonacci', 'Woodie', 'Camarilla', 'DM'])
if indicators['SMA']:
    params['SMA'] = st.sidebar.slider('SMA Period:', min_value=5, max_value=200, value=50)
    if params['SMA'] <= 0:
        st.sidebar.error("SMA Period must be greater than 0")

if indicators['RSI']:
    params['RSI'] = st.sidebar.slider('RSI Period:', min_value=5, max_value=200, value=14)
    params['RSI_Lower'] = st.sidebar.slider('RSI Lower Bound:', min_value=0, max_value=100, value=30)
    params['RSI_Upper'] = st.sidebar.slider('RSI Upper Bound:', min_value=0, max_value=100, value=70)
    if params['RSI_Lower'] >= params['RSI_Upper']:
        st.sidebar.error("RSI Lower Bound must be less than RSI Upper Bound")
if indicators['MACD']:
    params['MACD_slow'] = st.sidebar.slider('MACD Slow Period:', min_value=5, max_value=200, value=26)
    params['MACD_fast'] = st.sidebar.slider('MACD Fast Period:', min_value=5, max_value=200, value=12)
    params['MACD_sign'] = st.sidebar.slider('MACD Signal Period:', min_value=5, max_value=200, value=9)
    params['MACD_Type'] = st.sidebar.selectbox('MACD Type:', ['Üst Kesişim', 'Alt Kesişim'])
if indicators['Stochastic']:
    params['Stochastic'] = st.sidebar.slider('Stochastic Period:', min_value=5, max_value=200, value=14)
    params['Stochastic_Upper'] = st.sidebar.slider('Stochastic Upper Bound:', min_value=0, max_value=100, value=80)
    params['Stochastic_Lower'] = st.sidebar.slider('Stochastic Lower Bound:', min_value=0, max_value=100, value=20)
    params['Stochastic_Type'] = st.sidebar.selectbox('Stochastic Type:', ['Üst Kesişim', 'Alt Kesişim'])
if indicators['ADX']:
    params['ADX'] = st.sidebar.slider('ADX Period:', min_value=5, max_value=200, value=14)
    params['ADX_Threshold'] = st.sidebar.slider('ADX Threshold:', min_value=0, max_value=100, value=25)
if indicators['CCI']:
    params['CCI'] = st.sidebar.slider('CCI Period:', min_value=5, max_value=200, value=20)
    params['CCI_Lower'] = st.sidebar.slider('CCI Lower Bound:', min_value=-200, max_value=0, value=-100)
    params['CCI_Upper'] = st.sidebar.slider('CCI Upper Bound:', min_value=0, max_value=200, value=100)
if indicators['Williams %R']:
    params['Williams %R'] = st.sidebar.slider('Williams %R Period:', min_value=5, max_value=200, value=14)
    params['Williams %R_Lower'] = st.sidebar.slider('Williams %R Lower Bound:', min_value=-100, max_value=0, value=-80)
    params['Williams %R_Upper'] = st.sidebar.slider('Williams %R Upper Bound:', min_value=-100, max_value=0, value=-20)
if indicators['ROC']:
    params['ROC'] = st.sidebar.slider('ROC Period:', min_value=5, max_value=200, value=12)
if indicators['Ultimate Oscillator']:
    params['Ultimate Oscillator_short'] = st.sidebar.slider('Ultimate Oscillator Short Period:', min_value=1, max_value=200, value=7)
    params['Ultimate Oscillator_medium'] = st.sidebar.slider('Ultimate Oscillator Medium Period:', min_value=1, max_value=200, value=14)
    params['Ultimate Oscillator_long'] = st.sidebar.slider('Ultimate Oscillator Long Period:', min_value=1, max_value=200, value=28)
    params['Ultimate Oscillator_Lower'] = st.sidebar.slider('Ultimate Oscillator Lower Bound:', min_value=0, max_value=100, value=30)
    params['Ultimate Oscillator_Upper'] = st.sidebar.slider('Ultimate Oscillator Upper Bound:', min_value=0, max_value=100, value=70)
if indicators['Bollinger Bands']:
    params['BB_Period'] = st.sidebar.slider('Bollinger Bands Period:', min_value=5, max_value=200, value=20)
    params['BB_Multiplier'] = st.sidebar.slider('Bollinger Bands Multiplier:', min_value=1.0, max_value=5.0, value=2.0, step=0.1)
    if params['BB_Multiplier'] <= 0:
        st.sidebar.error("Bollinger Bands Multiplier must be greater than 0")
# Kullanıcı arayüzüne SR Channels seçeneğini ekleyin
indicators['SR Channels'] = st.sidebar.checkbox('SR Channels')
if indicators['SR Channels']:
    params['SR_PivotPeriod'] = st.sidebar.slider('SR Channels Pivot Period:', min_value=4, max_value=30, value=10)
    params['SR_ChannelWidth'] = st.sidebar.slider('SR Channels Max Width %:', min_value=1, max_value=8, value=5)
    params['SR_MinStrength'] = st.sidebar.slider('SR Channels Min Strength:', min_value=1, max_value=10, value=1)
    params['SR_MaxNumber'] = st.sidebar.slider('SR Channels Max Number:', min_value=1, max_value=10, value=6)
    params['SR_Loopback'] = st.sidebar.slider('SR Channels Loopback:', min_value=100, max_value=400, value=290)

    if params['SR_Loopback'] <= params['SR_PivotPeriod']:
        st.sidebar.error("SR Channels Loopback must be greater than Pivot Period")

def validate_parameters(params):
    errors = []
    if 'MACD' in params:
        if params['MACD_fast'] >= params['MACD_slow']:
            errors.append("MACD Fast Period must be less than Slow Period")

    if 'Ultimate Oscillator' in params:
        if not (params['Ultimate Oscillator_short'] < params['Ultimate Oscillator_medium'] < params['Ultimate Oscillator_long']):
            errors.append("Ultimate Oscillator periods should be in ascending order (short < medium < long)")

    return errors

# Ana analiz döngüsünden önce
validation_errors = validate_parameters(params)
if validation_errors:
    for error in validation_errors:
        st.error(error)
    st.stop()
# Ana analiz döngüsünde duygu analizini ekleyelim
if st.button("Start Analysis"):
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
                                    signal = check_indicator_signal(df, indicator, params,
                                                                    check_previous_candle,
                                                                    check_candle_shadows,
                                                                    use_proximity_sensor,
                                                                    proximity_threshold)
                                    if signal:
                                        if include_sentiment:
                                            sentiment = get_overall_sentiment(symbol)
                                            futures.append(executor.submit(lambda p: p.append((symbol, indicator, signal, sentiment)), results))
                                        else:
                                            futures.append(executor.submit(lambda p: p.append((symbol, indicator, signal)), results))
                    concurrent.futures.wait(futures)
        asyncio.run(analyze_symbols())

        if results:
            if include_sentiment:
                result_df = pd.DataFrame(results, columns=['Symbol', 'Indicator', 'Signal', 'Sentiment'])
            else:
                result_df = pd.DataFrame(results, columns=['Symbol', 'Indicator', 'Signal'])
            st.write(result_df)
        else:
            st.write("No signals found from the analysis.")
