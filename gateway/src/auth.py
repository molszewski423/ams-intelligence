"""AMS Gateway — Authentication Gate."""

from __future__ import annotations
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.exceptions import LoginError


def _build_authenticator() -> stauth.Authenticate:
    creds_raw   = st.secrets.get("credentials", {})
    usernames   = creds_raw.get("usernames", {})
    credentials = {"usernames": {k: dict(v) for k, v in usernames.items()}}
    cookie      = st.secrets.get("cookie", {})
    return stauth.Authenticate(
        credentials,
        cookie.get("name", "ams_gateway_auth"),
        cookie.get("key", "fallback_key_change_me"),
        cookie_expiry_days=int(cookie.get("expiry_days", 30)),
        auto_hash=False,
    )


def _get_authenticator() -> stauth.Authenticate:
    if "authenticator" not in st.session_state:
        st.session_state.authenticator = _build_authenticator()
    return st.session_state.authenticator


def is_authenticated() -> bool:
    return bool(st.session_state.get("authentication_status"))


def current_user() -> dict:
    return {
        "name":     st.session_state.get("name", "User"),
        "username": st.session_state.get("username", ""),
    }


def require_auth() -> None:
    if is_authenticated():
        return

    st.markdown(
        """<style>
        [data-testid="stSidebar"] {display: none;}
        .block-container {max-width: 460px; margin: 80px auto;}
        </style>""",
        unsafe_allow_html=True,
    )
    st.markdown("## 🏥 Clinical Intelligence Portal")
    st.caption("Pharmacovigilance & Antimicrobial Stewardship Research Platform — Restricted Access")
    st.markdown("---")

    authenticator = _get_authenticator()
    try:
        authenticator.login(
            location="main",
            fields={"Form name": "Sign in", "Username": "Username",
                    "Password": "Password", "Login": "Sign in"},
        )
    except LoginError:
        for key in ("authentication_status", "name", "username", "email", "authenticator"):
            st.session_state.pop(key, None)

    auth_status = st.session_state.get("authentication_status")
    if auth_status is False:
        st.error("Incorrect username or password.")
    elif auth_status is None:
        st.caption("Enter your credentials above.")

    st.stop()


def auth_sidebar() -> None:
    if not is_authenticated():
        return
    user = current_user()
    st.markdown("---")
    st.markdown(f"**{user['name']}**")
    st.caption(f"@{user['username']}")
    authenticator = _get_authenticator()
    authenticator.logout(button_name="Sign out", location="sidebar", key="logout_local")
