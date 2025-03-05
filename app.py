import streamlit as st
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import plotly.express as px

# Interface Streamlit
st.set_page_config(page_title="🎵 Analisador de Spotify", layout="wide")

st.title('Spotify Analysis')

# Seleção do usuário
selected_user = st.selectbox('Escolha o cliente para autenticar:',
                             ['duduguima', 'smokyarts'])

# Configurações do Spotify API

id_key = f"client_id_{selected_user}"
st.write(id_key)
#CLIENT_ID = st.secrets[]
# CLIENT_SECRET 
# REDIRECT_URI = "http://localhost:8888/callback"
# SCOPE = "playlist-read-private user-top-read"
