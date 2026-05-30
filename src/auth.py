"""AMS Intelligence — Authentication Gate (same pattern as PV Workbench)."""

from __future__ import annotations
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.exceptions import LoginError


def _build_authenticator() -> stauth.Authenticate:
    creds_raw  = st.secrets.get("credentials", {})
    usernames  = creds_raw.get("usernames", {})
    credentials = {"usernames": {k: dict(v) for k, v in usernames.items()}}
    cookie     = st.secrets.get("cookie", {})
    return stauth.Authenticate(
        credentials,
        cookie.get("name", "ams_intel_auth"),
        cookie.get("key", "fallback_key_change_me"),
        cookie_expiry_days=int(cookie.get("expiry_days", 30)),
        auto_hash=False,
    )


def _get_authenticator() -> stauth.Authenticate:
    if "authenticator" not in st.session_state:
        st.session_state.authenticator = _build_authenticator()
    return st.session_state.authenticator


def _oauth_user_logged_in() -> bool:
    try:
        return bool(st.user.is_logged_in)
    except Exception:
        return False


def is_authenticated() -> bool:
    if _oauth_user_logged_in():
        return True
    return bool(st.session_state.get("authentication_status"))


def current_user() -> dict:
    if _oauth_user_logged_in():
        try:
            return {"name": getattr(st.user, "name", "") or st.user.email,
                    "email": st.user.email, "method": "oauth"}
        except Exception:
            return {"name": "OAuth User", "email": "", "method": "oauth"}
    return {"name": st.session_state.get("name", "User"),
            "email": "", "method": "local"}


def require_auth() -> None:
    if is_authenticated():
        return

    st.markdown(
        """<style>
        [data-testid="stSidebar"] {display: none;}
        .block-container {max-width: 480px; margin: 60px auto;}
        </style>""",
        unsafe_allow_html=True,
    )
    st.markdown("## 🦠 AMS Intelligence")
    st.caption("Antimicrobial Stewardship Research Pipeline — Restricted Access")
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
    if user["email"]:
        st.caption(user["email"])
    st.caption(f"Auth: {user['method']}")
    if user["method"] == "oauth":
        if st.button("Sign out", key="logout_oauth"):
            st.logout()
    else:
        authenticator = _get_authenticator()
        authenticator.logout(button_name="Sign out", location="sidebar", key="logout_local")
