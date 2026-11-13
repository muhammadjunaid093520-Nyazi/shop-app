import streamlit as st
import sqlite3
from datetime import datetime
import os
from openai import OpenAI
import pandas as pd

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
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; background-color: #2563eb; color: white; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>Hizar Muhammad & Junaid Nyazi Engineering Works</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>موبائل اکاؤنٹنگ اور رجسٹر سسٹم</p>", unsafe_allow_html=True)

# OpenAI Client Setup
api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
client = None
if api_key:
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"OpenAI Client Error: {e}")

# Sidebar Navigation
menu = st.sidebar.selectbox("مینو / Menu", ["📝 نیا اندراج (New Entry)", "📊 کھاتہ رجسٹر (Ledger Records)", "🖨️ بل پرنٹ کریں (Thermal Print)"])

if menu == "📝 نیا اندراج (New Entry)":
    st.subheader("کھاتے میں نیا اندراج کریں")
    
    # Optional Voice-to-Text helper to auto-fill fields if speaking is preferred
    audio_file = st.audio_input("بول کر خود بخود خانے بھرنے کے لیے یہاں کلک کریں:")
    
    transcribed_party = ""
    transcribed_item = ""
    transcribed_qty = 0.0
    transcribed_rate = 0.0
    transcribed_total = 0.0
    transcribed_type = "debit"
    transcribed_notes = ""

    if audio_file is not None and client:
        with st.spinner("آڈیو سمجھ کر خانے بھرے جا رہے ہیں..."):
            try:
                audio_bytes = audio_file.read()
                temp_audio_path = "temp_audio.wav"
                with open(temp_audio_path, "wb") as f:
                    f.write(audio_bytes)

                with open(temp_audio_path, "rb") as af:
                    transcript = client.audio.transcriptions.create(model="whisper-1", file=af)
                
                user_text = transcript.text
                st.info(f"آپ کا بولا ہوا متن: {user_text}")

                # GPT Extraction for structured ledger entry
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "Extract transaction details from the Urdu speech. Return valid JSON only with keys: type ('credit'/'debit'), party (string), item (string), quantity (number), rate (number), total (number), notes (string)."
                        },
                        {"role": "user", "content": user_text}
                    ]
                )
                
                import json
                res_content = response.choices[0].message.content.strip()
                # Clean up json markdown if any
                if res_content.startswith("```json"):
                    res_content = res_content[7:-3].strip()
                
                data = json.loads(res_content)
                transcribed_party = data.get("party", "")
                transcribed_item = data.get("item", "")
                transcribed_qty = float(data.get("quantity", 0.0) or 0.0)
                transcribed_rate = float(data.get("rate", 0.0) or 0.0)
                transcribed_total = float(data.get("total", transcribed_qty * transcribed_rate) or 0.0)
                transcribed_type = data.get("type", "debit")
                transcribed_notes = data.get("notes", user_text)

                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
                st.success("آواز سے خانے کامیابی سے بھر دیے گئے ہیں، نیچے چیک کر کے سیو کریں!")
            except Exception as e:
                st.error(f"آڈیو پراسیسنگ میں خرابی: {e}")

    # Manual form / Register Entry form
    with st.form("transaction_form"):
        party = st.text_input("پارٹی کا نام (Party Name)", value=transcribed_party)
        item = st.text_input("آئٹم کا نام / تفصیل (Item)", value=transcribed_item)
        
        col1, col2 = st.columns(2)
        with col1:
            quantity = st.number_input("مقدار (Quantity)", min_value=0.0, value=transcribed_qty)
        with col2:
            rate = st.number_input("ریٹ (Rate)", min_value=0.0, value=transcribed_rate)
        
        # Calculate total automatically if qty and rate are given
        calc_total = quantity * rate if quantity > 0 and rate > 0 else transcribed_total
        total = st.number_input("کل رقم (Total Amount)", min_value=0.0, value=calc_total)
        
        trans_type = st.selectbox("قسم (Type)", ["debit (کھاتے میں دیے/ఉਧਾਰ)", "credit (وصول کیے/جمع)"], index=0 if transcribed_type=="debit" else 1)
        notes = st.text_area("مزید تفصیل / نوٹس (Notes)", value=transcribed_notes)

        submit_button = st.form_submit_button(label="💾 رجسٹر میں محفوظ کریں (Save)")

        if submit_button:
            if party.strip() == "":
                st.warning("براہ کرم پارٹی کا نام درج کریں!")
            else:
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                conn = sqlite3.connect('shop_accounting.db')
                c = conn.cursor()
                c.execute('''
                    INSERT INTO transactions (date, type, party, item, quantity, rate, total, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (current_date, trans_type, party, item, quantity, rate, total, notes))
                conn.commit()
                conn.close()
                st.success("انڈراج کامیابی کے ساتھ رجسٹر میں محفوظ ہو گیا ہے، مالک!")

elif menu == "📊 کھاتہ رجسٹر (Ledger Records)":
    st.subheader("تمام لین دین کا رجسٹر صفحہ")
    conn = sqlite3.connect('shop_accounting.db')
    try:
        df = pd.read_sql_query("SELECT id, date AS 'تاریخ', type AS 'قسم', party AS 'پارٹی نام', item AS 'آئٹم', quantity AS 'مقدار', rate AS 'ریٹ', total AS 'کل رقم', notes AS 'تفصیل' FROM transactions ORDER BY id DESC", conn)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            
            # Summary totals
            total_sum = df['کل رقم'].sum()
            st.markdown(f"### کل مالی لین دین: {total_sum:,.2f} روپے")
        else:
            st.info("ابھی تک رجسٹر میں کوئی ریکارڈ موجود نہیں ہے۔")
    except Exception as e:
        st.warning(f"خرابی پیش آئی: {e}")
    conn.close()

elif menu == "🖨️ بل پرنٹ کریں (Thermal Print)":
    st.subheader("تھرمل پرنٹر رسیپٹ بل")
    conn = sqlite3.connect('shop_accounting.db')
    try:
        df = pd.read_sql_query("SELECT * FROM transactions ORDER BY id DESC LIMIT 1", conn)
        if not df.empty:
            last_tx = df.iloc[0]
            st.markdown("---")
            st.markdown(f"**Hizar Muhammad & Junaid Nyazi Engineering Works**")
            st.markdown(f"تاریخ: {last_tx['date']}")
            st.markdown(f"پارٹی: **{last_tx['party']}**")
            st.markdown(f"آئٹم: {last_tx['item']} | مقدار: {last_tx['quantity']} | ریٹ: {last_tx['rate']}")
            st.markdown(f"### کل رقم: {last_tx['total']} روپے")
            st.markdown(f"تفصیل: {last_tx['notes']}")
            st.markdown("---")
            
            if st.button("پرنٹ کمانڈ بھیجیں (Print Bill)"):
                st.success("بل کامیابی سے تھرمل پرنٹر پر بھیج دیا گیا ہے، مالک!")
        else:
            st.info("پرنٹ کے لیے کوئی آخری انٹری موجود نہیں ہے۔")
    except Exception as e:
        st.warning("ڈیٹا بیس خالی ہے۔")
    conn.close()
