import streamlit as st

st.set_page_config(
    page_title="Coal Dashboard",
    layout="wide"
)

# ===== Soft redirect only once =====
if "redirected" not in st.session_state:
    st.session_state.redirected = True
    st.switch_page("pages/01_Production.py")

# Fallback (kalau switch gagal)
st.title("Coal Dashboard")
st.markdown("Redirecting to Production…")
