import streamlit as st
import google.generativeai as genai
import os # Untuk mengakses variabel lingkungan

# ==============================================================================
# PENGATURAN API KEY DAN MODEL (PENTING! UNTUK DEPLOYMENT)
# ==============================================================================

# Mengambil API Key dari Streamlit Secrets atau Environment Variables
# Di Streamlit Cloud, Anda akan menambahkan API_KEY di bagian Secrets.
# Di lokal, Anda bisa mengatur variabel lingkungan 'GEMINI_API_KEY'.
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("🚨 GEMINI_API_KEY tidak ditemukan. Harap atur di Streamlit Secrets atau sebagai variabel lingkungan.")
    st.stop() # Hentikan eksekusi aplikasi jika API Key tidak ada

# Nama model Gemini yang akan digunakan.
MODEL_NAME = 'gemini-1.5-flash' # Sesuai pilihan Anda

# ==============================================================================
# KONTEKS AWAL CHATBOT
# ==============================================================================

# Definisikan peran chatbot Anda di sini.
# Ini adalah "instruksi sistem" yang akan membuat chatbot berperilaku sesuai keinginan Anda.
# Buatlah singkat, jelas, dan langsung pada intinya untuk menghemat token.
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
        # st.success("Gemini API Key berhasil dikonfigurasi.") # Bisa diaktifkan untuk debugging
    except Exception as e:
        st.error(f"Kesalahan saat mengkonfigurasi API Key Gemini: {e}")
        st.stop() # Hentikan aplikasi jika konfigurasi gagal
    
    try:
        model = genai.GenerativeModel(
            MODEL_NAME,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=500
            )
        )
        # st.success(f"Model '{MODEL_NAME}' berhasil diinisialisasi.") # Bisa diaktifkan untuk debugging
        return model
    except Exception as e:
        st.error(f"Kesalahan saat inisialisasi model '{MODEL_NAME}': {e}")
        st.stop() # Hentikan aplikasi jika inisialisasi model gagal

# Panggil fungsi konfigurasi
model = configure_gemini()

# Inisialisasi sesi chat di Streamlit's session_state
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=INITIAL_CHATBOT_CONTEXT)
    # Tambahkan pesan pembuka dari chatbot ke riwayat chat Streamlit
    st.session_state.messages = []
    for msg in INITIAL_CHATBOT_CONTEXT:
        st.session_state.messages.append({"role": msg["role"], "content": msg["parts"][0]})


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
    # Tambahkan input pengguna ke riwayat chat Streamlit
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("Sedang memproses jawaban..."):
            # Kirim input pengguna ke sesi chat Gemini
            # Menggunakan .send_message() akan secara otomatis memperbarui history di objek chat_session
            response = st.session_state.chat_session.send_message(prompt, request_options={"timeout": 60})
            
            # Pastikan respons valid sebelum menampilkannya
            if response and response.text:
                chatbot_response = response.text
            else:
                chatbot_response = "Maaf, saya tidak bisa memberikan balasan. Respons API kosong atau tidak valid."

        # Tambahkan respons chatbot ke riwayat chat Streamlit
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

# Tombol untuk mereset chat (opsional, tapi berguna)
if st.button("Mulai Chat Baru"):
    st.session_state.chat_session = model.start_chat(history=INITIAL_CHATBOT_CONTEXT)
    st.session_state.messages = []
    for msg in INITIAL_CHATBOT_CONTEXT:
        st.session_state.messages.append({"role": msg["role"], "content": msg["parts"][0]})
    st.experimental_rerun() # Refresh aplikasi untuk menampilkan chat baru