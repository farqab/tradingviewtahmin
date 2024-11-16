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

[... Mevcut kod devam ediyor ...]

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

# Son güncelleme bilgisi
st.markdown("---")
st.caption(f"Son güncelleme: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
