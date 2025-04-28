import requests
import json
from streamlit_lottie import st_lottie

def load_lottieurl(url):
    """
    Carrega animação Lottie de uma URL
    """
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception as e:
        print(f"Error loading Lottie animation: {e}")
        return None

def load_lottiefile(filepath):
    """
    Carrega animação Lottie de um arquivo local
    """
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading Lottie file: {e}")
        return None

def display_lottie_animation(lottie_data, height=200, width=None, key=None):
    """
    Exibe uma animação Lottie com os parâmetros especificados
    """
    if lottie_data:
        st_lottie(
            lottie_data, 
            height=height,
            width=width,
            key=key,
            speed=1,
            loop=True,
            quality="high"
        )