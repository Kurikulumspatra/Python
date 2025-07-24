import streamlit as st
import google.generativeai as genai
import os

# ==============================================================================
# PENGATURAN API KEY DAN MODEL (PENTING! UNTUK DEPLOYMENT)
# ==============================================================================

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("🚨 GEMINI_API_KEY tidak ditemukan. Harap atur di Streamlit Secrets atau sebagai variabel lingkungan.")
    st.stop()

MODEL_NAME = 'gemini-1.5-flash'

# ==============================================================================
# KONTEKS AWAL CHATBOT
# ==============================================================================

INITIAL_CHATBOT_CONTEXT = [
    {
        "role": "user",
        "parts": ["anda adalah konsultan jasa keuangan virtual yang informatif dan profesional. tugas anda adalah memberikan informasi umum dan panduan dasar tentang produk/layanan keuangan (investasi, asuransi, pinjaman, perencanaan) dengan jawaban singkat dan relevan. jangan berikan nasihat investasi personal atau spesifik. batasi respons maksimal 100 kata. arahkan pengguna ke konsultan manusia untuk saran mendalam"]
    },
    {
        "role": "model",
        "parts": ["Baik! Apa yang akan kamu konsultasikan hari ini."]
    }
]

# ==============================================================================
# INISIALISASI GEMINI (FUNGSI UTAMA CHATBOT)
# ==============================================================================

@st.cache_resource
def configure_gemini():
    """Mengkonfigurasi Gemini API sekali saat aplikasi dimulai."""
    try:
        genai.configure(api_key=API_KEY)
    except Exception as e:
        st.error(f"Kesalahan saat mengkonfigurasi API Key Gemini: {e}")
        st.stop()
    
    try:
        model = genai.GenerativeModel(
            MODEL_NAME,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=500
            )
        )
        return model
    except Exception as e:
        st.error(f"Kesalahan saat inisialisasi model '{MODEL_NAME}': {e}")
        st.stop()

model = configure_gemini()

# Inisialisasi sesi chat di Streamlit's session_state
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=INITIAL_CHATBOT_CONTEXT)
    
    # --- PERUBAHAN PENTING DI SINI ---
    # Inisialisasi riwayat pesan yang ditampilkan kepada pengguna.
    # Hanya tambahkan balasan awal dari model (INITIAL_CHATBOT_CONTEXT[1]),
    # BUKAN prompt sistem (INITIAL_CHATBOT_CONTEXT[0])
    st.session_state.messages = [
        {"role": INITIAL_CHATBOT_CONTEXT[1]["role"], "content": INITIAL_CHATBOT_CONTEXT[1]["parts"][0]}
    ]
    # --- END PERUBAHAN PENTING ---


# ==============================================================================
# ANTARMUKA PENGGUNA STREAMLIT
# ==============================================================================

st.set_page_config(
    page_title="Konsultan Keuangan Virtual",
    page_icon="💰",
    layout="centered"
)

st.title("💰 Konsultan Jasa Keuangan Virtual Anda")
st.markdown(
    """
    Saya adalah asisten virtual yang berpengetahuan luas tentang jasa keuangan.
    Tanyakan apa saja seputar **investasi, asuransi, pinjaman, atau perencanaan keuangan.**
    """
)

# Tampilkan riwayat chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input pengguna
if prompt := st.chat_input("Tanyakan sesuatu..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("Sedang memproses jawaban..."):
            response = st.session_state.chat_session.send_message(prompt, request_options={"timeout": 60})
            
            if response and response.text:
                chatbot_response = response.text
            else:
                chatbot_response = "Maaf, saya tidak bisa memberikan balasan. Respons API kosong atau tidak valid."

        st.session_state.messages.append({"role": "assistant", "content": chatbot_response})
        with st.chat_message("assistant"):
            st.markdown(chatbot_response)

    except Exception as e:
        error_message = f"""
        Maaf, terjadi kesalahan saat berkomunikasi dengan Gemini:
        - **Detail:** {e}
        - **Kemungkinan penyebab:** Masalah koneksi internet, API Key tidak valid/kadaluarsa, atau melebihi kuota.
        """
        st.error(error_message)
        st.session_state.messages.append({"role": "assistant", "content": f"Maaf, terjadi kesalahan: {e}"})
        with st.chat_message("assistant"):
            st.markdown(f"Maaf, terjadi kesalahan: {e}")

# Tombol untuk mereset chat
if st.button("Mulai Chat Baru"):
    st.session_state.chat_session = model.start_chat(history=INITIAL_CHATBOT_CONTEXT)
    # HANYA tambahkan balasan awal model ke messages yang ditampilkan
    st.session_state.messages = [
        {"role": INITIAL_CHATBOT_CONTEXT[1]["role"], "content": INITIAL_CHATBOT_CONTEXT[1]["parts"][0]}
    ]
    st.rerun() # <--- GANTI BAGIAN INI: DARI st.experimental_rerun() MENJADI st.rerun()
