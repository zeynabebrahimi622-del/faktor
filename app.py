import streamlit as st
import pandas as pd
import re

# ==========================================
# ۱. تنظیمات و دیتابیس کاربران (بسیار ساده برای شروع)
# در دنیای واقعی این‌ها در یک فایل جدا یا دیتابیس هستند
# ==========================================
USER_DATA = {
    "customer1": {"password": "123", "expiry": "2025-12-31"},
    "customer2": {"password": "456", "expiry": "2025-06-01"},
    "admin": {"password": "admin_password", "expiry": "2030-01-01"}
}

# ==========================================
# ۲. توابع کمکی (Logic)
# ==========================================
def parse_input_line(line):
    """تبدیل خط متنی به داده‌های ساختاریافته"""
    try:
        # مثال ورودی: محصول - قیمت - تعداد
        parts = line.split('-')
        if len(parts) == 3:
            return {
                "product": parts[0].strip(),
                "price": float(parts[1].strip()),
                "quantity": int(parts[2].strip())
            }
    except Exception:
        return None
    return None

# ==========================================
# ۳. بخش مدیریت امنیت (Login System)
# ==========================================
def login_screen():
    st.title("🔐 ورود به سیستم فاکتورساز")
    st.info("لطفاً نام کاربری و رمز عبور خود را وارد کنید.")
    
    with st.form("login_form"):
        username = st.text_input("نام کاربری")
        password = st.text_input("رمز عبور", type="password")
        submit = st.form_submit_button("ورود")

        if submit:
            if username in USER_DATA and USER_DATA[username]["password"] == password:
                # چک کردن تاریخ انقضا
                # (در اینجا فقط چک می‌کنیم که کاربر وجود دارد)
                st.session_state['authenticated'] = True
                st.session_state['user'] = username
                st.success("با موفقیت وارد شدید!")
                st.rerun()
            else:
                st.error("نام کاربری یا رمز عبور اشتباه است.")

# ==========================================
# ۴. بدنه اصلی برنامه (Main App)
# ==========================================
def main_app():
    user = st.session_state['user']
    st.sidebar.title(f"👤 کاربر: {user}")
    if st.sidebar.button("خروج"):
        st.session_state['authenticated'] = False
        st.rerun()

    st.title("🧾 سیستم صدور فاکتور هوشمند")
    
    # بخش آپلود فایل
    uploaded_file = st.file_uploader("لیست محصولات اکسل را انتخاب کنید", type=['xlsx', 'csv'])
    
    # بخش ورودی متن
    text_input = st.text_area("فاکتور را وارد کنید (فرمت: محصول - قیمت - تعداد)", height=200)

    if st.button("✨ تولید فاکتور"):
        if not text_input:
            st.warning("لطفاً متن فاکتور را وارد کنید.")
        else:
            st.subheader("📄 پیش‌نمایش فاکتور")
            lines = text_input.strip().split('\n')
            data = []
            
            for line in lines:
                parsed = parse_input_line(line)
                if parsed:
                    data.append(parsed)
            
            if data:
                df = pd.DataFrame(data)
                # محاسبه جمع کل
                df['جمع'] = df['price'] * df['quantity']
                st.table(df)
                st.write(f"**جمع کل قابل پرداخت: {df['جمع'].sum():,.0f} ریال**")
            else:
                st.error("فرمت ورودی اشتباه است. لطفاً از فرمت 'محصول - قیمت - تعداد' استفاده کنید.")

# ==========================================
# ۵. کنترل جریان برنامه (Router)
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if st.session_state['authenticated']:
    main_app()
else:
    login_screen()
