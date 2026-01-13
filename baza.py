import streamlit as st
from supabase import create_client, Client

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

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Magazyn Pro", layout="wide")
st.title("📦 System Magazynowy")

try:
    # Pobieranie danych
    products = supabase.table("produkty").select("*").order("id").execute().data
    categories = supabase.table("kategorie").select("*").execute().data
    cat_map = {c['id']: c['nazwa'] for c in categories}

    # --- STATYSTYKI I PASEK ZAPEŁNIENIA ---
    total_qty = sum(p['liczba'] for p in products) if products else 0
    total_val = sum(p['liczba'] * float(p['cena']) for p in products) if products else 0.0
    
    col_m1, col_m2, col_m3 = st.columns([1, 1, 2])
    col_m1.metric("Suma produktów", f"{total_qty} szt.")
    col_m2.metric("Wartość towaru", f"{total_val:,.2f} zł")
    
    # Pasek zapełnienia (limit 1000 sztuk)
    limit = 1000
    percent = min(int(total_qty / limit * 100), 100)
    col_m3.write(f"Zapełnienie magazynu: {percent}%")
    col_m3.progress(total_qty / limit if total_qty < limit else 1.0)

    st.divider()

    # --- WYSZUKIWARKA ---
    search = st.text_input("🔍 Szybkie szukanie produktu...", "").lower()

    tab1, tab2 = st.tabs(["🛒 Lista Towarów", "📂 Kategorie"])

    with tab1:
        # Filtrowanie listy
        filtered = [p for p in products if search in p['nazwa'].lower()]

        if filtered:
            # Nagłówki tabeli (ID, Kolor, Nazwa, Cena, Szybka Edycja, Status, Akcja)
            cols = st.columns([0.8, 0.5, 2, 1, 1.8, 1, 0.8])
            header_names = ["ID", "Kolor", "Nazwa", "Cena", "Szybka edycja", "Status", "Akcja"]
            for col, h in zip(cols, header_names): col.write(f"**{h}**")
            
            for p in filtered:
                p_color = get_product_color(p['nazwa'])
                c1, c_col, c2, c3, c4, c_status, c5 = st.columns([0.8, 0.5, 2, 1, 1.8, 1, 0.8])
                
                c1.write(f"{p['id']}")
                c_col.markdown(f'<div style="width: 20px; height: 20px; background-color: {p_color}; border-radius: 50%; border: 1px solid #ddd; margin-top: 5px;"></div>', unsafe_allow_html=True)
                c2.write(f"**{p['nazwa']}**")
                c3.write(f"{p['cena']} zł")
                
                # --- SZYBKA EDYCJA ILOŚCI (PLUSY I MINUSY) ---
                with c4:
                    q1, q_val, q2 = st.columns([1, 1, 1])
                    if q1.button("➖", key=f"min_{p['id']}"):
                        new_qty = max(0, p['liczba'] - 1)
                        supabase.table("produkty").update({"liczba": new_qty}).eq("id", p['id']).execute()
                        st.rerun()
                    q_val.write(f"{p['liczba']}")
                    if q2.button("➕", key=f"pls_{p['id']}"):
                        new_qty = p['liczba'] + 1
                        supabase.table("produkty").update({"liczba": new_qty}).eq("id", p['id']).execute()
                        st.rerun()
                
                # Statusy kolorowe
                if p['liczba'] == 0:
                    c_status.error("Brak")
                elif p['liczba'] < 5:
                    c_status.warning("Mało")
                else:
                    c_status.success("OK")

                if c5.button("🗑️", key=f"del_{p['id']}"):
                    supabase.table("produkty").delete().eq("id", p['id']).execute()
                    st.rerun()
        else:
            st.info("Nie znaleziono produktów.")

        # --- DODAWANIE PRODUKTU (EXPANDER) ---
        st.divider()
        with st.expander("➕ DODAJ NOWY PRODUKT"):
            with st.form("add_form", clear_on_submit=True):
                f1, f2 = st.columns(2)
                name = f1.text_input("Nazwa produktu")
                price = f1.number_input("Cena za sztukę", min_value=0.0, step=0.01)
                qty = f2.number_input("Ilość na start", min_value=0, step=1)
                cat = f2.selectbox("Kategoria", options=list(cat_map.values()) if cat_map else ["Brak"])
                
                if st.form_submit_button("Zapisz w magazynie"):
                    if name:
                        c_id = [k for k, v in cat_map.items() if v == cat][0] if cat_map else None
                        supabase.table("produkty").insert({
                            "nazwa": name, "cena": price, "liczba": qty, "kategoria_id": c_id
                        }).execute()
                        st.success("Dodano!")
                        st.rerun()
                    else:
                        st.error("Nazwa jest wymagana!")

    with tab2:
        st.header("Zarządzanie kategoriami")
        for cid, cname in cat_map.items():
            cc1, cc2 = st.columns([5, 1])
            cc1.write(f"📁 {cname}")
            if cc2.button("Usuń", key=f"dc_{cid}"):
                supabase.table("kategorie").delete().eq("id", cid).execute()
                st.rerun()
        
        with st.form("new_cat"):
            nc = st.text_input("Nazwa nowej kategorii")
            if st.form_submit_button("Dodaj"):
                if nc:
                    supabase.table("kategorie").insert({"nazwa": nc}).execute()
                    st.rerun()

except Exception as e:
    st.error(f"Wystąpił błąd: {e}")
