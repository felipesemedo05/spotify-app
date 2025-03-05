import streamlit as st
import time
import requests
import json
from collections import Counter
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

# Funções auxiliares para acessar e renovar tokens (como já discutido)
TOKEN_FILE = "tokens.json"
TOKEN_URL = "https://accounts.spotify.com/api/token"

CLIENTS = {
    "duduguima": {
        "client_id": st.secrets['client_id_duduguima'],
        "client_secret": st.secrets['client_secret_duduguima']
    },
    "smokyarts": {
        "client_id": st.secrets['client_id_smokyarts'],
        "client_secret": st.secrets['client_secret_smokyarts']
    }
}

def load_tokens():
    with open(TOKEN_FILE, "r") as file:
        return json.load(file)

def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as file:
        json.dump(tokens, file, indent=4)

def refresh_access_token(user):
    tokens = load_tokens()
    refresh_token = tokens[user]["refresh_token"]
    
    client_id = CLIENTS[user]["client_id"]
    client_secret = CLIENTS[user]["client_secret"]

    response = requests.post(TOKEN_URL, data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    })

    if response.status_code == 200:
        new_token_data = response.json()
        tokens[user]["access_token"] = new_token_data["access_token"]
        tokens[user]["expires_at"] = time.time() + new_token_data.get("expires_in", 3600)
        save_tokens(tokens)
        return new_token_data["access_token"]
    else:
        return None

def get_valid_token(user):
    tokens = load_tokens()
    if time.time() > tokens[user]["expires_at"]:
        return refresh_access_token(user)
    return tokens[user]["access_token"]

def get_user_info(access_token):
    url = "https://api.spotify.com/v1/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_user_playlists(access_token):
    url = "https://api.spotify.com/v1/me/playlists"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['items']
    else:
        return []

def get_playlist_tracks(access_token, playlist_id):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    all_tracks = []
    # Paginação: Para pegar todas as faixas
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            all_tracks.extend(data['items'])
            url = data.get('next', None)  # Pega o link da próxima página, se houver
        else:
            st.error("Erro ao carregar as faixas da playlist")
            break
    
    return all_tracks

def get_tracks_dataframe(tracks):
    track_data = []
    for track in tracks:
        track_info = track['track']
        track_data.append({
            'track_name': track_info['name'],
            'artist_name': track_info['artists'][0]['name'],
            'album_name': track_info['album']['name'],
            'release_date': track_info['album']['release_date']
        })
    
    # Criar DataFrame
    df = pd.DataFrame(track_data)
    return df

# Streamlit Interface
st.title("Spotify Authentication and Playlists")

# Menu de navegação
st.sidebar.title("Navegação")
option = st.sidebar.radio("Escolha uma opção", ("Informações do Usuário", "Playlists"))

# Usuário selecionado
user = st.selectbox("Usuário", ["duduguima", "smokyarts"])

# Obtendo o token válido
access_token = get_valid_token(user)

if option == "Informações do Usuário":
    st.header("Informações do Usuário")
    user_info = get_user_info(access_token)

    if user_info:
        st.write(f"Nome: {user_info['display_name']}")
        st.write(f"Email: {user_info['email']}")
        st.image(user_info['images'][0]['url'] if user_info['images'] else None)
    else:
        st.error("Erro ao acessar as informações do usuário")

elif option == "Playlists":
    st.header("Suas Playlists")
    playlists = get_user_playlists(access_token)

    if playlists:
        playlist_names = [playlist['name'] for playlist in playlists]
        selected_playlist_name = st.selectbox("Escolha uma playlist", playlist_names)

        selected_playlist = next(playlist for playlist in playlists if playlist['name'] == selected_playlist_name)
        st.write(f"Você selecionou a playlist: {selected_playlist_name}")

        # Obtendo as faixas da playlist
        tracks = get_playlist_tracks(access_token, selected_playlist['id'])

        if tracks:
            # Criando DataFrame
            df = get_tracks_dataframe(tracks)
            st.write(f"Total de faixas na playlist: {len(df)}")
            st.dataframe(df)  # Exibe o DataFrame com as faixas
        else:
            st.error("Erro ao carregar as faixas da playlist")
    else:
        st.error("Você não tem playlists.")
