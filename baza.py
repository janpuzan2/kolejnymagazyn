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
st.set_page_config(page_title="Magazyn Interaktywny", layout="wide")
st.title("📦 Magazyn z Szybką Edycją")

try:
    # Pobieranie danych
    products = supabase.table("produkty").select("*").order("id").execute()
    categories = supabase.table("kategorie").select("*").execute()
    cat_map = {c['id']: c['nazwa'] for c in categories.data}

    # --- PODSUMOWANIE (METRYKI) ---
    total_qty = sum(p['liczba'] for p in products.data) if products.data else 0
    total_val = sum(p['liczba'] * float(p['cena']) for p in products.data) if products.data else 0.0
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Suma sztuk", f"{total_qty} szt.")
    m2.metric("Wartość", f"{total_val:,.2f} zł")
    # Pasek postępu (zakładamy limit magazynu np. 1000 sztuk)
    limit = 1000
    m3.write(f"Zapełnienie magazynu ({int(total_qty/limit*100)}%)")
    m3.progress(min(total_qty / limit, 1.0))

    st.divider()

    tab1, tab2 = st.tabs(["🛒 Zarządzanie Towarem", "📂 Kategorie"])

    with tab1:
        if products.data:
            # Nagłówki
            cols = st.columns([1, 0.5, 2.5, 1, 1.5, 1])
            header_names = ["ID", "Kolor", "Nazwa", "Cena", "Ilość (Szybka edycja)", "Akcja"]
            for col, h in zip(cols, header_names): col.write(f"**{h}**")
            
            for p in products.data:
                p_color = get_product_color(p['nazwa'])
                c1, c_col, c2, c3, c4, c5 = st.columns([1, 0.5, 2.5, 1, 1.5, 1])
                
                c1.write(f"{p['id']}")
                c_col.markdown(f'<div style="width: 20px; height: 20px; background-color: {p_color}; border-radius: 50%; border: 1px solid #ddd; margin-top: 5px;"></div>', unsafe_allow_html=True)
                c2.write(f"**{p['nazwa']}**")
                c3.write(f"{p['cena']} zł")
                
                # --- SZYBKA EDYCJA ILOŚCI ---
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

                if c5.button("Usuń", key=f"del_{p['id']}"):
                    supabase.table("produkty").delete().eq("id", p['id']).execute()
                    st.toast(f"Usunięto {p['nazwa']}", icon="🗑️")
                    st.rerun()
        else:
            st.info("Pusto tutaj... dodaj coś!")

        st.divider()
        with st.expander("➕ Dodaj nowy produkt"):
            with st.form("new_p", clear_on_submit=True):
                n = st.text_input("Nazwa")
                c = st.number_input("Cena", min_value=0.0)
                l = st.number_input("Ilość", min_value=0)
                cat = st.selectbox("Kategoria", options=list(cat_map.values()) if cat_map else ["Brak"])
                if st.form_submit_button("Dodaj produkt"):
                    if n:
                        c_id = [k for k, v in cat_map.items() if v == cat][0] if cat_map else None
                        supabase.table("produkty").insert({"nazwa": n, "cena": c, "liczba": l, "kategoria_id": c_id}).execute()
                        st.toast("Produkt dodany!", icon="✅")
                        st.rerun()

    with tab2:
        st.header("Kategorie")
        for cid, cname in cat_map.items():
            cc1, cc2 = st.columns([5, 1])
            cc2.button("Usuń", key=f"dc_{cid}", on_click=lambda id=cid: supabase.table("kategorie").delete().eq("id", id).execute())
            cc1.write(f"📁 {cname}")
        
        with st.form("add_cat"):
            nc = st.text_input("Nowa kategoria")
            if st.form_submit_button("Dodaj"):
                if nc:
                    supabase.table("kategorie").insert({"nazwa": nc}).execute()
                    st.rerun()

except Exception as e:
    st.error(f"Coś poszło nie tak: {e}")
