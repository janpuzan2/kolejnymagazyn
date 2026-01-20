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
st.set_page_config(page_title="Magazyn Pro Light", layout="wide", page_icon="📦")

try:
    # Pobieranie danych
    products = supabase.table("produkty").select("*").order("id").execute().data
    categories = supabase.table("kategorie").select("*").execute().data
    cat_map = {c['id']: c['nazwa'] for c in categories}

    # --- STATYSTYKI ---
    st.title("📦 System Magazynowy")
    
    total_qty = sum(p['liczba'] for p in products) if products else 0
    total_val = sum(p['liczba'] * float(p['cena']) for p in products) if products else 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("Suma produktów", f"{total_qty} szt.")
    m2.metric("Wartość towaru", f"{total_val:,.2f} zł")
    m3.progress(min(total_qty / 1000, 1.0), text=f"Zapełnienie: {total_qty}/1000")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["🛒 Inwentarz", "📂 Kategorie", "📊 Analityka"])

    with tab1:
        search = st.text_input("🔍 Szukaj produktu...", "").lower()
        # Filtrujemy produkty
        filtered = [p for p in products if search in p['nazwa'].lower()]

        if filtered:
            # --- NAGŁÓWKI (Dodano kolumnę Kategoria) ---
            cols = st.columns([0.5, 0.4, 2, 1.2, 0.8, 1.5, 1, 0.5])
            header_names = ["ID", "Kol.", "Nazwa", "Kategoria", "Cena", "Ilość", "Status", ""]
            for col, h in zip(cols, header_names): col.write(f"**{h}**")
            
            for p in filtered:
                p_color = get_product_color(p['nazwa'])
                # Pobieramy nazwę kategorii z mapy po ID
                p_cat_name = cat_map.get(p['kategoria_id'], "Brak")
                
                c1, c_col, c2, c_cat, c3, c4, c_status, c5 = st.columns([0.5, 0.4, 2, 1.2, 0.8, 1.5, 1, 0.5])
                
                c1.write(f"`{p['id']}`")
                c_col.markdown(f'<div style="width:15px; height:15px; background:{p_color}; border-radius:50%; margin-top:10px; border:1px solid #ddd"></div>', unsafe_allow_html=True)
                c2.write(f"**{p['nazwa']}**")
                
                # WYŚWIETLANIE KATEGORII jako szary badge
                c_cat.markdown(f'<span style="background-color: #f0f2f6; padding: 2px 8px; border-radius: 10px; font-size: 0.8rem; color: #555; border: 1px solid #ddd;">{p_cat_name}</span>', unsafe_allow_html=True)
                
                c3.write(f"{p['cena']} zł")
                
                # Szybka edycja ilości
                with c4:
                    q_min, q_val, q_pls = st.columns([1, 1, 1])
                    if q_min.button("−", key=f"m_{p['id']}"):
                        supabase.table("produkty").update({"liczba": max(0, p['liczba'] - 1)}).eq("id", p['id']).execute()
                        st.rerun()
                    q_val.write(f"{p['liczba']}")
                    if q_pls.button("+", key=f"p_{p['id']}"):
                        supabase.table("produkty").update({"liczba": p['liczba'] + 1}).eq("id", p['id']).execute()
                        st.rerun()
                
                # Statusy
                if p['liczba'] == 0: c_status.error("Brak")
                elif p['liczba'] < 5: c_status.warning("Mało")
                else: c_status.success("OK")

                if c5.button("🗑️", key=f"d_{p['id']}"):
                    supabase.table("produkty").delete().eq("id", p['id']).execute()
                    st.toast(f"Usunięto {p['nazwa']}")
                    st.rerun()

        # Sekcja dodawania
        st.markdown("---")
        with st.expander("➕ Dodaj nowy produkt"):
            with st.form("add_form_final", clear_on_submit=True):
                name = st.text_input("Nazwa produktu")
                f1, f2, f3 = st.columns(3)
                price = f1.number_input("Cena (zł)", min_value=0.0)
                qty = f2.number_input("Ilość", min_value=0)
                cat = f3.selectbox("Wybierz kategorię", options=list(cat_map.values()))
                
                if st.form_submit_button("Dodaj do bazy"):
                    if name:
                        selected_cat_id = [k for k, v in cat_map.items() if v == cat][0]
                        supabase.table("produkty").insert({
                            "nazwa": name, "cena": price, "liczba": qty, "kategoria_id": selected_cat_id
                        }).execute()
                        st.toast(f"Dodano produkt: {name}")
                        st.rerun()

    with tab2:
        st.subheader("📁 Zarządzanie kategoriami")
        c_list, c_add = st.columns([2, 1])
        with c_list:
            for cid, cname in cat_map.items():
                col_n, col_b = st.columns([3, 1])
                col_n.write(f"• {cname}")
                if col_b.button("Usuń", key=f"del_cat_{cid}"):
                    supabase.table("kategorie").delete().eq("id", cid).execute()
                    st.rerun()
        with c_add:
            new_cat = st.text_input("Nazwa nowej kategorii")
            if st.button("Dodaj kategorię") and new_cat:
                supabase.table("kategorie").insert({"nazwa": new_cat}).execute()
                st.rerun()

    with tab3:
        st.subheader("📊 Podsumowanie ilościowe")
        if products:
            chart_dict = {p['nazwa']: p['liczba'] for p in products}
            st.bar_chart(chart_dict)
        else:
            st.info("Brak danych do wykresu.")

except Exception as e:
    st.error(f"Wystąpił błąd połączenia: {e}")
