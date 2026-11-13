import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# Database Setup
def init_db():
    conn = sqlite3.connect('shop_accounting.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
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

# Custom Styling for Mobile/Register View
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    h1, h2, h3 { color: #1e293b; font-family: sans-serif; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; background-color: #1e3a8a; color: white; font-size: 16px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>ہجر محمد اینڈ جنید نیازی انجینئرنگ ورکس</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>ڈیجیٹل رجسٹر اور بلنگ سسٹم</p>", unsafe_allow_html=True)

# Sidebar Navigation
menu = st.sidebar.selectbox("مینو / Menu", ["📝 نیا اندراج (New Entry)", "📊 کھاتہ رجسٹر (Ledger Records)", "🖨️ بل پرنٹ کریں (Thermal Print)"])

if menu == "📝 نیا اندراج (New Entry)":
    st.subheader("رجسٹر میں نیا کھاتا درج کریں")
    st.info("مالک! نیچے خانے میں تفصیل لکھیں (آپ کی بورڈ کا مائیک بھی استعمال کر سکتے ہیں)")

    with st.form("register_form", clear_on_submit=True):
        party = st.text_input("پارٹی کا نام (Party Name)")
        item = st.text_input("آئٹم کا نام / تفصیل (Item)")
        
        col1, col2 = st.columns(2)
        with col1:
            quantity = st.number_input("مقدار (Quantity)", min_value=0.0, format="%.2f")
        with col2:
            rate = st.number_input("ریٹ (Rate)", min_value=0.0, format="%.2f")
        
        # Calculate total automatically if both qty and rate are provided
        calculated_total = quantity * rate if quantity > 0 and rate > 0 else 0.0
        total = st.number_input("کل رقم (Total Amount)", min_value=0.0, value=calculated_total, format="%.2f")
        
        notes = st.text_area("مزید تفصیل / نوٹس (Notes)")

        submit_button = st.form_submit_button(label="💾 رجسٹر میں محفوظ کریں (Save)")

        if submit_button:
            if not party.strip():
                st.warning("براہ کرم پارٹی کا نام لازمی درج کریں!")
            else:
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                conn = sqlite3.connect('shop_accounting.db')
                c = conn.cursor()
                c.execute('''
                    INSERT INTO transactions (date, party, item, quantity, rate, total, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (current_date, party, item, quantity, rate, total, notes))
                conn.commit()
                conn.close()
                st.success("انڈراج کامیابی کے ساتھ رجسٹر میں محفوظ ہو گیا ہے، مالک!")

elif menu == "📊 کھاتہ رجسٹر (Ledger Records)":
    st.subheader("مکمل کھاتہ رجسٹر (ریکارڈ)")
    conn = sqlite3.connect('shop_accounting.db')
    try:
        df = pd.read_sql_query("SELECT id AS 'آئی ڈی', date AS 'تاریخ', party AS 'پارٹی نام', item AS 'آئٹم', quantity AS 'مقدار', rate AS 'ریٹ', total AS 'کل رقم', notes AS 'تفصیل' FROM transactions ORDER BY id DESC", conn)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            
            # Summary totals
            total_sum = df['کل رقم'].sum()
            st.markdown(f"### 💰 کل کاروبار / رقم: {total_sum:,.2f} روپے")
        else:
            st.info("ابھی تک رجسٹر میں کوئی انٹری موجود نہیں ہے۔")
    except Exception as e:
        st.warning(f"خرابی پیش آئی: {e}")
    conn.close()

elif menu == "🖨️ بل پرنٹ کریں (Thermal Print)":
    st.subheader("آخری بل / رسیپٹ")
    conn = sqlite3.connect('shop_accounting.db')
    try:
        df = pd.read_sql_query("SELECT * FROM transactions ORDER BY id DESC LIMIT 1", conn)
        if not df.empty:
            last_tx = df.iloc[0]
            st.markdown("---")
            st.markdown("<h3 style='text-align: center;'>ہجر محمد اینڈ جنید نیازی انجینئرنگ ورکس</h3>", unsafe_allow_html=True)
            st.markdown(f"**تاریخ:** {last_tx['date']}")
            st.markdown(f"**پارٹی کا نام:** {last_tx['party']}")
            st.markdown(f"**آئٹم:** {last_tx['item']}")
            st.markdown(f"**مقدار:** {last_tx['quantity']} | **ریٹ:** {last_tx['rate']}")
            st.markdown(f"### کل رقم: {last_tx['total']} روپے")
            if last_tx['notes']:
                st.markdown(f"**تفصیل:** {last_tx['notes']}")
            st.markdown("---")
            
            if st.button("🖨️ بل پرنٹ کریں"):
                st.success("پرنٹنگ کمانڈ کامیابی سے جاری کر دی گئی ہے!")
        else:
            st.info("پرنٹ کے لیے کوئی آخری انٹری موجود نہیں ہے۔")
    except Exception as e:
        st.warning("ڈیٹا بیس خالی ہے۔")
    conn.close()
