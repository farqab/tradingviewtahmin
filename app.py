import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import requests
import warnings
warnings.filterwarnings('ignore')

# Sayfa yapılandırması
st.set_page_config(page_title="Yatırım Portföyü Oluşturucu", layout="wide")

# Ana başlık
st.title("Kişisel Yatırım Portföyü Oluşturucu")

# Yeni Halka Arzlar Bölümü
UPCOMING_IPOS = {
    "Örnek Şirket A": {
        "halka_arz_tarihi": "2024-12-01",
        "fiyat_araligi": "25-30 TL",
        "lot_buyuklugu": 1000,
        "toplam_buyukluk": "500 Milyon TL",
        "aracı_kurum": "X Yatırım",
        "sektor": "Teknoloji",
        "halka_arz_amaci": "Büyüme ve Yeni Yatırımlar"
    },
    "Örnek Şirket B": {
        "halka_arz_tarihi": "2024-12-15",
        "fiyat_araligi": "40-45 TL",
        "lot_buyuklugu": 500,
        "toplam_buyukluk": "750 Milyon TL",
        "aracı_kurum": "Y Yatırım",
        "sektor": "Sağlık",
        "halka_arz_amaci": "Borç Ödemesi ve İşletme Sermayesi"
    }
}

# Sektör Performans Verileri
SECTOR_PERFORMANCE = {
    "Bankacılık": {"1ay": 5.2, "3ay": 12.5, "1yil": 25.3},
    "Teknoloji": {"1ay": 3.8, "3ay": 9.2, "1yil": 18.7},
    "Sanayi": {"1ay": 4.1, "3ay": 10.8, "1yil": 22.1},
    "Perakende": {"1ay": 2.9, "3ay": 8.5, "1yil": 16.4},
    "Enerji": {"1ay": 4.5, "3ay": 11.2, "1yil": 20.8}
}

# Ana başlık
st.title("Kişisel Yatırım Portföyü Oluşturucu")

# Borsa verilerini çekme fonksiyonu - Geliştirilmiş hata yönetimi
@st.cache_data(ttl=3600)  # 1 saat cache
def get_stock_data(ticker, period='1y'):
    try:
        # BIST hisseleri için özel kontrol
        if ticker.endswith('.IS'):
            # Önce basic veriyi kontrol et
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            if hist.empty:
                # Alternatif ticker dene
                alternative_ticker = ticker.replace('.IS', '.TI')
                stock = yf.Ticker(alternative_ticker)
                hist = stock.history(period=period)
            
            if not hist.empty:
                return hist, stock.info
            else:
                st.warning(f"{ticker} için veri çekilemedi. Lütfen daha sonra tekrar deneyin.")
                return None, None
        else:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            return hist, stock.info
    except Exception as e:
        st.warning(f"{ticker} için veri çekilirken hata oluştu. Alternatif kaynak deneniyor...")
        return None, None

# Yeni Halka Arzlar Bölümü
st.header("Yeni Halka Arzlar")
col_ipo1, col_ipo2 = st.columns([1, 2])

with col_ipo1:
    selected_ipo = st.selectbox(
        "Halka Arz Detayları",
        options=list(UPCOMING_IPOS.keys())
    )
    
    if selected_ipo:
        ipo_data = UPCOMING_IPOS[selected_ipo]
        st.subheader(f"{selected_ipo} Halka Arz Bilgileri")
        for key, value in ipo_data.items():
            st.write(f"{key.replace('_', ' ').title()}: {value}")
        
        # Halka Arz Katılım Hesaplayıcı
        st.subheader("Halka Arz Katılım Hesaplayıcı")
        yatirim_miktari = st.number_input(
            "Yatırım Yapmak İstediğiniz Tutar (TL)",
            min_value=0,
            value=10000
        )
        
        fiyat_min, fiyat_max = map(float, ipo_data["fiyat_araligi"].split("-")[0:2])
        lot_buyuklugu = ipo_data["lot_buyuklugu"]
        
        max_lot = yatirim_miktari // (fiyat_min * lot_buyuklugu)
        toplam_maliyet_min = max_lot * lot_buyuklugu * fiyat_min
        toplam_maliyet_max = max_lot * lot_buyuklugu * fiyat_max
        
        st.write(f"Alabileceğiniz Maximum Lot: {max_lot}")
        st.write(f"Toplam Maliyet Aralığı: {toplam_maliyet_min:,.2f} TL - {toplam_maliyet_max:,.2f} TL")

