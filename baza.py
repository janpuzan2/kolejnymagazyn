import streamlit as st
from supabase import create_client, Client
import plotly.express as px
import pandas as pd

# --- KONFIGURACJA POŁĄCZENIA ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(URL, KEY)

# --- FUNKCJA DYNAMICZNYCH KOLORÓW ---
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

st.set_page_config(page_title="Magazyn Pro", layout="wide")
st.title("🚀 Inteligentny Magazyn")

try:
    # --- POBIERANIE DANYCH ---
    products_res = supabase.table("produkty").select("*").order("id").execute()
    categories_res = supabase.table("kategorie").select("*").execute()
    
    df = pd.DataFrame(products_res.data) if products_res.data else pd.DataFrame()
    cat_map = {c['id']: c['nazwa'] for c in categories_res.data}

    # --- NAGŁÓWEK: STATYSTYKI ---
    if not df.empty:
        total_items = df['liczba'].sum()
        total_value = (df['liczba'] * df['cena'].astype(float)).sum()
        low_stock_count = df[df['liczba'] < 5].shape[0]

        c_stat1, c_stat2, c_stat3 = st.columns(3)
        c_stat1.metric("Suma towarów", f"{total_items} szt.")
        c_stat2.metric("Wartość magazynu", f"{total_value:,.2f} zł")
        c_stat3.metric("Niski stan (<5 szt.)", f"{low_stock_count} poz.", delta_color="inverse")
    
    st.divider()

    # --- PANEL BOCZNY: FILTRY ---
    st.sidebar.header("🔍 Szukaj i Filtruj")
    search_query = st.sidebar.text_input("Szukaj produktu...", "").lower()
    
    # --- WYKRES W PANELU BOCZNYM ---
    if not df.empty:
        df['kategoria_nazwa'] = df['kategoria_id'].map(cat_map)
        fig = px.pie(df, names='kategoria_nazwa', values='liczba', title="Rozkład kategorii", hole=0.4)
        fig.update_layout(showlegend=False, height=250, margin=dict(t=30, b=0, l=0, r=0))
        st.sidebar.plotly_chart(fig, use_container_width=True)

    tab1, tab2 = st.tabs(["🛒 Lista Towarów", "📂 Kategorie"])

    with tab1:
        # Filtrowanie danych na żywo
        filtered_df = df[df['nazwa'].str.lower().contains(search_query)] if not df.empty else df

        if not filtered_df.empty:
            cols = st.columns([1, 0.5, 3, 1, 1, 1])
            for col, name in zip(cols, ["ID", "Kolor", "Nazwa", "Cena", "Ilość", "Akcja"]):
                col.write(f"**{name}**")
            
            for _, p in filtered_df.iterrows():
                p_color = get_product_color(p['nazwa'])
                is_low = p['liczba'] < 5
                
                c1, c_col, c2, c3, c4, c5 = st.columns([1, 0.5, 3, 1, 1, 1])
                c1.write(f"{p['id']}")
                c_col.markdown(f'<div style="width: 20px; height: 20px; background-color: {p_color}; border-radius: 50%; border: 1px solid #ddd; margin-top: 5px;"></div>', unsafe_allow_html=True)
                
                # Wyróżnienie nazwy jeśli mało towaru
                label = f"{p['nazwa']} ⚠️" if is_low else p['nazwa']
                c2.write(f"**{label}**")
                
                c3.write(f"{p['cena']} zł")
                c4.write(f"{p['liczba']} szt.")
                
                if c5.button("🗑️", key=f"del_{p['id']}"):
                    supabase.table("produkty").delete().eq("id", p['id']).execute()
                    st.rerun()
        else:
            st.warning("Nie znaleziono produktów spełniających kryteria.")

        # FORMULARZ DODAWANIA
        with st.expander("➕ Dodaj nowy przedmiot do bazy"):
            with st.form("add_p", clear_on_submit=True):
                ca, cb = st.columns(2)
                n = ca.text_input("Nazwa")
                p = ca.number_input("Cena", min_value=0.0)
                l = cb.number_input("Ilość", min_value=0)
                cat = cb.selectbox("Kategoria", options=list(cat_map.values()))
                if st.form_submit_button("Dodaj do magazynu"):
                    new_id = [k for k, v in cat_map.items() if v == cat][0]
                    supabase.table("produkty").insert({"nazwa": n, "cena": p, "liczba": l, "kategoria_id": new_id}).execute()
                    st.rerun()

    with tab2:
        st.header("Zarządzanie kategoriami")
        # Wyświetlanie kategorii i prosty formularz (jak wcześniej)
        for cid, cname in cat_map.items():
            cc1, cc2 = st.columns([5, 1])
            cc1.write(f"📁 {cname}")
            if cc2.button("Usuń", key=f"dc_{cid}"):
                supabase.table("kategorie").delete().eq("id", cid).execute()
                st.rerun()
        
        with st.form("new_cat"):
            nc = st.text_input("Nowa kategoria")
            if st.form_submit_button("Stwórz"):
                supabase.table("kategorie").insert({"nazwa": nc}).execute()
                st.rerun()

except Exception as e:
    st.error(f"Błąd: {e}")
