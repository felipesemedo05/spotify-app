import streamlit as st
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

# Função para obter as credenciais do Spotify
def get_spotify_client(client_id, client_secret):
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    return Spotify(client_credentials_manager=client_credentials_manager)

# Função para mostrar as informações do usuário
def show_user_info(spotify):
    user = spotify.current_user()
    st.write(f"Nome: {user['display_name']}")
    st.write(f"ID do usuário: {user['id']}")
    st.write(f"Seguidores: {user['followers']['total']}")

# Layout do Streamlit
st.title('Spotify User Information')

# Seleção do usuário
user_selection = st.selectbox("Selecione o usuário", ["duduguima", "smokyarts"])

# Obter as credenciais de acordo com a seleção usando st.secrets
client_id = st.secrets["spotify"][user_selection]["client_id"]
client_secret = st.secrets["spotify"][user_selection]["client_secret"]

# Autenticar com a API do Spotify
spotify = get_spotify_client(client_id, client_secret)

# Mostrar as informações do usuário
st.header(f"Informações do usuário {user_selection}")
show_user_info(spotify)