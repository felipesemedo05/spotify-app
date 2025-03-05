import streamlit as st
import time
import requests
import json
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

# Funções auxiliares para acessar e renovar tokens (como já discutido)
TOKEN_FILE = "tokens.json"
TOKEN_URL = "https://accounts.spotify.com/api/token"

CLIENTS = {
    "duduguima": {
        "client_id": "CLIENT_ID_DUDUGUIMA",
        "client_secret": "CLIENT_SECRET_DUDUGUIMA"
    },
    "smokyarts": {
        "client_id": "CLIENT_ID_SMOKYARTS",
        "client_secret": "CLIENT_SECRET_SMOKYARTS"
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

# Streamlit Interface
st.title("Spotify Authentication")
st.write("Escolha um usuário para ver suas informações:")

user = st.selectbox("Usuário", ["duduguima", "smokyarts"])

access_token = get_valid_token(user)
user_info = get_user_info(access_token)

if user_info:
    st.write(f"Nome: {user_info['display_name']}")
    st.write(f"Email: {user_info['email']}")
    st.image(user_info['images'][0]['url'] if user_info['images'] else None)
else:
    st.error("Erro ao acessar as informações do usuário")