with col_ipo2:
    # Halka Arz Takvimi
    st.subheader("Halka Arz Takvimi")
    
    # Tarih sıralaması için halka arzları düzenle
    sorted_ipos = sorted(UPCOMING_IPOS.items(), key=lambda x: datetime.strptime(x[1]['halka_arz_tarihi'], '%Y-%m-%d'))
    
    # Gantt chart için data hazırla
    gantt_data = []
    for company, data in sorted_ipos:
        start_date = datetime.strptime(data['halka_arz_tarihi'], '%Y-%m-%d')
        end_date = start_date + timedelta(days=7)  # Varsayılan 1 haftalık süreç
        
        gantt_data.append(dict(
            Task=company,
            Start=start_date,
            Finish=end_date,
            Resource=data['sektor']
        ))
    
    df_gantt = pd.DataFrame(gantt_data)
    
    fig = px.timeline(df_gantt, x_start="Start", x_end="Finish", y="Task", color="Resource",
                     title="Halka Arz Takvimi")
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

# Sektör Analizi Bölümü
st.header("Sektör Analizi")
col_sector1, col_sector2 = st.columns(2)

with col_sector1:
    # Sektör performans karşılaştırması
    sector_df = pd.DataFrame(SECTOR_PERFORMANCE).T
    
    fig_sector = go.Figure()
    for period in sector_df.columns:
        fig_sector.add_trace(go.Bar(
            name=period,
            x=sector_df.index,
            y=sector_df[period],
            text=sector_df[period].apply(lambda x: f'{x:.1f}%'),
            textposition='auto',
        ))
    
    fig_sector.update_layout(
        title="Sektör Performansları",
        barmode='group',
        height=400
    )
    st.plotly_chart(fig_sector, use_container_width=True)

with col_sector2:
    # Sektör korelasyon matrisi
    st.subheader("Sektör Korelasyon Analizi")
    
    # Örnek korelasyon verileri
    correlation_data = np.array([
        [1.0, 0.7, 0.5, 0.3, 0.4],
        [0.7, 1.0, 0.6, 0.4, 0.5],
        [0.5, 0.6, 1.0, 0.5, 0.6],
        [0.3, 0.4, 0.5, 1.0, 0.7],
        [0.4, 0.5, 0.6, 0.7, 1.0]
    ])
    
    sectors = list(SECTOR_PERFORMANCE.keys())
    
    fig_corr = go.Figure(data=go.Heatmap(
        z=correlation_data,
        x=sectors,
        y=sectors,
        colorscale='RdBu',
        zmin=-1,
        zmax=1
    ))
    
    fig_corr.update_layout(
        title="Sektörler Arası Korelasyon",
        height=400
    )
    st.plotly_chart(fig_corr, use_container_width=True)

# BIST ve global endeksleri tanımlama - Alternatif tickerlar eklendi
INDICES = {
    'BIST 100': 'XU100.IS',  # Alternatif: 'XU100.TI'
    'S&P 500': '^GSPC',
    'NASDAQ': '^IXIC',
    'DAX': '^GDAXI'
}

# Popüler Türk hisseleri - Alternatif formatlar eklendi
TURKISH_STOCKS = {
    'Garanti Bankası': 'GARAN.IS',
    'Koç Holding': 'KCHOL.IS',
    'Ereğli Demir Çelik': 'EREGL.IS',
    'Türk Hava Yolları': 'THYAO.IS',
    'Aselsan': 'ASELS.IS',
    'Akbank': 'AKBNK.IS',
    'Yapı Kredi': 'YKBNK.IS',
    'Tüpraş': 'TUPRS.IS',
    'Arçelik': 'ARCLK.IS',
    'Ford Otosan': 'FROTO.IS',
    'Şişe Cam': 'SISE.IS',
    'Sabancı Holding': 'SAHOL.IS',
    'Turkcell': 'TCELL.IS',
    'Petkim': 'PETKM.IS',
    'BİM': 'BIMAS.IS'
}

