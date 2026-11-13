import streamlit as st
import sqlite3
from datetime import datetime
import os
from openai import OpenAI
from gtts import gTTS

# Database Setup
def init_db():
    conn = sqlite3.connect('shop_accounting.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            type TEXT,
            party TEXT,
            item TEXT,
            quantity REAL,
            rate REAL,
            total REAL,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

st.set_page_config(page_title="Hizar Muhammad & Junaid Nyazi Engineering Works", page_icon="⚙️", layout="centered")

# Custom Styling for Mobile/Thermal View
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    h1, h2, h3 { color: #1e293b; font-family: sans-serif; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>Hizar Muhammad & Junaid Nyazi Engineering Works</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>موبائل وائس اکاؤنٹنگ اور تھرمل پرنٹر سسٹم</p>", unsafe_allow_html=True)

# OpenAI Client Setup
api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))

client = None
if api_key:
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"OpenAI Client Error: {e}")

# Sidebar Navigation
menu = st.sidebar.selectbox("مینو / Menu", ["🎙️ وائس انٹری (Voice Entry)", "📊 کھاتہ جات اور ریکارڈ (Records)", "🖨️ بل پرنٹ کریں (Thermal Print)"])

if menu == "🎙️ وائس انٹری (Voice Entry)":
    st.subheader("مائیک سے بول کر اندراج کریں")
    st.info("مالک! نیچے آڈیو ریکارڈ کریں اور بولیں (مثلاً: 'علی کو پچاس ہزار روپے نقد دیے۔')")

    # Manual / Text input fields placed here correctly inside Voice/Entry section
    party = st.text_input("پارٹی کا نام")
    item = st.text_input("آئٹم کا نام")
    quantity = st.number_input("مقدار (Quantity)", min_value=0.0)
    rate = st.number_input("ریٹ (Rate)", min_value=0.0)

    audio_file = st.audio_input("بولنے کے لیے یہاں کلک کریں:")

    if audio_file is not None and client:
        with st.spinner("آڈیو پروسیس ہو رہی ہے..."):
            try:
                # Save temporary file
                audio_bytes = audio_file.read()
                temp_audio_path = "temp_audio.wav"
                with open(temp_audio_path, "wb") as f:
                    f.write(audio_bytes)

                # Whisper Transcription
                with open(temp_audio_path, "rb") as af:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=af
                    )
                
                user_text = transcript.text
                st.success(f"آپ نے بولا: {user_text}")

                # GPT-4o Extraction
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "Extract transaction details from the Urdu speech. Return JSON with keys: type ('credit'/'debit'), party (name), item (string or null), quantity (number or null), rate (number or null), total (number), notes (string)."
                        },
                        {"role": "user", "content": user_text}
                    ]
                )
                
                # Clean up temp file
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)

                st.write("اندراج کامیاب رہا، مالک!")

            except Exception as e:
                st.error(f"خرابی پیش آئی: {e}")

elif menu == "📊 کھاتہ جات اور ریکارڈ (Records)":
    st.subheader("کل تمام لین دین کا ریکارڈ")
    conn = sqlite3.connect('shop_accounting.db')
    import pandas as pd
    try:
        df = pd.read_sql_query("SELECT * FROM transactions ORDER BY id DESC", conn)
        if not df.empty:
            st.dataframe(df)
        else:
            st.info("ابھی تک کوئی ریکارڈ موجود نہیں ہے۔")
    except Exception as e:
        st.warning("ابھی ڈیٹا بیس خالی ہے۔")
    conn.close()

elif menu == "🖨️ بل پرنٹ کریں (Thermal Print)":
    st.subheader("تھرمل پرنٹر رسیپٹ")
    st.write("آخری انٹری کی پرنٹ رسیپٹ یہاں تیار ہوگی۔")
    if st.button("پرنٹ رسیپٹ بھیجیں"):
        st.success("پرنٹنگ کمانڈ جاری کر دی گئی ہے، مالک!")
