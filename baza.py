import streamlit as st
from supabase import create_client, Client

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

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Magazyn Pro Plus", layout="wide")
st.title("📦 Twój Inteligentny Magazyn")

try:
    # Pobieranie danych
    products_data = supabase.table("produkty").select("*").order("id").execute().data
    categories_data = supabase.table("kategorie").select("*").execute().data
    cat_map = {c['id']: c['nazwa'] for c in categories_data}

    # --- WYSZUKIWARKA ---
    search = st.text_input("🔍 Szukaj produktu po nazwie...", "").lower()

    # --- TABELE ---
    tab1, tab2 = st.tabs(["🛒 Asortyment", "📂 Kategorie"])

    with tab1:
        if products_data:
            # Filtrowanie na poziomie kodu Pythona
            filtered_products = [p for p in products_data if search in p['nazwa'].lower()]

            cols = st.columns([1, 0.5, 2.5, 1, 1, 1, 1])
            for col, h in zip(cols, ["ID", "Kolor", "Nazwa", "Cena", "Ilość", "Status", "Akcja"]):
                col.write(f"**{h}**")
            st.divider()

            for p in filtered_products:
                p_color = get_product_color(p['nazwa'])
                c1, c_col, c2, c3, c4, c_status, c5 = st.columns([1, 0.5, 2.5, 1, 1, 1, 1])
                
                c1.write(f"{p['id']}")
                c_col.markdown(f'<div style="width: 20px; height: 20px; background-color: {p_color}; border-radius: 50%; border: 1px solid #ddd; margin-top: 5px;"></div>', unsafe_allow_html=True)
                c2.write(f"**{p['nazwa']}**")
                c3.write(f"{p['cena']} zł")
                c4.write(f"{p['liczba']} szt.")
                
                # --- PROSTY SYSTEM STATUSÓW ---
                if p['liczba'] == 0:
                    c_status.error("Brak")
                elif p['liczba'] < 5:
                    c_status.warning("Mało")
                else:
                    c_status.success("Dużo")

                if c5.button("Usuń", key=f"del_{p['id']}"):
                    supabase.table("produkty").delete().eq("id", p['id']).execute()
                    st.rerun()
        else:
            st.info("Brak produktów do wyświetlenia.")

    with tab2:
        st.subheader("Lista kategorii")
        for cid, cname in cat_map.items():
            with st.container(border=True):
                cc1, cc2 = st.columns([5, 1])
                cc1.write(f"📁 **{cname}**")
                if cc2.button("Usuń", key=f"dc_{cid}"):
                    supabase.table("kategorie").delete().eq("id", cid).execute()
                    st.rerun()
        
        st.divider()
        with st.form("new_cat"):
            nc = st.text_input("Nazwa nowej kategorii")
            if st.form_submit_button("Dodaj kategorię"):
                if nc:
                    supabase.table("kategorie").insert({"nazwa": nc}).execute()
                    st.rerun()

except Exception as e:
    st.error(f"Błąd: {e}")

# --- FORMULARZ DODAWANIA NA DOLE (Sidebar) ---
with st.sidebar:
    st.header("➕ Nowy Produkt")
    with st.form("add_p", clear_on_submit=True):
        n = st.text_input("Nazwa przedmiotu")
        c = st.number_input("Cena", min_value=0.0)
        l = st.number_input("Ilość", min_value=0)
        cat_name = st.selectbox("Kategoria", options=list(cat_map.values()) if cat_map else ["Brak"])
        if st.form_submit_button("Dodaj do bazy"):
            if n:
                c_id = [k for k, v in cat_map.items() if v == cat_name][0] if cat_map else None
                supabase.table("produkty").insert({"nazwa": n, "cena": c, "liczba": l, "kategoria_id": c_id}).execute()
                st.rerun()