# Veri olmadığında kullanılacak dummy veri oluşturma fonksiyonu
def create_dummy_data(ticker, period='1y'):
    end_date = datetime.now()
    
    if period == '1y':
        start_date = end_date - timedelta(days=365)
    elif period == '1mo':
        start_date = end_date - timedelta(days=30)
    elif period == '5d':
        start_date = end_date - timedelta(days=5)
    else:
        start_date = end_date - timedelta(days=365)
    
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Rastgele fiyat hareketi oluştur
    np.random.seed(42)  # Tekrarlanabilirlik için
    prices = np.random.randn(len(date_range)).cumsum() + 100
    
    df = pd.DataFrame({
        'Open': prices + np.random.randn(len(date_range)),
        'High': prices + abs(np.random.randn(len(date_range))),
        'Low': prices - abs(np.random.randn(len(date_range))),
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, size=len(date_range))
    }, index=date_range)
    
    return df

# Veri çekme fonksiyonunu güncelle
def get_market_data(ticker, period='1y'):
    data, info = get_stock_data(ticker, period)
    
    if data is None:
        st.warning(f"{ticker} için gerçek veri alınamadı. Gösterim amaçlı örnek veri kullanılıyor.")
        data = create_dummy_data(ticker, period)
        info = {
            'shortName': ticker,
            'regularMarketPrice': data['Close'].iloc[-1],
            'regularMarketPreviousClose': data['Close'].iloc[-2]
        }
    
    return data, info

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
    
    # Yatırım vadesi - Kısa vadeli seçenekler eklendi
    yatirim_vadesi = st.selectbox(
        "Yatırım Vadesi",
        options=[
            "Günlük Trade", 
            "Haftalık", 
            "Aylık",
            "Kısa Vade (0-2 yıl)", 
            "Orta Vade (2-5 yıl)", 
            "Uzun Vade (5+ yıl)"
        ]
    )
    
    # Yatırım hedefi
    yatirim_hedefi = st.selectbox(
        "Yatırım Hedefi",
        options=["Sermaye Koruma", "Dengeli Büyüme", "Agresif Büyüme"]
    )
    
    # Özel hisse seçimi
    st.header("Özel Hisse Seçimi")
    secili_hisseler = st.multiselect(
        "Portföyünüze eklemek istediğiniz hisseler:",
        options=list(TURKISH_STOCKS.keys()),
        default=["Garanti Bankası", "Koç Holding"]
    )
    
    if secili_hisseler:
        hisse_agirliklar = {}
        st.write("Her hisse için ağırlık belirleyin (%):")
        toplam_agirlik = 0
        for hisse in secili_hisseler:
            agirlik = st.slider(f"{hisse} ağırlığı (%)", 0, 100, 
                              value=100 // len(secili_hisseler),
                              key=f"weight_{hisse}")
            hisse_agirliklar[hisse] = agirlik
            toplam_agirlik += agirlik
        
        if toplam_agirlik != 100:
            st.warning(f"Toplam ağırlık 100% olmalıdır. Şu anki toplam: {toplam_agirlik}%")

# Portföy oluşturma fonksiyonu - Güncellendi
def portfoy_olustur(risk_toleransi, yatirim_vadesi, yatirim_hedefi):
    # Temel dağılım
    if yatirim_vadesi in ["Günlük Trade", "Haftalık"]:
        hisse_orani = 0.8
        tahvil_orani = 0.05
        altin_orani = 0.1
        nakit_orani = 0.05
    elif yatirim_vadesi == "Aylık":
        hisse_orani = 0.6
        tahvil_orani = 0.15
        altin_orani = 0.15
        nakit_orani = 0.1
    elif risk_toleransi <= 3:
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
    
    # Vade bazlı ayarlamalar
    if yatirim_vadesi == "Kısa Vade (0-2 yıl)":
        hisse_orani *= 0.7
        tahvil_orani *= 1.2
        nakit_orani *= 1.5
    elif yatirim_vadesi == "Uzun Vade (5+ yıl)":
        hisse_orani *= 1.2
        tahvil_orani *= 0.8
        nakit_orani *= 0.5
    
    # Hedef bazlı ayarlamalar
    if yatirim_hedefi == "Sermaye Koruma":
        hisse_orani *= 0.8
        tahvil_orani *= 1.2
    elif yatirim_hedefi == "Agresif Büyüme":
        hisse_orani *= 1.2
        tahvil_orani *= 0.8
    
    # Normalizasyon
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

