import streamlit as st
from supabase import create_client, Client
from streamlit_confetti import confetti

# --- KONFIGURACJA POŁĄCZENIA ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(URL, KEY)

# --- FUNKCJA KOLORÓW ---
def get_product_color(nazwa):
    nazwa = nazwa.lower()
    skojarzenia = {
        "mleko": "#FFFFFF", "jajko": "#F4D03F", "pióro": "#5D6D7E",
        "kopyto": "#5D4037", "chleb": "#EDBB99", "pomidor": "#E74C3C",
        "ogórek": "#27AE60", "woda": "#3498DB", "ser": "#F1C40F"
    }
    for klucz, kolor in skojarzenia.items():
        if klucz in nazwa: return kolor
    return "#BDC3C7"

# --- INTERFEJS UŻYTKOWNIKA ---
st.set_page_config(page_title="Magazyn z Fajerwerkami", layout="wide")
st.title("📦 System Zarządzania Magazynem")

tab1, tab2 = st.tabs(["🛒 Produkty", "📂 Kategorie"])

# --- TABELA PRODUKTY ---
with tab1:
    st.header("Lista produktów")
    try:
        products = supabase.table("produkty").select("*").order("id").execute()
        categories = supabase.table("kategorie").select("*").execute()
        cat_map = {c['id']: c['nazwa'] for c in categories.data}

        if products.data:
            cols = st.columns([1, 0.5, 3, 1, 1, 1])
            fields = ["ID", "Kolor", "Nazwa", "Cena", "Ilość", "Akcja"]
            for col, field in zip(cols, fields): col.write(f"**{field}**")
            st.divider()

            for p in products.data:
                p_color = get_product_color(p['nazwa'])
                c1, c_col, c2, c3, c4, c5 = st.columns([1, 0.5, 3, 1, 1, 1])
                c1.write(f"{p['id']}")
                c_col.markdown(f'<div style="width: 20px; height: 20px; background-color: {p_color}; border-radius: 50%; border: 1px solid #ddd; margin-top: 5px;"></div>', unsafe_allow_html=True)
                c2.write(f"**{p['nazwa']}**")
                c3.write(f"{p['cena']} zł")
                c4.write(f"{p['liczba']} szt.")
                if c5.button("Usuń", key=f"del_p_{p['id']}"):
                    supabase.table("produkty").delete().eq("id", p['id']).execute()
                    st.rerun()
        else:
            st.info("Baza produktów jest pusta.")
    except Exception as e:
        st.error(f"Błąd: {e}")

    st.divider()
    st.subheader("➕ Dodaj nowy produkt")
    with st.form("form_add_product", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            p_name = st.text_input("Nazwa produktu")
            p_price = st.number_input("Cena (zł)", min_value=0.0, step=0.01)
        with col_b:
            p_count = st.number_input("Ilość (szt)", min_value=0, step=1)
            cat_options = {c['nazwa']: c['id'] for c in categories.data}
            p_cat_name = st.selectbox("Wybierz kategorię", options=list(cat_options.keys()))

        if st.form_submit_button("Zapisz produkt w bazie"):
            if p_name:
                new_data = {"nazwa": p_name, "liczba": p_count, "cena": p_price, "kategoria_id": cat_options[p_cat_name] if p_cat_name else None}
                try:
                    supabase.table("produkty").insert(new_data).execute()
                    # --- TUTAJ LECĄ FAJERWERKI ---
                    confetti() 
                    st.success(f"Dodano: {p_name}!")
                    # Nie robimy st.rerun() od razu, żeby było widać animację
                except Exception as e:
                    st.error(f"Błąd zapisu: {e}")
            else:
                st.warning("Podaj nazwę produktu!")

# --- TABELA KATEGORIE ---
with tab2:
    st.header("Zarządzanie kategoriami")
    try:
        if categories.data:
            for c in categories.data:
                ca1, ca2, ca3 = st.columns([1, 4, 1])
                ca1.write(f"ID: {c['id']}")
                ca2.write(f"**{c['nazwa']}**")
                if ca3.button("Usuń", key=f"del_c_{c['id']}"):
                    supabase.table("kategorie").delete().eq("id", c['id']).execute()
                    st.rerun()
        
        st.divider()
        with st.form("form_add_category"):
            new_cat_name = st.text_input("Nazwa nowej kategorii")
            if st.form_submit_button("Dodaj kategorię"):
                if new_cat_name:
                    supabase.table("kategorie").insert({"nazwa": new_cat_name}).execute()
                    st.rerun()
    except Exception as e:
        st.error(f"Błąd: {e}")
