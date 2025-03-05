import streamlit as st
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import plotly.express as px
import os

st.set_page_config(page_title="🎵 Analisador de Spotify", layout="wide")

# Configurações do Spotify API
CLIENT_ID = st.secrets['SPOTIFY_CLIENT_ID']
CLIENT_SECRET = st.secrets['SPOTIFY_CLIENT_SECRET']
REDIRECT_URI = st.secrets['SPOTIFY_REDIRECT_URI'] # Altere para o URL de callback correto
SCOPE = "playlist-read-private user-top-read"

# Criar autenticação do Spotify
auth_manager = SpotifyOAuth(client_id=CLIENT_ID,
                             client_secret=CLIENT_SECRET,
                             redirect_uri=REDIRECT_URI,
                             scope=SCOPE,
                             show_dialog=True)  # Isso força o usuário a sempre fazer login

# Função para autenticação e pegar o token
def authenticate():
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp

# Função para buscar playlists do usuário
def get_user_playlists(sp):
    playlists = sp.current_user_playlists()
    return {p["name"]: p["id"] for p in playlists["items"]}

# Função para buscar músicas e álbuns de uma playlist
def get_playlist_tracks(sp, playlist_id):
    tracks_data = []
    results = sp.playlist_tracks(playlist_id)
    
    while results:
        for item in results["items"]:
            track = item["track"]
            artist_name = track["artists"][0]["name"]
            album_name = track["album"]["name"]
            album_artist = track["album"]["artists"][0]["name"]
            tracks_data.append([track["name"], artist_name, album_name, album_artist])
        
        results = sp.next(results) if results["next"] else None
    
    return pd.DataFrame(tracks_data, columns=["Música", "Artista", "Álbum", "Artista do Álbum"])

# Função para buscar as músicas mais ouvidas das últimas 4 semanas (agora com até 400 músicas)
def get_top_tracks(sp):
    tracks_data = []
    results = sp.current_user_top_tracks(limit=50, time_range="short_term")  # Últimas 4 semanas
    
    while results:
        tracks_data.extend([[track["name"], track["artists"][0]["name"], track["album"]["name"], 
                             track["album"]["artists"][0]["name"], track["popularity"]]
                            for track in results["items"]])
        
        if len(tracks_data) >= 500:
            break
        
        results = sp.next(results) if results["next"] else None
    
    return pd.DataFrame(tracks_data[:500], columns=["Música", "Artista", "Álbum", "Artista do Álbum", "Popularidade"])

# Autenticação e obtenção do token
sp = authenticate()

# Configuração do Streamlit
st.title("🎵 Analisador de Spotify - Playlists & Músicas Mais Ouvidas")

st.write("Clique no botão abaixo para autenticar com sua conta Spotify:")

if st.button("🔑 Fazer login no Spotify"):
    auth_url = auth_manager.get_authorize_url()
    st.markdown(f"[Clique aqui para autenticar]( {auth_url} )", unsafe_allow_html=True)

# Verificar se o token foi gerado e usuário está autenticado
if sp.current_user():
    user_info = sp.current_user()
    st.success(f"✅ Logado como: {user_info['display_name']}")

    playlists = get_user_playlists(sp)
    playlist_name = st.selectbox("Selecione uma playlist:", list(playlists.keys()))

    # Criar abas para visualizações
    tab1, tab2 = st.tabs([f"🎤 Top 5 Artistas da Playlist {playlist_name}", "🔥 Mais Ouvidas (Últimas 4 Semanas)"])

    # 🔹 Aba 1 - Análise de uma Playlist (Top Artistas)
    with tab1:
        st.subheader("🎤 Top 5 Artistas com Mais Músicas na Playlist")
        
        if playlist_name:
            playlist_id = playlists[playlist_name]
            df_tracks = get_playlist_tracks(sp, playlist_id)

            if df_tracks.empty:
                st.warning("❌ Essa playlist não contém músicas!")
            else:
                artist_counts = df_tracks["Artista"].value_counts().reset_index()
                artist_counts.columns = ["Artista", "Quantidade"]
                top_5_artists = artist_counts.head(5)

                st.dataframe(top_5_artists)

    # 🔹 Aba 2 - Músicas Mais Ouvidas (Últimas 4 Semanas)
    with tab2:
        st.subheader("🔥 Suas Músicas Mais Ouvidas nas Últimas 4 Semanas")

        df_top_tracks = get_top_tracks(sp)

        if df_top_tracks.empty:
            st.warning("❌ Nenhuma música encontrada no seu histórico!")
        else:
            st.dataframe(df_top_tracks)

            fig_top_tracks = px.bar(df_top_tracks, x="Música", y="Popularidade",
                                    title="Top 10 Músicas Mais Ouvidas (4 Semanas)", text_auto=True, color="Popularidade",)

            fig_top_tracks.update_layout(xaxis=dict(tickangle=45))

            st.plotly_chart(fig_top_tracks)
