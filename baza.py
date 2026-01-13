import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
# Dane pobierane z Streamlit Secrets (Ustawienia na Streamlit Cloud)
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(URL, KEY)

# --- FUNKCJA KOLORÓW ---
def get_product_color(nazwa):
    """Przypisuje kolor HEX na podstawie słów kluczowych w nazwie."""
    nazwa = nazwa.lower()
    skojarzenia = {
        "mleko": "#FFFFFF",      # Biały
        "jajko": "#F4D03F",      # Żółty
        "pióro": "#5D6D7E",      # Szary/Stalowy
        "kopyto": "#5D4037",     # Brązowy
        "chleb": "#EDBB99",      # Jasny brąz
        "pomidor": "#E74C3C",    # Czerwony
        "ogórek": "#27AE60",     # Zielony
        "woda": "#3498DB",       # Niebieski
        "ser": "#F1C40F"         # Serowy żółty
    }
    
    for klucz, kolor in skojarzenia.items():
        if klucz in nazwa:
            return kolor
    return "#BDC3C7"  # Domyślny szary

# --- INTERFEJS UŻYTKOWNIKA ---
st.set_page_config(page_title="Magazyn Supabase", layout="wide")
st.title("📦 System Zarządzania Magazynem")

tab1, tab2 = st.tabs(["🛒 Produkty", "📂 Kategorie"])

# --- TABELA PRODUKTY ---
with tab1:
    st.header("Lista produktów")
    
    # Pobieranie danych z bazy
    try:
        products = supabase.table("produkty").select("*").order("id").execute()
        categories = supabase.table("kategorie").select("*").execute()
        cat_map = {c['id']: c['nazwa'] for c in categories.data}

        if products.data:
            # Nagłówki tabeli
            h1, h2, h3, h4, h5, h6 = st.columns([1, 0.5, 3, 1, 1, 1])
            h1.write("**ID**")
            h2.write("**Kolor**")
            h3.write("**Nazwa**")
            h4.write("**Cena**")
            h5.write("**Ilość**")
            h6.write("**Akcja**")
            st.divider()

            for p in products.data:
                p_color = get_product_color(p['nazwa'])
                col1, col_color, col2, col3, col4, col5 = st.columns([1, 0.5, 3, 1, 1, 1])
                
                col1.write(f"{p['id']}")
                
                # Wizualizacja koloru (kółko HTML)
                col_color.markdown(
                    f'<div style="width: 20px; height: 20px; background-color: {p_color}; border-radius: 50%; border: 1px solid #ddd; margin-top: 5px;"></div>', 
                    unsafe_allow_html=True
                )
                
                col2.write(f"**{p['nazwa']}**")
                col3.write(f"{p['cena']} zł")
                col4.write(f"{p['liczba']} szt.")
                
                if col5.button("Usuń", key=f"del_p_{p['id']}"):
                    supabase.table("produkty").delete().eq("id", p['id']).execute()
                    st.rerun()
        else:
            st.info("Baza produktów jest pusta.")
    except Exception as e:
        st.error(f"Błąd podczas pobierania produktów: {e}")

    st.divider()
    st.subheader("➕ Dodaj nowy produkt")
    with st.form("form_add_product"):
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
                new_data = {
                    "nazwa": p_name,
                    "liczba": p_count,
                    "cena": p_price,
                    "kategoria_id": cat_options[p_cat_name] if p_cat_name else None
                }
                try:
                    supabase.table("produkty").insert(new_data).execute()
                    st.success(f"Dodano: {p_name}")
                    st.rerun()
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
                c1, c2, c3 = st.columns([1, 4, 1])
                c1.write(f"ID: {c['id']}")
                c2.write(f"**{c['nazwa']}**")
                if c3.button("Usuń", key=f"del_c_{c['id']}"):
                    supabase.table("kategorie").delete().eq("id", c['id']).execute()
                    st.rerun()
        else:
            st.info("Brak zdefiniowanych kategorii.")
    except Exception as e:
        st.error(f"Błąd kategorii: {e}")

    st.divider()
    with st.form("form_add_category"):
        new_cat_name = st.text_input("Nazwa nowej kategorii")
        if st.form_submit_button("Dodaj kategorię"):
            if new_cat_name:
                supabase.table("kategorie").insert({"nazwa": new_cat_name}).execute()
                st.rerun()
