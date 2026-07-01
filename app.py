import os
import asyncio
import streamlit as st

st.set_page_config(page_title="AeroSense AI", page_icon="🌬️", layout="centered")

# ---- Setup kredensial: jalan di LOKAL (.env + gcloud) & CLOUD (st.secrets) ----
def _secret(key, default=None):
    try:
        return st.secrets[key]
    except Exception:
        return default

_api_key = _secret("GOOGLE_API_KEY")
if _api_key:  # mode CLOUD
    os.environ["GOOGLE_API_KEY"] = _api_key
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
    os.environ["GOOGLE_CLOUD_PROJECT"] = _secret("GOOGLE_CLOUD_PROJECT", "aerosense-ai-501007")
    _adc = _secret("ADC_JSON")
    if _adc:
        with open("adc.json", "w") as f:
            f.write(_adc)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("adc.json")
else:  # mode LOKAL
    from dotenv import load_dotenv
    load_dotenv(os.path.join("aerosense", ".env"))

# import agent SETELAH kredensial siap
from google.genai import types
from google.adk.runners import InMemoryRunner
from aerosense.agent import root_agent

APP_NAME, USER_ID = "aerosense", "user"

@st.cache_resource
def get_runner():
    return InMemoryRunner(agent=root_agent, app_name=APP_NAME)

runner = get_runner()

async def _ensure_session(sid):
    svc = runner.session_service
    try:
        s = await svc.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=sid)
    except Exception:
        s = None
    if not s:
        await svc.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=sid)

# Fungsi _ask DIUPDATE untuk menerima image
async def _ask(sid, text, image_bytes=None, mime_type=None):
    await _ensure_session(sid)
    
    parts = []
    if image_bytes and mime_type:
        parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
    parts.append(types.Part.from_text(text=text))
    
    content = types.Content(role="user", parts=parts)
    
    final = ""
    async for event in runner.run_async(user_id=USER_ID, session_id=sid, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            final = event.content.parts[0].text or final
    return final

# Fungsi ask DIUPDATE untuk menerima image
def ask(sid, text, image_bytes=None, mime_type=None):
    return asyncio.run(_ask(sid, text, image_bytes, mime_type))

# ---------------- UI ----------------
st.title("🌬️ AeroSense AI")
st.caption("Asisten analitik kualitas udara kota-kota Asia-Pasifik — tanya pakai bahasa biasa.")

# ---- SIDEBAR: Upload Foto (Multimodal) ----
with st.sidebar:
    st.header("📸 Analisis Visual")
    st.write("Coba unggah foto langit di sekitarmu, lalu tanyakan tentang polusi dari foto tersebut!")
    uploaded_file = st.file_uploader("Upload foto langit kota Anda", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="Foto yang akan dianalisis", use_container_width=True)

if "sid" not in st.session_state:
    st.session_state.sid = "s-" + os.urandom(4).hex()
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.expander("💡 Contoh pertanyaan"):
    st.markdown(
        "- Berapa PM2.5 terbaru di Jakarta?\n"
        "- 5 kota paling berpolusi di APAC?\n"
        "- (Sambil upload foto): Tolong analisis visibilitas di foto ini, apakah sesuai dengan data BigQuery hari ini?\n"
        "- (Pakai Internet): Apa berita terbaru tentang polusi udara di Delhi menurut Google Search?"
    )

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# HANYA ADA SATU CHAT_INPUT DI SINI
# ... (kode sebelumnya di app.py)
if prompt := st.chat_input("Tanya soal kualitas udara..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        with st.spinner("Menganalisis data dari BigQuery, Internet & Visual..."):
            try:
                # Cek apakah ada file foto yang di-upload dari Sidebar
                if uploaded_file is not None:
                    img_bytes = uploaded_file.getvalue()
                    mime_type = uploaded_file.type
                    answer = ask(st.session_state.sid, prompt, image_bytes=img_bytes, mime_type=mime_type)
                else:
                    answer = ask(st.session_state.sid, prompt)
                
                # Tampilkan jawaban jika sukses
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                # ERROR HANDLING ELEGAN
                error_msg = f"Telah terjadi kendala teknis saat memproses permintaan Anda. (Kode: {str(e)[:50]}...)"
                st.error("⚠️ Sistem sedang sibuk atau koneksi terputus. Mohon coba beberapa saat lagi.")
                
                # Opsi: Munculkan toast (notifikasi popup di pojok)
                st.toast("Gagal menghubungi agen. Cek koneksi Anda.", icon="🚨")
                
                # Jangan simpan error yang panjang ke dalam memori chat history,
                # agar sesi chat tidak rusak jika user ingin bertanya lagi.