import streamlit as st
import pandas as pd
import re
from io import BytesIO

# --- ۱. تنظیمات اولیه و ظاهر (UI Configuration) ---
st.set_page_config(page_title="سیستم صدور فاکتور هوشمند", layout="centered")

# استایل برای راست‌چین کردن (RTL)
st.markdown("""
<style>
    .main { direction: rtl; text-align: right; }
    div[data-testid="stMarkdownContainer"] p { text-align: right; }
    .stButton>button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- ۲. توابع کمکی (Helper Functions) ---

def to_persian_digits(number_str):
    """تبدیل اعداد انگلیسی به فارسی برای نمایش بهتر"""
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    latin_digits = "0123456789"
    table = str.maketrans(latin_digits, persian_digits)
    return str(number_str).translate(table)

def find_best_product(input_text, products_df):
    """جستجوی هوشمند محصول در میان لیست محصولات (Partial Match)"""
    # استخراج کلمات از متن کاربر
    words = re.findall(r'[a-zA-Z\u0600-\u06FF]+', input_text)
    best_match = None
    max_score = 0
    
    for _, row in products_df.iterrows():
        product_name = str(row['name']).lower()
        score = 0
        for word in words:
            if word.lower() in product_name:
                score += 1
        if score > max_score:
            max_score = score
            best_match = row
    return best_match

def parse_input_line(line, products_df):
    """تجزیه و تحلیل هر خط وارد شده توسط کاربر"""
    line = line.strip()
    if not line:
        return None
    
    discount_val = 0
    shipping_val = 0
    
    # استخراج تخفیف و هزینه ارسال با استفاده از کلمات کلیدی
    if "تخفیف" in line:
        parts = re.split(r'تخفیف', line)
        line = parts[0]
        try:
            discount_val = float(re.findall(r'\d+', parts[1])[0])
        except: discount_val = 0
        
    if "ارسال" in line:
        parts = re.split(r'ارسال', line)
        line = parts[0]
        try:
            shipping_val = float(re.findall(r'\d+', parts[1])[0])
        except: shipping_val = 0
        
    product_row = find_best_product(line, products_df)
    if product_row is None:
        return {"error": f"محصول در متن یافت نشد."}
    
    # استخراج اعداد (تعداد و قیمت دستی)
    numbers = re.findall(r'\d+', line)
    quantity = 1
    manual_price = None
    
    if len(numbers) >= 2:
        quantity = int(numbers[0])
        manual_price = float(numbers[1])
    elif len(numbers) == 1:
        quantity = int(numbers[0])
        manual_price = float(product_row['price'])
    else:
        quantity = 1
        manual_price = float(product_row['price'])
        
    final_unit_price = manual_price if manual_price is not None else float(product_row['price'])
    total_item_price = (quantity * final_unit_price) - discount_val + shipping_val
    
    return {
        "name": product_row['name'],
        "quantity": quantity,
        "unit_price": final_unit_price,
        "total_price": total_item_price,
        "discount": discount_val,
        "shipping": shipping_val
    }

# --- ۳. مدیریت وضعیت برنامه (Session State) ---
if 'current_invoice' not in st.session_state:
    st.session_state.current_invoice = []
if 'grand_total' not in st.session_state:
    st.session_state.grand_total = 0

# --- ۴. بدنه اصلی برنامه (Main App) ---
st.title("🧾 صدور فاکتور هوشمند")

uploaded_file = st.file_uploader("فایل اکسل محصولات را انتخاب کنید", type=["xlsx"])

if uploaded_file:
    try:
        # خواندن فایل اکسل
        df = pd.read_excel(uploaded_file)
        # پاکسازی نام ستون‌ها (حذف فاصله‌های اضافی)
        df.columns = [str(c).strip() for c in df.columns]
        
        st.success("✅ فایل محصولات با موفقیت بارگذاری شد.")

        user_input_text = st.text_area("لیست محصولات (هر خط یک محصول):", height=150, 
                                     placeholder="مثال:\nریمل حرفه ای 2\nصابون 1 15000")
        
        if st.button("🚀 محاسبه و تولید فاکتور"):
            if user_input_text:
                lines = user_input_text.split('\n')
                temp_invoice_items = []
                errors = []
                total_acc = 0
                
                for line in lines:
                    if line.strip():
                        result = parse_input_line(line, df)
                        if result and "error" not in result:
                            temp_invoice_items.append(result)
                            total_acc += result['total_price']
                        elif result and "error" in result:
                            errors.append(result["error"])
                            
                if errors:
                    for err in errors:
                        st.error(err)
                
                if temp_invoice_items:
                    st.session_state.current_invoice = temp_invoice_items
                    st.session_state.grand_total = total_acc
                else:
                    st.session_state.current_invoice = []
                    st.session_state.grand_total = 0
                    st.warning("هیچ محصول معتبری پیدا نشد.")
            else:
                st.warning("لطفاً متنی وارد کنید.")
        
        # --- نمایش نتایج ---
        if st.session_state.current_invoice:
            st.divider()
            st.subheader("📊 جدول محاسبات")
            display_data = []
            for item in st.session_state.current_invoice:
                display_data.append({
                    "محصول": to_persian_digits(item['name']),
                    "تعداد": f"{to_persian_digits(item['quantity'])} عدد",
                    "قیمت واحد": to_persian_digits(int(item['unit_price'])),
                    "جمع کل ردیف": to_persian_digits(int(item['total_price']))
                })
            st.table(pd.DataFrame(display_data))
            
            st.markdown(f"### 💰 مبلغ نهایی فاکتور: **{to_persian_digits(int(st.session_state.grand_total))} تومان**")
            
            st.divider()
            st.subheader("📋 متن آماده برای ارسال")
            ready_to_copy_text = ""
            for item in st.session_state.current_invoice:
                row_total = item['quantity'] * item['unit_price']
                ready_to_copy_text += f"{to_persian_digits(item['name'])} {to_persian_digits(item['quantity'])} عدد {to_persian_digits(int(row_total))}\n"
            
            ready_to_copy_text += f"\n------------------\n"
            ready_to_copy_text += f"💰 جمع کل نهایی: {to_persian_digits(int(st.session_state.grand_total))} تومان"
            st.code(ready_to_copy_text, language=None)
            
            st.divider()
            st.subheader("📥 دانلود فایل‌ها")
            col1, col2 = st.columns(2)
            with col1:
                # تولید اکسل برای دانلود
                df_to_download = pd.DataFrame(st.session_state.current_invoice)
                df_to_download = df_to_download[['name', 'quantity', 'unit_price', 'total_price']]
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_to_download.to_excel(writer, index=False, sheet_name='Invoice')
                st.download_button("📊 اکسل (جزئیات)", output.getvalue(), "invoice_detailed.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            with col2:
                # تولید متن برای دانلود
                st.download_button("📄 متن (TXT)", ready_to_copy_text.encode('utf-8'), "invoice.txt", "text/plain")

    except Exception as e:
        st.error(f"خطا در پردازش فایل: {e}")
