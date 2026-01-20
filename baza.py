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
st.set_page_config(page_title="Magazyn Pro", layout="wide", page_icon="📦")

try:
    # Pobieranie danych
    products = supabase.table("produkty").select("*").order("id").execute().data
    categories = supabase.table("kategorie").select("*").execute().data
    cat_map = {c['id']: c['nazwa'] for c in categories}

    st.title("📦 System Magazynowy")
    
    # --- STATYSTYKI ---
    total_qty = sum(p['liczba'] for p in products) if products else 0
    total_val = sum(p['liczba'] * float(p['cena']) for p in products) if products else 0.0
    
    m1, m2, m3 = st.columns([1,1,1])
    m1.metric("Suma sztuk", f"{total_qty}")
    m2.metric("Wartość towaru", f"{total_val:,.2f} zł")
    m3.write(f"Zapełnienie: {total_qty}/1000")
    m3.progress(min(total_qty / 1000, 1.0))

    st.divider()

    # --- TABS (Dodano zakładkę Analityka) ---
    tab1, tab2, tab3 = st.tabs(["🛒 Inwentarz", "📂 Kategorie", "📊 Analityka"])

    with tab1:
        search = st.text_input("🔍 Szukaj produktu...", "").lower()
        filtered = [p for p in products if search in p['nazwa'].lower()]

        if filtered:
            # Rozkład kolumn
            cols = st.columns([0.5, 0.4, 1.8, 1.2, 0.8, 1.8, 1, 0.5])
            headers = ["ID", "•", "Nazwa", "Kategoria", "Cena", "Zmień Ilość", "Status", ""]
            for col, h in zip(cols, headers): col.write(f"**{h}**")
            
            for p in filtered:
                p_color = get_product_color(p['nazwa'])
                p_cat = cat_map.get(p['kategoria_id'], "Brak")
                
                c1, c_col, c2, c_cat, c3, c4, c_status, c5 = st.columns([0.5, 0.4, 1.8, 1.2, 0.8, 1.8, 1, 0.5])
                
                c1.write(f"`{p['id']}`")
                c_col.markdown(f'<div style="width:15px; height:15px; background:{p_color}; border-radius:50%; margin-top:10px; border:1px solid #ddd"></div>', unsafe_allow_html=True)
                c2.write(f"**{p['nazwa']}**")
                c_cat.markdown(f'<code style="font-size: 0.75rem;">{p_cat}</code>', unsafe_allow_html=True)
                c3.write(f"{p['cena']} zł")
                
                # Szybka edycja ilości (Plus / Minus)
                with c4:
                    q_min, q_val, q_pls = st.columns([1, 1.2, 1])
                    if q_min.button("➖", key=f"btn_min_{p['id']}"):
                        supabase.table("produkty").update({"liczba": max(0, p['liczba'] - 1)}).eq("id", p['id']).execute()
                        st.rerun()
                    
                    q_val.markdown(f"<div style='text-align: center; font-weight: bold; margin-top: 5px;'>{p['liczba']}</div>", unsafe_allow_html=True)
                    
                    if q_pls.button("➕", key=f"btn_pls_{p['id']}"):
                        supabase.table("produkty").update({"liczba": p['liczba'] + 1}).eq("id", p['id']).execute()
                        st.rerun()
                
                if p['liczba'] == 0: c_status.error("Brak")
                elif p['liczba'] < 5: c_status.warning("Mało")
                else: c_status.success("OK")

                if c5.button("🗑️", key=f"btn_del_{p['id']}"):
                    supabase.table("produkty").delete().eq("id", p['id']).execute()
                    st.rerun()

        st.markdown("---")
        with st.expander("➕ Dodaj nowy produkt"):
            with st.form("add_p"):
                name = st.text_input("Nazwa")
                f1, f2, f3 = st.columns(3)
                pr = f1.number_input("Cena", min_value=0.0)
                qt = f2.number_input("Ilość", min_value=0)
                kt = f3.selectbox("Kategoria", options=list(cat_map.values()) if cat_map else ["Brak"])
                if st.form_submit_button("Zatwierdź i dodaj"):
                    if name and cat_map:
                        cid = [k for k, v in cat_map.items() if v == kt][0]
                        supabase.table("produkty").insert({"nazwa": name, "cena": pr, "liczba": qt, "kategoria_id": cid}).execute()
                        st.toast(f"Dodano {name}")
                        st.rerun()

    with tab2:
        st.subheader("Zarządzanie Kategoriami")
        for cid, cname in cat_map.items():
            cx1, cx2 = st.columns([3,1])
            cx1.write(f"📂 {cname}")
            if cx2.button("Usuń", key=f"c_del_{cid}"):
                supabase.table("kategorie").delete().eq("id", cid).execute()
                st.rerun()
        
        with st.form("new_c"):
            nc = st.text_input("Nazwa nowej kategorii")
            if st.form_submit_button("Dodaj kategorię"):
                if nc:
                    supabase.table("kategorie").insert({"nazwa": nc}).execute()
                    st.rerun()

    with tab3:
        st.subheader("📊 Stan magazynowy na wykresie")
        if products:
            # Tworzymy dane do wykresu: Słownik {Nazwa: Liczba}
            # Streamlit automatycznie narysuje słupki dla tych danych
            chart_data = {p['nazwa']: p['liczba'] for p in products}
            
            # Wyświetlenie wykresu
            st.bar_chart(chart_data)
            
            # Dodatkowy podgląd wartościowy (opcjonalnie)
            st.markdown("### 💰 Wartość zapasów (PLN)")
            val_data = {p['nazwa']: (p['liczba'] * float(p['cena'])) for p in products}
            st.area_chart(val_data)
        else:
            st.info("Dodaj produkty, aby zobaczyć wykresy.")

except Exception as e:
    st.error(f"Wystąpił błąd: {e}")
