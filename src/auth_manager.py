import streamlit as st
import hashlib

# auth_manager.py — Access Control for Data Management

# Hardcoded dummy accounts with hashed passwords to prevent plain-text exposure
AUTHORIZED_ACCOUNTS = {
    "admin": "a36aef5a11c4073fbe60314fc9df530a9d5f986533594d1f5190742ff9e0e408",
    "manager": "f3cdf766bd8256fded84ed1590ab9bbc192ee1e930bd86b450905dfa09d31105"
}

def verify_credentials(username, password):
    if username not in AUTHORIZED_ACCOUNTS:
        return False
    hashed_input = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return hashed_input == AUTHORIZED_ACCOUNTS[username]

def render_data_management_login():
    """Render a standalone login screen for the Data Management feature."""
    st.markdown("""
    <style>
    /* 1. Pusatkan Halaman dan Batasi Lebar (Hanya untuk halaman login) */
    .block-container {
        max-width: 550px !important;
        padding-top: 10vh !important;
    }
    
    /* 2. Styling Kartu Form Utama (Padding sangat lega, dijamin tidak mepet!) */
    [data-testid="stForm"] {
        background-color: var(--bg-surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.12) !important;
        padding: 3.5rem 3rem !important; /* Padding super lega */
    }
    
    /* 3. Styling Header di dalam Kartu */
    .login-header {
        text-align: center;
        margin-bottom: 2.5rem;
    }
    .login-header .login-title {
        color: #E30613 !important; /* Professional Red */
        font-size: 1.8rem !important; /* Diperkecil */
        font-weight: 800 !important;
        margin-bottom: 0.5rem !important;
        line-height: 1.2 !important;
        white-space: nowrap !important; /* Memaksa agar mendatar (tidak turun baris) */
    }
    .login-header p {
        color: var(--text-secondary) !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
    }
    
    /* 4. Beri jarak lega antar input */
    [data-testid="stTextInput"] {
        margin-bottom: 1.5rem !important;
    }
    
    /* 5. Styling Tombol Login Merah */
    [data-testid="stFormSubmitButton"] {
        margin-top: 2rem !important; /* Jarak ekstra lega ke atas */
    }
    [data-testid="stFormSubmitButton"] button {
        background-color: #E30613 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0.6rem 0 !important;
        font-weight: 700 !important;
        border: none !important;
        transition: all 0.2s ease;
    }
    [data-testid="stFormSubmitButton"] button:hover {
        background-color: #B3000D !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(227,6,19,0.3) !important;
    }
    
    /* 6. Styling Tombol Kembali (Di luar kartu) */
    .back-btn-wrapper {
        margin-top: 1.5rem;
        display: flex;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # KARTU LOGIN UTAMA
    with st.form("auth_form", clear_on_submit=False):
        st.markdown("""
        <div class="login-header">
            <div class="login-title">Verifikasi diri anda</div>
            <p>Bukan Admin atau Manager? Anda mungkin belum bisa mengakses fitur ini.</p>
        </div>
        """, unsafe_allow_html=True)
        
        username = st.text_input("Username (admin / manager)")
        password = st.text_input("Password", type="password")
        
        submit = st.form_submit_button("Login Account", use_container_width=True)
        
        if submit:
            if verify_credentials(username.lower().strip(), password):
                st.session_state["data_admin_logged_in"] = True
                st.rerun()
            else:
                st.error("Username atau password salah.")
                
    # TOMBOL KEMBALI (DI LUAR KARTU)
    st.markdown('<div class="back-btn-wrapper">', unsafe_allow_html=True)
    if st.button("Kembali ke Dashboard Utama", use_container_width=True, type="secondary"):
        st.session_state.current_page = "dashboard"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def logout_data_management():
    if "data_admin_logged_in" in st.session_state:
        del st.session_state["data_admin_logged_in"]
    st.session_state.current_page = "dashboard"
    st.rerun()

def has_permission(permission_name):
    return True