# Portföy Optimizasyonu
st.header("Portföy Optimizasyonu")
with st.expander("Portföy Optimizasyonu Detayları"):
    col_opt1, col_opt2 = st.columns(2)
    
    with col_opt1:
        st.subheader("Risk-Getiri Optimizasyonu")
        risk_free_rate = st.slider(
            "Risksiz Faiz Oranı (%)",
            min_value=0.0,
            max_value=30.0,
            value=15.0,
            step=0.1
        )
        
        optimization_method = st.selectbox(
            "Optimizasyon Metodu",
            ["Minimum Varyans", "Maximum Sharpe Oranı", "Risk Paritesi"]
        )
    
    with col_opt2:
        st.subheader("Kısıtlamalar")
        max_weight = st.slider(
            "Maximum Hisse Ağırlığı (%)",
            min_value=0,
            max_value=100,
            value=30
        )
        
        min_stocks = st.slider(
            "Minimum Hisse Sayısı",
            min_value=1,
            max_value=10,
            value=3
        )

# Piyasa Haberleri ve Duyurular
st.header("Piyasa Haberleri ve Duyurular")
with st.expander("Son Gelişmeler"):
    col_news1, col_news2 = st.columns(2)
    
    with col_news1:
        st.subheader("Önemli Ekonomik Veriler")
        economic_data = {
            "TÜFE": "12.5%",
            "ÜFE": "15.2%",
            "İşsizlik": "9.8%",
            "Büyüme": "3.5%",
            "Cari Açık": "-2.5 Milyar $"
        }
        
        for indicator, value in economic_data.items():
            st.metric(indicator, value)
    
    with col_news2:
        st.subheader("Yaklaşan Önemli Tarihler")
        events = {
            "2024-12-01": "TCMB Para Politikası Kurulu",
            "2024-12-15": "TÜFE Açıklanması",
            "2024-12-20": "Ödemeler Dengesi",
            "2024-12-25": "Kapasite Kullanım Oranı"
        }
        
        for date, event in events.items():
            st.write(f"{date}: {event}")


# Teknik analiz göstergeleri hesaplama
def hesapla_teknik_gostergeler(data):
    df = data.copy()
    
    # RSI hesaplama (14 günlük)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD hesaplama
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # Bollinger Bands
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['20dSTD'] = df['Close'].rolling(window=20).std()
    df['Upper_Band'] = df['MA20'] + (df['20dSTD'] * 2)
    df['Lower_Band'] = df['MA20'] - (df['20dSTD'] * 2)
    
    return df

# Ana panel - Piyasa Durumu
st.header("Güncel Piyasa Durumu")
col_market1, col_market2 = st.columns(2)

with col_market1:
    st.subheader("Önemli Endeksler")
    for name, ticker in INDICES.items():
        data, _ = get_stock_data(ticker, '5d')
        if data is not None:
            son_fiyat = data['Close'][-1]
            degisim = ((son_fiyat - data['Close'][-2]) / data['Close'][-2]) * 100
            col1, col2 = st.columns([2, 1])
            col1.metric(name, f"{son_fiyat:,.2f}", f"{degisim:+.2f}%")

with col_market2:
    st.subheader("Seçili Hisseler")
    for name in secili_hisseler:
        ticker = TURKISH_STOCKS[name]
        data, stock_info = get_stock_data(ticker, '5d')
        if data is not None:
            son_fiyat = data['Close'][-1]
            degisim = ((son_fiyat - data['Close'][-2]) / data['Close'][-2]) * 100
            col1, col2 = st.columns([2, 1])
            col1.metric(name, f"{son_fiyat:,.2f} TL", f"{degisim:+.2f}%")

# Portföy Analizi
st.header("Önerilen Portföy Dağılımı")
col1, col2 = st.columns([2, 1])

with col1:
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
    
    df_portfoy = pd.DataFrame({
        'Varlık Sınıfı': portfoy.keys(),
        'Oran (%)': [f"{v*100:.1f}%" for v in portfoy.values()],
        'Tutar (TL)': [f"{v*yatirim_tutari:,.0f} TL" for v in portfoy.values()]
    })
    st.dataframe(df_portfoy, hide_index=True)
    
    beklenen_getiri = risk_toleransi * 2
    max_kayip = risk_toleransi * 3
    
    st.markdown("### Beklenen Performans")
    st.write(f"Yıllık Beklenen Getiri: ~%{beklenen_getiri}")
    st.write(f"Maximum Kayıp Riski: -%{max_kayip}")

# Detaylı Analiz Bölümü
st.header("Detaylı Teknik Analiz")
col_analysis1, col_analysis2 = st.columns([1, 2])

