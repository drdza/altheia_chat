# frontend/pages/03_Logout.py

import streamlit as st
from services.auth_service import logout_user

def main():
    logout_user()
    st.switch_page("pages/00_welcome.py")


if __name__ == "__main__":
    main()