import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Sayfa yapılandırması
st.set_page_config(page_title="Yatırım Portföyü Oluşturucu", layout="wide")

# Ana başlık
st.title("Kişisel Yatırım Portföyü Oluşturucu")

# Borsa verilerini çekme fonksiyonu
@st.cache_data(ttl=3600)  # 1 saat cache
def get_stock_data(ticker, period='1y'):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        return hist
    except Exception as e:
        st.error(f"Veri çekilirken hata oluştu: {e}")
        return None

# BIST ve global endeksleri tanımlama
INDICES = {
    'BIST 100': '^XU100.IS',
    'S&P 500': '^GSPC',
    'NASDAQ': '^IXIC',
    'DAX': '^GDAXI'
}

# Popüler Türk hisseleri
TURKISH_STOCKS = {
    'Garanti Bankası': 'GARAN.IS',
    'Koç Holding': 'KCHOL.IS',
    'Ereğli Demir Çelik': 'EREGL.IS',
    'Türk Hava Yolları': 'THYAO.IS',
    'Aselsan': 'ASELS.IS'
}

# Yan panel - Kullanıcı bilgileri
with st.sidebar:
    st.header("Kişisel Bilgiler")
    
    # Yatırım tutarı
    yatirim_tutari = st.number_input(
        "Toplam Yatırım Tutarı (TL)",
        min_value=1000,
        value=100000
    )
    
    # Risk toleransı
    risk_toleransi = st.slider(
        "Risk Toleransı",
        min_value=1,
        max_value=10,
        value=5,
        help="1: En düşük risk, 10: En yüksek risk"
    )
    
    # Yatırım vadesi
    yatirim_vadesi = st.selectbox(
        "Yatırım Vadesi",
        options=["Kısa Vade (0-2 yıl)", "Orta Vade (2-5 yıl)", "Uzun Vade (5+ yıl)"]
    )
    
    # Yatırım hedefi
    yatirim_hedefi = st.selectbox(
        "Yatırım Hedefi",
        options=["Sermaye Koruma", "Dengeli Büyüme", "Agresif Büyüme"]
    )

# Portföy oluşturma fonksiyonu
def portfoy_olustur(risk_toleransi, yatirim_vadesi, yatirim_hedefi):
    if risk_toleransi <= 3:
        hisse_orani = 0.2
        tahvil_orani = 0.5
        altin_orani = 0.2
        nakit_orani = 0.1
    elif risk_toleransi <= 7:
        hisse_orani = 0.4
        tahvil_orani = 0.3
        altin_orani = 0.2
        nakit_orani = 0.1
    else:
        hisse_orani = 0.6
        tahvil_orani = 0.2
        altin_orani = 0.15
        nakit_orani = 0.05
    
    if yatirim_vadesi == "Kısa Vade (0-2 yıl)":
        hisse_orani *= 0.7
        tahvil_orani *= 1.2
        nakit_orani *= 1.5
    elif yatirim_vadesi == "Uzun Vade (5+ yıl)":
        hisse_orani *= 1.2
        tahvil_orani *= 0.8
        nakit_orani *= 0.5
    
    if yatirim_hedefi == "Sermaye Koruma":
        hisse_orani *= 0.8
        tahvil_orani *= 1.2
    elif yatirim_hedefi == "Agresif Büyüme":
        hisse_orani *= 1.2
        tahvil_orani *= 0.8
    
    toplam = hisse_orani + tahvil_orani + altin_orani + nakit_orani
    hisse_orani /= toplam
    tahvil_orani /= toplam
    altin_orani /= toplam
    nakit_orani /= toplam
    
    return {
        "Hisse Senetleri": hisse_orani,
        "Tahvil/Bono": tahvil_orani,
        "Altın": altin_orani,
        "Nakit": nakit_orani
    }

# Ana panel - Piyasa Durumu
st.header("Güncel Piyasa Durumu")
col_market1, col_market2 = st.columns(2)

with col_market1:
    st.subheader("Önemli Endeksler")
    for name, ticker in INDICES.items():
        data = get_stock_data(ticker, '5d')
        if data is not None:
            son_fiyat = data['Close'][-1]
            degisim = ((son_fiyat - data['Close'][-2]) / data['Close'][-2]) * 100
            col1, col2 = st.columns([2, 1])
            col1.metric(name, f"{son_fiyat:,.2f}", f"{degisim:+.2f}%")

