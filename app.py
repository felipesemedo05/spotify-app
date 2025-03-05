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
id_secret = f"client_secret_{selected_user}"

CLIENT_ID = st.secrets[id_key]
CLIENT_SECRET = st.secrets[id_secret]
REDIRECT_URI = "https://spotify-app-qtnrmxu4qmnesgsgoyvvxg.streamlit.app/callback"
SCOPE = "playlist-read-private user-top-read"

# Criar autenticação do Spotify
auth_manager = SpotifyOAuth(client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            redirect_uri=REDIRECT_URI,
                            scope=SCOPE)

sp = spotipy.Spotify(auth_manager=auth_manager)

def get_user_playlists():
    playlists = sp.current_user_playlists()
    return {p["name"]: p["id"] for p in playlists["items"]}

user_info = sp.current_user()
st.write(user_info)
