import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(
    page_title="Benim Web Sitem",
    page_icon="🌟",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Sayfa başlığı
st.set_page_config(page_title="Benim Web Sitem", page_icon="✨")

# Başlık
st.title("Benim Web Sitem")

# Alt başlık
st.header("Streamlit ile yapılmış basit bir web sitesi")

# Metin
st.write("""
    Merhaba! Bu, Streamlit kullanarak Python ile yapılmış bir web sitesi tasarımı örneğidir.
    Burada, farklı işlevsellikler ekleyebilirsiniz, örneğin grafikler, kullanıcı girdileri ve daha fazlası.
""")

# Kullanıcıdan bilgi alma
name = st.text_input("Adınızı girin:", "")
age = st.number_input("Yaşınızı girin:", min_value=0, max_value=100, value=25)

if st.button('Gönder'):
    st.write(f"Merhaba, {name}! Yaşınız: {age}")

# Grafik
x = np.linspace(0, 10, 100)
y = np.sin(x)

fig, ax = plt.subplots()
ax.plot(x, y, label='Sin(x)')
ax.set_xlabel('X ekseni')
ax.set_ylabel('Y ekseni')
ax.set_title('Matplotlib ile Grafik')
ax.legend()

st.pyplot(fig)
