# auth_manager.py — Google OAuth & Role-Based Access Control (RBAC) Module

import json
import os
import urllib.parse
import streamlit as st
import requests
import hashlib

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROLES_FILE_PATH = os.path.join(ROOT_DIR, "config", "roles.json")
CREDENTIALS_FILE_PATH = os.path.join(ROOT_DIR, "config", "credentials.json")

def load_credentials():
    if os.path.exists(CREDENTIALS_FILE_PATH):
        try:
            with open(CREDENTIALS_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_credentials(creds):
    with open(CREDENTIALS_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(creds, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def load_roles_config():
    """Load roles configuration from config/roles.json."""
    if os.path.exists(ROLES_FILE_PATH):
        try:
            with open(ROLES_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading roles config: {e}")
    return {
        "roles": {"admin": [], "manager": [], "viewer": []},
        "domain_defaults": {},
        "permissions": {
            "admin": ["view_dashboard", "export_data", "save_snapshot", "delete_snapshot", "clear_cache"],
            "manager": ["view_dashboard", "export_data", "save_snapshot"],
            "viewer": ["view_dashboard"]
        }
    }

def get_google_auth_config():
    """Fetch Google OAuth credentials from st.secrets or environment variables."""
    client_id = None
    client_secret = None
    redirect_uri = "http://localhost:8501"

    # Try st.secrets first
    try:
        if hasattr(st, "secrets") and "google_oauth" in st.secrets:
            client_id = st.secrets["google_oauth"].get("client_id")
            client_secret = st.secrets["google_oauth"].get("client_secret")
            redirect_uri = st.secrets["google_oauth"].get("redirect_uri", redirect_uri)
    except Exception:
        pass

    # Fallback to environment variables if still None
    if not client_id:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", redirect_uri)

    return client_id, client_secret, redirect_uri

def resolve_role(email):
    """Determine role based on user email and roles.json."""
    if not email:
        return "viewer"

    email_clean = email.strip().lower()
    config = load_roles_config()
    roles_map = config.get("roles", {})
    
    # Check explicit email mappings
    for role, emails in roles_map.items():
        if any(e.lower() == email_clean for e in emails):
            return role

    # Check domain defaults
    domain_defaults = config.get("domain_defaults", {})
    if "@" in email_clean:
        domain = email_clean.split("@")[-1]
        if domain in domain_defaults:
            return domain_defaults[domain]

    # Default fallback
    return "viewer"

def has_permission(permission_name):
    """Check if currently logged-in user has specific permission."""
    user = st.session_state.get("user")
    if not user:
        return False
    
    role = user.get("role", "viewer")
    config = load_roles_config()
    role_perms = config.get("permissions", {}).get(role, [])
    return permission_name in role_perms

def init_auth_session():
    """Ensure session state variables for authentication are initialized."""
    from streamlit_cookies_controller import CookieController
    
    if "cookie_controller" not in st.session_state:
        st.session_state.cookie_controller = CookieController()
        
    if st.session_state.get("user") is None:
        # Check if auth token exists in cookies synchronously via context
        auth_cookie = None
        if hasattr(st, "context") and hasattr(st.context, "cookies"):
            auth_cookie = st.context.cookies.get("auth_token")
            
        if not auth_cookie:
            # This might return None on the first run, but trigger a rerun when ready
            auth_cookie = st.session_state.cookie_controller.get("auth_token")
            
        if auth_cookie:
            # Reconstruct the user session automatically
            role = resolve_role(auth_cookie)
            st.session_state.user = {
                "email": auth_cookie,
                "name": auth_cookie.split("@")[0],  # simple default name
                "picture": None,
                "role": role
            }
            # Force a rerun to immediately render the dashboard if we just loaded the cookie
            st.rerun()
        else:
            st.session_state.user = None

def login_user(email, name="User", picture=None):
    """Store logged-in user info in st.session_state."""
    role = resolve_role(email)
    st.session_state.user = {
        "email": email,
        "name": name,
        "picture": picture,
        "role": role
    }
    # Set the cookie with a 7-day expiration
    if "cookie_controller" in st.session_state:
        st.session_state.cookie_controller.set("auth_token", email, max_age=86400 * 7)

def logout_user():
    """Clear user session state and query parameters."""
    st.session_state.user = None
    if "cookie_controller" in st.session_state:
        st.session_state.cookie_controller.remove("auth_token")
        
    if hasattr(st, "query_params"):
        st.query_params.clear()
    st.rerun()

def render_login_component():
    """Render Custom Email/Password Login + Google Password Reset"""
    init_auth_session()

    client_id, client_secret, redirect_uri = get_google_auth_config()
    
    # Check for authorization code in query params if coming back from Google OAuth
    query_params = getattr(st, "query_params", {})
    if "code" in query_params and client_id and client_secret:
        auth_code = query_params["code"]
        with st.spinner("Memverifikasi email dengan Google... Mohon tunggu sebentar."):
            try:
                token_res = requests.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": auth_code,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                    timeout=10
                )
                if token_res.status_code == 200:
                    tokens = token_res.json()
                    id_token_str = tokens.get("access_token")
                    user_res = requests.get(
                        "https://www.googleapis.com/oauth2/v2/userinfo",
                        headers={"Authorization": f"Bearer {id_token_str}"},
                        timeout=10
                    )
                    if user_res.status_code == 200:
                        info = user_res.json()
                        st.session_state.google_verified_email = info.get("email")
                        st.query_params.clear()
                        st.rerun()
            except Exception as e:
                st.error(f"Google verifikasi gagal: {e}")
                if st.button("Kembali"):
                    st.query_params.clear()
                    st.rerun()
                st.stop()

    # UI Design
    st.markdown("""
    <style>
    /* Full bleed for login page */
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    header { visibility: hidden !important; }
    
    /* Remove padding from columns */
    [data-testid="column"] {
        padding: 0 !important;
    }
    
    /* Red background container on the left */
    .left-bg {
        background: linear-gradient(135deg, #E30613 0%, #900010 100%);
        height: 100vh;
        width: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 10%;
        position: relative;
        overflow: hidden;
    }
    .left-bg::after {
        content: "";
        position: absolute;
        top: -20%;
        right: -10%;
        width: 60vh;
        height: 60vh;
        background: rgba(255,255,255,0.05);
        border-radius: 50%;
        transform: rotate(45deg);
    }
    .left-bg h1 {
        color: white !important;
        font-size: 3.5rem !important;
        font-weight: 800 !important;
        line-height: 1.1 !important;
        margin-bottom: 1.5rem !important;
        z-index: 1;
    }
    .left-bg p {
        color: rgba(255,255,255,0.9) !important;
        font-size: 1.1rem !important;
        line-height: 1.5 !important;
        max-width: 80%;
        z-index: 1;
    }

    /* Style the form */
    [data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
    }
    
    [data-testid="stForm"] button {
        background-color: #111827 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        border: none !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stTextInput"] label {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1], gap="large")
    
    with col1:
        st.markdown("""
        <div class="left-bg">
            <h1>Pantau Performa.<br>Akses Instan.<br>Dari Mana Saja.</h1>
            <p>Dashboard operasional GraPARI Jawa Barat terpadu. Masuk untuk mengelola data dan memantau collection rate harian.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
        
        inner_col1, inner_col2, inner_col3 = st.columns([1, 8, 1])
        with inner_col2:
            st.markdown("""
            <h2 style='font-weight: 800; font-size: 2.2rem; color: var(--text-primary); margin-bottom: 0.2rem;'>Welcome Back!</h2>
            <p style='color: var(--text-muted); font-size: 0.95rem; margin-bottom: 2rem;'>Log in to start managing your dashboard.</p>
            """, unsafe_allow_html=True)
            
            # If user is in reset password mode
            if "google_verified_email" in st.session_state and st.session_state.google_verified_email:
                verified_email = st.session_state.google_verified_email
                st.success(f"✅ Email terverifikasi: **{verified_email}**")
                
                with st.form("reset_password_form"):
                    st.markdown("<div style='font-size: 0.9rem; margin-bottom: 10px;'>Silakan masukkan password baru Anda. <b>Hapus jika browser Anda mengisinya secara otomatis (autofill).</b></div>", unsafe_allow_html=True)
                    new_password = st.text_input("Masukkan Password Baru", type="password")
                    confirm_password = st.text_input("Konfirmasi Password Baru", type="password")
                    
                    submitted_reset = st.form_submit_button("Simpan Password", type="primary", use_container_width=True)
                    
                    if submitted_reset:
                        if not new_password:
                            st.error("Password tidak boleh kosong.")
                        elif new_password != confirm_password:
                            st.error("Password tidak cocok. Periksa kembali ketikan Anda.")
                        else:
                            creds = load_credentials()
                            if verified_email not in creds:
                                creds[verified_email] = {}
                            creds[verified_email]["password_hash"] = hash_password(new_password)
                            save_credentials(creds)
                            
                            st.success("Password berhasil diubah! Silakan klik Batal lalu Login.")
                            st.session_state.google_verified_email = None
                            st.rerun()
                            
                if st.button("Batal", use_container_width=True):
                    st.session_state.google_verified_email = None
                    st.rerun()
                    
                st.stop()

            # Regular Login Form
            with st.form("login_form"):
                input_email = st.text_input("Email")
                input_password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
                
                if submitted:
                    if not input_email or not input_password:
                        st.error("Email dan Password harus diisi.")
                    else:
                        creds = load_credentials()
                        user_cred = creds.get(input_email)
                        if user_cred and user_cred.get("password_hash") == hash_password(input_password):
                            login_user(email=input_email)
                            st.rerun()
                        else:
                            st.error("Email atau Password salah.")

            st.markdown("<hr style='margin: 15px 0'>", unsafe_allow_html=True)
            st.markdown("<div style='text-align: center; margin-bottom: 15px; font-size: 13px; color: gray;'>Lupa password? Atur ulang via Google</div>", unsafe_allow_html=True)
            
            if not client_id or not client_secret:
                st.error("⚠️ Google OAuth Client ID is not configured. Please set GOOGLE_CLIENT_ID & GOOGLE_CLIENT_SECRET in environment or secrets.toml")
                return
                
            # Render official Google Login Link for Reset Password
            google_auth_url = (
                "https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={urllib.parse.quote(client_id)}&"
                f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
                "response_type=code&"
                "scope=" + urllib.parse.quote("openid email profile") + "&"
                "access_type=offline&prompt=consent"
            )
            st.markdown(f"""
            <a href="{google_auth_url}" target="_self" style="text-decoration: none;">
                <button style="width: 100%; display: flex; align-items: center; justify-content: center; gap: 12px; background-color: #ffffff; color: #374151; border: 1px solid #d1d5db; padding: 12px 24px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <svg width="18" height="18" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
                    </svg>
                    Reset Password
                </button>
            </a>
            """, unsafe_allow_html=True)

def render_user_header():
    """Render top right user badge with Role indicator & Logout button."""
    user = st.session_state.get("user")
    if not user:
        return

    email = user.get("email", "")
    name = user.get("name", "User")
    role = user.get("role", "viewer").upper()

    role_colors = {
        "ADMIN": "#EF4444",
        "MANAGER": "#F59E0B",
        "CO-VIEWER": "#3B82F6",
        "VIEWER": "#10B981"
    }
    badge_bg = role_colors.get(role, "#6B7280")

    col_info, col_logout = st.columns([4, 1])
    with col_info:
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: flex-end; gap: 10px; margin-bottom: 10px;">
            <div style="text-align: right;">
                <div style="font-size: 14px; font-weight: 600; color: var(--text-primary, #111827);">{name}</div>
                <div style="font-size: 12px; color: var(--text-muted, #6b7280);">{email}</div>
            </div>
            <span style="background-color: {badge_bg}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 700; text-transform: uppercase;">
                {role}
            </span>
        </div>
        """, unsafe_allow_html=True)
    with col_logout:
        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            logout_user()