with col_market2:
    st.subheader("Popüler Türk Hisseleri")
    for name, ticker in TURKISH_STOCKS.items():
        data = get_stock_data(ticker, '5d')
        if data is not None:
            son_fiyat = data['Close'][-1]
            degisim = ((son_fiyat - data['Close'][-2]) / data['Close'][-2]) * 100
            col1, col2 = st.columns([2, 1])
            col1.metric(name, f"{son_fiyat:,.2f} TL", f"{degisim:+.2f}%")

# Portföy Analizi
st.header("Önerilen Portföy Dağılımı")
col1, col2 = st.columns([2, 1])

with col1:
    # Portföy hesaplama
    portfoy = portfoy_olustur(risk_toleransi, yatirim_vadesi, yatirim_hedefi)
    
    # Pasta grafiği
    fig = go.Figure(data=[go.Pie(
        labels=list(portfoy.keys()),
        values=list(portfoy.values()),
        hole=.3
    )])
    fig.update_layout(
        title="Varlık Dağılımı",
        showlegend=True,
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Portföy Detayları")
    
    # Detaylı dağılım tablosu
    df_portfoy = pd.DataFrame({
        'Varlık Sınıfı': portfoy.keys(),
        'Oran (%)': [f"{v*100:.1f}%" for v in portfoy.values()],
        'Tutar (TL)': [f"{v*yatirim_tutari:,.0f} TL" for v in portfoy.values()]
    })
    st.dataframe(df_portfoy, hide_index=True)
    
    # Beklenen getiri ve risk hesaplama
    beklenen_getiri = risk_toleransi * 2
    max_kayip = risk_toleransi * 3
    
    st.markdown("### Beklenen Performans")
    st.write(f"Yıllık Beklenen Getiri: ~%{beklenen_getiri}")
    st.write(f"Maximum Kayıp Riski: -%{max_kayip}")

# Piyasa Analizi
st.header("Detaylı Piyasa Analizi")
secili_endeks = st.selectbox("Analiz edilecek endeks/hisse seçin:", 
                            options=list(INDICES.keys()) + list(TURKISH_STOCKS.keys()))

if secili_endeks in INDICES:
    ticker = INDICES[secili_endeks]
else:
    ticker = TURKISH_STOCKS[secili_endeks]

period = st.select_slider(
    "Analiz Periyodu",
    options=['1mo', '3mo', '6mo', '1y', '2y', '5y'],
    value='1y'
)

data = get_stock_data(ticker, period)

if data is not None:
    # Fiyat grafiği
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'])])
    
    fig.update_layout(
        title=f"{secili_endeks} Fiyat Grafiği",
        yaxis_title="Fiyat",
        xaxis_title="Tarih",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Temel istatistikler
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    with col_stat1:
        st.metric("Günlük Değişim (%)", 
                 f"{((data['Close'][-1] - data['Close'][-2]) / data['Close'][-2] * 100):.2f}%")
    
    with col_stat2:
        st.metric("30 Günlük Volatilite", 
                 f"{(data['Close'].pct_change().std() * np.sqrt(252) * 100):.2f}%")
    
    with col_stat3:
        st.metric("İşlem Hacmi (Son)", 
                 f"{data['Volume'][-1]:,.0f}")

# Öneriler ve uyarılar
st.markdown("---")
st.header("Öneriler ve Dikkat Edilmesi Gerekenler")

with st.expander("Portföy Çeşitlendirme Önerileri"):
    st.write("""
    - Portföyünüzü düzenli olarak gözden geçirin ve rebalancing yapın
    - Tek bir varlık sınıfına aşırı yoğunlaşmaktan kaçının
    - Yatırım kararlarınızı verirken piyasa koşullarını da değerlendirin
    - Acil durum fonu oluşturmayı unutmayın
    - Farklı sektörlerden hisseler seçerek riski dağıtın
    - Global piyasalardaki gelişmeleri takip edin
    """)

with st.expander("Risk Uyarıları"):
    st.write("""
    - Geçmiş performans, gelecekteki performansın garantisi değildir
    - Yatırım yaparken risk-getiri dengesini gözetin
    - Portföy dağılımınızı kişisel finansal hedeflerinize göre ayarlayın
    - Yatırım kararlarınızı vermeden önce profesyonel danışmanlık alabilirsiniz
    - Piyasa koşulları sürekli değişebilir, güncel kalmaya özen gösterin
    """)

# Son güncelleme bilgisi
st.markdown("---")
st.caption(f"Son güncelleme: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
