import streamlit as st
import requests
import urllib.parse
import pandas as pd

# Configurações do seu app no Spotify
CLIENT_ID = st.secrets['SPOTIFY_CLIENT_ID']
CLIENT_SECRET = st.secrets['SPOTIFY_CLIENT_SECRET']
REDIRECT_URI = st.secrets['SPOTIFY_REDIRECT_URI'] # Ajuste conforme seu domínio público

SCOPE = "playlist-read-private user-read-private user-read-email"  # Adicionado escopo para ler playlists

# URLs da API do Spotify
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_ME = "https://api.spotify.com/v1/me"
SPOTIFY_API_PLAYLISTS = "https://api.spotify.com/v1/me/playlists"
SPOTIFY_API_PLAYLIST_TRACKS = "https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

# Criar a URL de autenticação
def get_auth_url():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

# Função para trocar código por token
def get_access_token(code):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=data)
    return response.json()

# Função para buscar informações do usuário
def get_user_info(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(SPOTIFY_API_ME, headers=headers)
    return response.json()

# Função para buscar playlists do usuário
def get_user_playlists(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(SPOTIFY_API_PLAYLISTS, headers=headers)
    return response.json()

# Função para buscar todas as músicas de uma playlist (página por página)
def get_all_playlist_tracks(access_token, playlist_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    tracks = []
    next_url = SPOTIFY_API_PLAYLIST_TRACKS.format(playlist_id=playlist_id)
    
    while next_url:
        response = requests.get(next_url, headers=headers).json()
        tracks.extend(response.get("items", []))
        next_url = response.get("next")  # Pega a próxima página
    
    return tracks

# Interface Streamlit
st.title("Login com Spotify")

# Captura do código de autenticação na URL
query_params = st.query_params
if "code" in query_params:
    code = query_params["code"]
    st.success("Código de autenticação recebido!")
    
    # Troca o código pelo token de acesso
    token_info = get_access_token(code)
    if "access_token" in token_info:
        st.session_state["access_token"] = token_info["access_token"]
        st.success("Autenticação bem-sucedida!")
    else:
        st.error("Erro ao obter o token de acesso.")

# Exibir botão de login caso não esteja autenticado
if "access_token" not in st.session_state:
    st.markdown(f"[Clique aqui para fazer login no Spotify]({get_auth_url()})")
else:
    access_token = st.session_state["access_token"]
    user_info = get_user_info(access_token)
    st.write(f"Usuário autenticado como {user_info['display_name']}")

        # Buscar e exibir playlists do usuário
    playlists_data = get_user_playlists(access_token)
    playlists = {p["name"]: p["id"] for p in playlists_data.get("items", [])}
    
    if playlists:
        selected_playlist = st.selectbox("Selecione uma playlist:", list(playlists.keys()))
        
        if selected_playlist:
            playlist_id = playlists[selected_playlist]
            tracks_data = get_all_playlist_tracks(access_token, playlist_id)
            
            # Contagem de músicas por artista
            artist_count = {}
            track_list = []
            
            for item in tracks_data:
                track = item.get("track", {})
                track_name = track.get("name", "Desconhecido")
                artists = [artist["name"] for artist in track.get("artists", [])]
                track_list.append({"Música": track_name, "Artistas": ", ".join(artists)})
                
                for artist in artists:
                    artist_count[artist] = artist_count.get(artist, 0) + 1
            
            # Exibir todas as músicas
            df_tracks = pd.DataFrame(track_list)
            st.write("Músicas na Playlist:")
            st.dataframe(df_tracks)
            
            # Exibir análise
            df_artists = pd.DataFrame(artist_count.items(), columns=["Artista", "Total de Músicas"])
            df_artists = df_artists.sort_values(by="Total de Músicas", ascending=False)
            st.write("Análise de músicas por artista na playlist:")
            st.dataframe(df_artists)