with col_analysis1:
    analiz_hisse = st.selectbox(
        "Analiz edilecek hisse/endeks:",
        options=list(INDICES.keys()) + list(TURKISH_STOCKS.keys())
    )
    
    period = st.select_slider(
        "Analiz Periyodu",
        options=['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y'],
        value='1mo'
    )
    
    interval = st.select_slider(
        "Veri Aralığı",
        options=['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'],
        value='1d'
    )

with col_analysis2:
    if analiz_hisse in INDICES:
        ticker = INDICES[analiz_hisse]
    else:
        ticker = TURKISH_STOCKS[analiz_hisse]

    data, stock_info = get_stock_data(ticker, period)
    
    if data is not None:
        # Teknik göstergeleri hesapla
        teknik_data = hesapla_teknik_gostergeler(data)
        
        # Ana grafik
        fig = go.Figure()
        
        # Mum grafiği
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Fiyat"
        ))
        
        # Bollinger Bands devamı
        fig.add_trace(go.Scatter(x=teknik_data.index, y=teknik_data['MA20'],
                                name='20 Günlük Ortalama', line=dict(color='orange')))
        fig.add_trace(go.Scatter(x=teknik_data.index, y=teknik_data['Lower_Band'],
                                name='Alt Bant', line=dict(color='gray', dash='dash')))
        
        fig.update_layout(
            title=f"{analiz_hisse} Fiyat ve Teknik Analiz Grafiği",
            yaxis_title="Fiyat",
            xaxis_title="Tarih",
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Teknik göstergeler
        col_indicators1, col_indicators2, col_indicators3 = st.columns(3)
        
        with col_indicators1:
            st.metric("RSI (14)", 
                     f"{teknik_data['RSI'].iloc[-1]:.2f}",
                     f"{teknik_data['RSI'].iloc[-1] - teknik_data['RSI'].iloc[-2]:.2f}")
            
            # RSI yorumu
            rsi_value = teknik_data['RSI'].iloc[-1]
            if rsi_value > 70:
                st.warning("RSI aşırı alım bölgesinde")
            elif rsi_value < 30:
                st.warning("RSI aşırı satım bölgesinde")
        
        with col_indicators2:
            macd = teknik_data['MACD'].iloc[-1]
            signal = teknik_data['Signal'].iloc[-1]
            st.metric("MACD", 
                     f"{macd:.2f}",
                     f"{macd - signal:.2f}")
            
            # MACD yorumu
            if macd > signal:
                st.success("MACD pozitif sinyal veriyor")
            else:
                st.error("MACD negatif sinyal veriyor")
        
        with col_indicators3:
            volatilite = teknik_data['Close'].pct_change().std() * np.sqrt(252) * 100
            st.metric("Yıllık Volatilite", 
                     f"%{volatilite:.2f}")
            
            # Volatilite yorumu
            if volatilite > 50:
                st.warning("Yüksek volatilite")
            elif volatilite < 20:
                st.info("Düşük volatilite")

        # Destek ve Direnç Seviyeleri
        st.subheader("Destek ve Direnç Seviyeleri")
        col_support1, col_support2 = st.columns(2)
        
        # Son 20 günlük veriden destek ve direnç hesaplama
        son_20_gun = teknik_data['Close'].tail(20)
        min_fiyat = son_20_gun.min()
        max_fiyat = son_20_gun.max()
        current_price = son_20_gun.iloc[-1]
        
        with col_support1:
            st.write("Güçlü Direnç:", f"{max_fiyat * 1.02:.2f}")
            st.write("Direnç:", f"{max_fiyat:.2f}")
        
        with col_support2:
            st.write("Destek:", f"{min_fiyat:.2f}")
            st.write("Güçlü Destek:", f"{min_fiyat * 0.98:.2f}")

        # Hacim Analizi
        st.subheader("Hacim Analizi")
        fig_volume = go.Figure()
        
        # Hacim çubuklarını ekle
        fig_volume.add_trace(go.Bar(
            x=data.index,
            y=data['Volume'],
            name="Hacim",
            marker_color='rgba(0,0,255,0.5)'
        ))
        
        # Ortalama hacim çizgisi
        avg_volume = data['Volume'].rolling(window=20).mean()
        fig_volume.add_trace(go.Scatter(
            x=data.index,
            y=avg_volume,
            name="20 Günlük Ortalama Hacim",
            line=dict(color='red')
        ))
        
        fig_volume.update_layout(
            title="Hacim Analizi",
            yaxis_title="Hacim",
            xaxis_title="Tarih",
            height=300
        )
        
        st.plotly_chart(fig_volume, use_container_width=True)

        # Momentum Göstergeleri
        st.subheader("Momentum Göstergeleri")
        col_mom1, col_mom2, col_mom3 = st.columns(3)
        
        with col_mom1:
            # ROC (Rate of Change) hesaplama
            roc = ((data['Close'].iloc[-1] - data['Close'].iloc[-10]) / data['Close'].iloc[-10]) * 100
            st.metric("10 Günlük ROC", 
                     f"%{roc:.2f}")
        
        with col_mom2:
            # Momentum hesaplama
            momentum = data['Close'].iloc[-1] - data['Close'].iloc[-10]
            st.metric("10 Günlük Momentum", 
                     f"{momentum:.2f}")
        
        with col_mom3:
            # Fiyat Değişimi
            price_change = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100
            st.metric(f"{period} Fiyat Değişimi", 
                     f"%{price_change:.2f}")

        # Al/Sat Sinyalleri
        st.subheader("Teknik Analiz Sinyalleri")
        
        signals = []
        
        # RSI bazlı sinyal
        if rsi_value > 70:
            signals.append(("RSI", "Sat", "Aşırı alım bölgesinde"))
        elif rsi_value < 30:
            signals.append(("RSI", "Al", "Aşırı satım bölgesinde"))
        
        # MACD bazlı sinyal
        if macd > signal:
            signals.append(("MACD", "Al", "MACD sinyal çizgisini yukarı kesti"))
        else:
            signals.append(("MACD", "Sat", "MACD sinyal çizgisini aşağı kesti"))
        
        # Bollinger Bands bazlı sinyal
        last_close = data['Close'].iloc[-1]
        if last_close > teknik_data['Upper_Band'].iloc[-1]:
            signals.append(("Bollinger", "Sat", "Üst bandın üzerinde"))
        elif last_close < teknik_data['Lower_Band'].iloc[-1]:
            signals.append(("Bollinger", "Al", "Alt bandın altında"))
        
        # Sinyalleri tablo olarak göster
        df_signals = pd.DataFrame(signals, columns=['Gösterge', 'Sinyal', 'Açıklama'])
        st.dataframe(df_signals, hide_index=True)

# Alım-Satım Stratejileri
st.header("Alım-Satım Stratejileri")

strateji_tipi = st.selectbox(
    "Strateji Tipi",
    ["Günlük Trade", "Swing Trade", "Pozisyon Trade"]
)

if strateji_tipi == "Günlük Trade":
    st.write("""
    ### Günlük Trade Stratejisi
    - Açılış sonrası ilk 30 dakika trendin belirlenmesi
    - Hacim artışlarının takibi
    - Gün içi destek/direnç seviyelerinin kullanımı
    - Stop-loss seviyesi: Giriş fiyatının %1 altı
    - Kar hedefi: Risk/Ödül oranı minimum 1:2
    """)
elif strateji_tipi == "Swing Trade":
    st.write("""
    ### Swing Trade Stratejisi
    - 4 saatlik grafiklerde trend analizi
    - MACD ve RSI uyumlu sinyaller
    - Bollinger Bands kırılmaları
    - Stop-loss seviyesi: Giriş fiyatının %2-3 altı
    - Kar hedefi: Risk/Ödül oranı minimum 1:3
    """)
else:
    st.write("""
    ### Pozisyon Trade Stratejisi
    - Günlük ve haftalık grafiklerde trend analizi
    - Temel analiz göstergelerinin takibi
    - Sektörel momentum analizi
    - Stop-loss seviyesi: Giriş fiyatının %5-7 altı
    - Kar hedefi: Risk/Ödül oranı minimum 1:4
    """)

# Risk Yönetimi
st.header("Risk Yönetimi Önerileri")
with st.expander("Risk Yönetimi Detayları"):
    st.write("""
    ### Stop Loss Seviyeleri
    - Günlük Trade: %1-2
    - Swing Trade: %2-4
    - Pozisyon Trade: %5-8
    
    ### Pozisyon Büyüklüğü
    - Tek pozisyonda portföyün maksimum %5'i
    - Aynı sektörde maksimum %20 pozisyon
    - Korelasyonu yüksek hisselerde toplam pozisyon maksimum %25
    
    ### Risk/Ödül Oranları
    - Minimum 1:2
    - Önerilen 1:3
    - İdeal 1:4 ve üzeri
    """)

# Son güncelleme bilgisi
st.markdown("---")
st.caption(f"Son güncelleme: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
