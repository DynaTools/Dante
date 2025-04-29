import streamlit as st
import requests
import pandas as pd
import datetime
import os
import base64
import json
# Removed Lottie import
from utils.local_storage import save_key, get_key

# Page configuration
st.set_page_config(
    page_title="Dante AI - AI & Politics Tweets",
    page_icon="🐦",
    layout="wide"
)

# Added Coming Soon placeholder
st.title("🐦 AI & Politics – Coming Soon")
st.info("This page is under construction. Please check back soon!")
st.stop()

