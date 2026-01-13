import streamlit as st
from db import add_kategoria, delete_kategoria, add_produkt, delete_produkt, get_kategorie, get_produkty

st.title("🗃️ Zarządzanie Bazą Danych")

st.header("Dodaj kategorię")
nazwa_kat = st.text_input("Nazwa kategorii")
opis_kat = st.text_area("Opis kategorii")
if st.button("Dodaj kategorię"):
    add_kategoria(nazwa_kat, opis_kat)
    st.success("Dodano kategorię!")

st.header("Usuń kategorię")
kategorie = get_kategorie()
kat_id = st.selectbox("Wybierz kategorię do usunięcia", [k["id"] for k in kategorie])
if st.button("Usuń kategorię"):
    delete_kategoria(kat_id)
    st.success("Usunięto kategorię!")

st.header("Dodaj produkt")
nazwa_prod = st.text_input("Nazwa produktu")
opis_prod = st.text_area("Opis produktu")
kat_id_prod = st.selectbox("Kategoria produktu", [k["id"] for k in kategorie])
if st.button("Dodaj produkt"):
    add_produkt(nazwa_prod, opis_prod, kat_id_prod)
    st.success("Dodano produkt!")

st.header("Usuń produkt")
produkty = get_produkty()
prod_id = st.selectbox("Wybierz produkt do usunięcia", [p["id"] for p in produkty])
if st.button("Usuń produkt"):
    delete_produkt(prod_id)
    st.success("Usunięto produkt!")

