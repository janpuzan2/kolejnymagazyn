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

    # --- NAGŁÓWEK I STATYSTYKI ---
    st.title("📦 System Magazynowy")
    
    total_qty = sum(p['liczba'] for p in products) if products else 0
    total_val = sum(p['liczba'] * float(p['cena']) for p in products) if products else 0.0

    m1, m2, m3 = st.columns(3)
    with m1:
        st.info(f"**Suma sztuk:** {total_qty}")
    with m2:
        st.success(f"**Wartość:** {total_val:,.2f} zł")
    with m3:
        # Dynamiczny alert jeśli magazyn jest prawie pełny
        percent = min(int(total_qty / 1000 * 100), 100)
        st.warning(f"**Zapełnienie:** {percent}%")

    st.divider()

    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["🛒 Inwentarz", "📂 Kategorie", "📊 Prosta Analityka"])

    with tab1:
        search = st.text_input("🔍 Szukaj produktu...", "").lower()
        filtered = [p for p in products if search in p['nazwa'].lower()]

        if filtered:
            # Nagłówki
            cols = st.columns([0.5, 0.5, 2, 1, 1.5, 1, 0.5])
            titles = ["ID", "Kol.", "Nazwa", "Cena", "Ilość", "Status", ""]
            for col, t in zip(cols, titles): col.write(f"**{t}**")

            for p in filtered:
                p_color = get_product_color(p['nazwa'])
                c1, c_col, c2, c3, c4, c_status, c5 = st.columns([0.5, 0.5, 2, 1, 1.5, 1, 0.5])
                
                c1.write(f"`{p['id']}`")
                c_col.markdown(f'<div style="width:15px; height:15px; background:{p_color}; border-radius:3px; margin-top:10px; border:1px solid #444"></div>', unsafe_allow_html=True)
                
                # Podświetlenie jeśli zero
                label = f"**{p['nazwa']}**" if p['liczba'] > 0 else f"~~{p['nazwa']}~~ (BRAK)"
                c2.write(label)
                
                c3.write(f"{p['cena']} zł")
                
                with c4:
                    q_min, q_val, q_pls = st.columns([1,1,1])
                    if q_min.button("−", key=f"m_{p['id']}"):
                        supabase.table("produkty").update({"liczba": max(0, p['liczba'] - 1)}).eq("id", p['id']).execute()
                        st.rerun()
                    q_val.write(f"{p['liczba']}")
                    if q_pls.button("+", key=f"p_{p['id']}"):
                        supabase.table("produkty").update({"liczba": p['liczba'] + 1}).eq("id", p['id']).execute()
                        st.rerun()

                if p['liczba'] == 0: c_status.error("Brak")
                elif p['liczba'] < 5: c_status.warning("Mało")
                else: c_status.success("OK")

                if c5.button("🗑️", key=f"d_{p['id']}"):
                    supabase.table("produkty").delete().eq("id", p['id']).execute()
                    st.toast(f"Usunięto {p['nazwa']}")
                    st.rerun()

        # Dodawanie produktu
        st.markdown("---")
        with st.expander("➕ Szybkie dodawanie"):
            with st.form("light_add"):
                n = st.text_input("Nazwa")
                c1, c2, c3 = st.columns(3)
                pr = c1.number_input("Cena", min_value=0.0)
                qt = c2.number_input("Ilość", min_value=0)
                kt = c3.selectbox("Kategoria", options=list(cat_map.values()))
                
                if st.form_submit_button("Zatwierdź"):
                    if n:
                        cid = [k for k, v in cat_map.items() if v == kt][0]
                        supabase.table("produkty").insert({"nazwa": n, "cena": pr, "liczba": qt, "kategoria_id": cid}).execute()
                        st.toast(f"Dodano {n}!", icon="✅")
                        st.rerun()

    with tab2:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            for cid, cname in cat_map.items():
                st.button(f"📁 {cname} (Usuń)", key=f"c_{cid}", on_click=lambda id=cid: supabase.table("kategorie").delete().eq("id", id).execute())
        with col_right:
            new_c = st.text_input("Nowa kategoria")
            if st.button("Dodaj kategorię") and new_c:
                supabase.table("kategorie").insert({"nazwa": new_c}).execute()
                st.rerun()

    with tab3:
        st.subheader("Szybki podgląd stanów")
        if products:
            # Tworzymy dane do wykresu bez Pandasa
            chart_data = {p['nazwa']: p['liczba'] for p in products}
            st.bar_chart(chart_data)
            
            # Prosta lista kontrolna "Do zamówienia"
            low_stock = [p['nazwa'] for p in products if p['liczba'] < 5]
            if low_stock:
                st.warning("⚠️ **Lista zakupowa (poniżej 5 szt.):**")
                for item in low_stock:
                    st.write(f"- {item}")
        else:
            st.info("Brak danych")

except Exception as e:
    st.error(f"Coś poszło nie tak: {e}")
