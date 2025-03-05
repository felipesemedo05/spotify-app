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

# Usuário a ser escolhido (não mais usando selectbox)
user_selection = st.selectbox("Selecione o usuário", ["duduguima", "smokyarts"])

if user_selection:  # Verifica se o nome do usuário foi informado
    # Construir as chaves dinamicamente com base no nome do usuário
    client_id_key = f"client_id_{user_selection}"
    client_secret_key = f"client_secret_{user_selection}"

    if client_id_key in st.secrets and client_secret_key in st.secrets:
        # Obter as credenciais com base na seleção
        client_id = st.secrets[client_id_key]
        client_secret = st.secrets[client_secret_key]

        # Autenticar com a API do Spotify
        spotify = get_spotify_client(client_id, client_secret)

        # Mostrar as informações do usuário
        st.header(f"Informações do usuário {user_selection}")
        show_user_info(spotify)
    else:
        st.error("Usuário não encontrado. Por favor, insira 'duduguima' ou 'smokyarts'.")