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
# O escopo de permissões que você deseja obter (exemplo: acessar informações do perfil do usuário)
SCOPE = 'user-library-read'

# Criar o gerenciador de autenticação
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                client_secret=CLIENT_SECRET,
                                                redirect_uri=REDIRECT_URI,
                                                scope=SCOPE))

# Agora você pode usar a API com a nova conta
# Exemplo: Consultar o perfil do usuário
user_profile = sp.current_user()
print("Perfil do Usuário:")
print(f"Nome: {user_profile['display_name']}")
print(f"ID do Usuário: {user_profile['id']}")
print(f"Imagem de Perfil: {user_profile['images'][0]['url'] if user_profile['images'] else 'Sem imagem'}")

# Exemplo: Consultar as músicas salvas do usuário
saved_tracks = sp.current_user_saved_tracks(limit=10)
print("\nMúsicas salvas:")
for idx, item in enumerate(saved_tracks['items']):
    track = item['track']
    print(f"{idx + 1}. {track['name']} - {track['artists'][0]['name']}")
