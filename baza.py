import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia z Supabase
# Na GitHubie/Streamlit Cloud użyj st.secrets dla bezpieczeństwa!
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(URL, KEY)

st.title("📦 Zarządzanie Produktami i Kategoriami")

# --- ZAKŁADKI ---
tab1, tab2 = st.tabs(["Produkty", "Kategorie"])

# --- TABELA PRODUKTY ---
with tab1:
    st.header("Lista produktów")
    
    # Pobieranie danych
    products = supabase.table("produkty").select("*").execute()
    categories = supabase.table("kategorie").select("*").execute()
    
    # Słownik do mapowania nazw kategorii
    cat_map = {c['id']: c['nazwa'] for c in categories.data}
    
    if products.data:
        for p in products.data:
            col1, col2, col3, col4, col5 = st.columns([1, 3, 1, 1, 1])
            col1.write(f"ID: {p['id']}")
            col2.write(f"**{p['nazwa']}**")
            col3.write(f"{p['cena']} zł")
            col4.write(f"Sztuk: {p['liczba']}")
            if col5.button("Usuń", key=f"del_prod_{p['id']}"):
                supabase.table("produkty").delete().eq("id", p['id']).execute()
                st.rerun()
    else:
        st.info("Brak produktów w bazie.")

    st.divider()
    st.subheader("Dodaj nowy produkt")
    with st.form("add_product"):
        p_name = st.text_input("Nazwa produktu")
        p_count = st.number_input("Liczba", min_value=0, step=1)
        p_price = st.number_input("Cena", min_value=0.0, step=0.01)
        
        # Wybór kategorii (FK)
        cat_options = {c['nazwa']: c['id'] for c in categories.data}
        p_cat_name = st.selectbox("Kategoria", options=list(cat_options.keys()))
        
        if st.form_submit_button("Dodaj produkt"):
            new_prod = {
                "nazwa": p_name,
                "liczba": p_count,
                "cena": p_price,
                "kategoria_id": cat_options[p_cat_name] if p_cat_name else None
            }
            supabase.table("produkty").insert(new_prod).execute()
            st.success("Dodano produkt!")
            st.rerun()

# --- TABELA KATEGORIE ---
with tab2:
    st.header("Kategorie")
    
    if categories.data:
        for c in categories.data:
            col1, col2, col3 = st.columns([1, 4, 1])
            col1.write(f"ID: {c['id']}")
            col2.write(c['nazwa'])
            if col3.button("Usuń", key=f"del_cat_{c['id']}"):
                supabase.table("kategorie").delete().eq("id", c['id']).execute()
                st.rerun()
    
    st.divider()
    st.subheader("Dodaj nową kategorię")
    with st.form("add_category"):
        c_name = st.text_input("Nazwa kategorii")
        if st.form_submit_button("Dodaj kategorię"):
            supabase.table("kategorie").insert({"nazwa": c_name}).execute()
            st.success("Dodano kategorię!")
            st.rerun()
