import streamlit as st
import time
import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from collections import Counter


st.set_page_config(page_title="🎵 Analisador de Spotify", layout="wide")

# Funções auxiliares para acessar e renovar tokens (como já discutido)
TOKEN_FILE = "tokens.json"
TOKEN_URL = "https://accounts.spotify.com/api/token"

CLIENTS = {
    "duduguima": {
        "client_id": "e875ed6d6c774284be23d0d891625989",
        "client_secret": "d51d83756a6e407f893289e233763158"
    },
    "smokyarts": {
        "client_id": "c3c44b8fc55743548e06cbcf9091a144",
        "client_secret": "686d326c88e74648b70b60fcd55bb86c"
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
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            all_tracks.extend(data['items'])
            url = data.get('next', None)
        else:
            st.error("Erro ao carregar as faixas da playlist")
            break
    
    return all_tracks

def get_albums_with_most_tracks(tracks):
    album_counts = {}
    for track in tracks:
        album_name = track['track']['album']['name']
        artist_name = track['track']['album']['artists'][0]['name']
        
        if album_name in album_counts:
            album_counts[album_name]['count'] += 1
        else:
            album_counts[album_name] = {'count': 1, 'artist': artist_name}
    
    # Convertendo para um DataFrame
    album_data = [{"Álbum": album, "Artista do Álbum": data['artist'], "Músicas": data['count']} 
                  for album, data in album_counts.items()]
    
    df_albums = pd.DataFrame(album_data)
    return df_albums.sort_values(by="Músicas", ascending=False)

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
    
    df = pd.DataFrame(track_data)
    return df

def get_top_tracks(access_token):
    tracks_data = []
    url = "https://api.spotify.com/v1/me/top/tracks?time_range=short_term&limit=50"  # Últimas 4 semanas
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    results = requests.get(url, headers=headers).json()
    
    while results:
        # Adiciona as músicas retornadas pela API
        tracks_data.extend([[
            track["name"], 
            track["artists"][0]["name"], 
            track["album"]["name"], 
            track["album"]["artists"][0]["name"], 
            track["popularity"]
        ] for track in results["items"]])

        # Verifica se há mais músicas para pegar
        if len(tracks_data) >= 100:
            break

        # Se houver mais músicas, continua a busca com a próxima página
        url = results.get("next")
        if url:
            results = requests.get(url, headers=headers).json()
        else:
            break

    # Limita a 500 músicas, caso a contagem ultrapasse
    return pd.DataFrame(tracks_data[:100], columns=["Música", "Artista", "Álbum", "Artista do Álbum", "Popularidade"])

# Função para pegar as top tracks dos últimos 6 meses
def get_top_tracks_6_months(access_token):
    tracks_data = []
    url = "https://api.spotify.com/v1/me/top/tracks?time_range=medium_term&limit=50"  # Últimos 6 meses
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    results = requests.get(url, headers=headers).json()

    while results:
        # Adiciona as músicas retornadas pela API
        tracks_data.extend([[
            track["name"], 
            track["artists"][0]["name"], 
            track["album"]["name"], 
            track["album"]["artists"][0]["name"], 
            track["popularity"]
        ] for track in results["items"]])

        # Verifica se há mais músicas para pegar
        if len(tracks_data) >= 100:
            break

        # Se houver mais músicas, continua a busca com a próxima página
        url = results.get("next")
        if url:
            results = requests.get(url, headers=headers).json()
        else:
            break

    # Limita a 400 músicas, caso a contagem ultrapasse
    return pd.DataFrame(tracks_data[:100], columns=["Música", "Artista", "Álbum", "Artista do Álbum", "Popularidade"])

# Função para obter o histórico de reprodução do usuário
def get_recently_played(access_token):
    url = "https://api.spotify.com/v1/me/player/recently-played?limit=50"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 401:  # Token expirado
        st.error("❌ Token expirado! Tente reiniciar o token.")
        return pd.DataFrame()
    
    data = response.json()

    if "items" not in data:
        st.warning("❌ Não foi possível obter o histórico de reprodução.")
        return pd.DataFrame()

    # Extrai as informações relevantes
    tracks_data = []
    for item in data["items"]:
        track = item["track"]
        played_at = item["played_at"]
        track_name = track["name"]
        artist_name = track["artists"][0]["name"]
        album_name = track["album"]["name"]
        popularity = track["popularity"]

        tracks_data.append([played_at, track_name, artist_name, album_name, popularity])

    # Converte para DataFrame
    df_history = pd.DataFrame(tracks_data, columns=["Tocada Em", "Música", "Artista", "Álbum", "Popularidade"])
    
    # Converte a coluna de data para um formato legível
    df_history["Tocada Em"] = pd.to_datetime(df_history["Tocada Em"]).dt.strftime("%d/%m/%Y %H:%M:%S")

    return df_history

def get_artists_with_most_tracks(tracks):
    artists = [track['track']['artists'][0]['name'] for track in tracks if track['track']['artists']]
    artist_counts = Counter(artists)
    return artist_counts

# Função para obter os gêneros dos artistas mais ouvidos
def get_top_genres(access_token):
    url = "https://api.spotify.com/v1/me/top/artists?limit=50&time_range=medium_term"  # Últimos 6 meses
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers).json()

    genre_counts = {}

    if "items" in response:
        for artist in response["items"]:
            for genre in artist["genres"]:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1

    # Transforma em DataFrame
    df_genres = pd.DataFrame(genre_counts.items(), columns=["Gênero", "Frequência"])
    df_genres = df_genres.sort_values(by="Frequência", ascending=False)

    return df_genres

def plot_popularity(tracks):
    popularities = [track['track']['popularity'] for track in tracks]
    track_names = [track['track']['name'] for track in tracks]
    
    # Criar gráfico
    plt.figure(figsize=(10, 6))
    sns.barplot(x=track_names, y=popularities, palette='viridis')
    plt.xticks(rotation=90)
    plt.xlabel('Música')
    plt.ylabel('Popularidade')
    plt.title('Popularidade das 100 músicas mais ouvidas')
    plt.tight_layout()
    st.pyplot(plt)

# Streamlit Interface
st.title("Spotify Authentication and Playlists")

# Menu de navegação
st.sidebar.title("Navegação")
option = st.sidebar.radio("Escolha uma opção", ("📋 Informações do Usuário", 
                                                "🎧 Playlists", 
                                                "🔥 Mais ouvidas das últimas 4 semanas", 
                                                "🔄 Mais ouvidas dos últimos 6 meses",
                                                "📱 Histórico de músicas ouvidas",
                                                "🎵 Gêneros mais ouvidos"))

# Usuário selecionado
user = st.selectbox("👤 Escolha o usuário", ["duduguima", 
                                             "smokyarts"])

# Atualiza o token quando o usuário muda
if "current_user" not in st.session_state or st.session_state["current_user"] != user:
    st.session_state["current_user"] = user
    st.session_state["access_token"] = refresh_access_token(user)
    st.cache_data.clear()  # Limpa o cache para garantir atualização
    st.rerun()

# Botão para reiniciar o token
if st.button("🔄 Reiniciar Token"):
    new_access_token = refresh_access_token(user)
    if new_access_token:
        st.session_state["access_token"] = new_access_token
        st.rerun()  # Atualiza a página

# Obtendo o token válido
access_token = get_valid_token(user)

if option == "📋 Informações do Usuário":
    st.header("Informações do Usuário")
    user_info = get_user_info(access_token)

    if user_info:
        st.write(f"Nome: {user_info['display_name']}")
        st.write(f"Email: {user_info['email']}")
        st.image(user_info['images'][0]['url'] if user_info['images'] else None)
    else:
        st.error("Erro ao acessar as informações do usuário")

elif option == "🎧 Playlists":
    st.header("Suas Playlists")
    playlists = get_user_playlists(access_token)

    if playlists:
        playlist_names = [playlist['name'] for playlist in playlists]
        selected_playlist_name = st.selectbox("Escolha uma playlist", playlist_names)

        selected_playlist = next(playlist for playlist in playlists if playlist['name'] == selected_playlist_name)
        st.write(f"Você selecionou a playlist: {selected_playlist_name}")

        try:
            # Tentamos obter as faixas da playlist
            tracks = get_playlist_tracks(access_token, selected_playlist['id'])

            if tracks:
                # DataFrame das faixas
                df = get_tracks_dataframe(tracks)
                st.subheader(f"Total de faixas na playlist: {len(df)}")
                st.dataframe(df)  # Exibe o DataFrame com as faixas

                # Artistas com mais músicas
                artist_counts = get_artists_with_most_tracks(tracks)
                artist_df = pd.DataFrame(artist_counts.items(), columns=['Artista', 'Músicas'])
                artist_df = artist_df.sort_values(by='Músicas', ascending=False)
                st.subheader("Artistas com mais músicas na playlist:")
                st.dataframe(artist_df)

                # Álbuns com mais músicas
                album_df = get_albums_with_most_tracks(tracks)
                st.subheader("Álbuns com mais músicas na playlist:")
                st.dataframe(album_df)
            else:
                st.error("Erro ao carregar as faixas da playlist")
        except TypeError:
            st.error("Não é possível analisar essa playlist. Tente selecionar outra.")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {str(e)}")
    else:
        st.error("Você não tem playlists.")

elif option == "🔥 Mais ouvidas das últimas 4 semanas":
    top_tracks_df = get_top_tracks(access_token)
    #st.dataframe(top_tracks_df)  # Exibe o DataFrame no Streamlit

    if top_tracks_df.empty:
        st.warning("❌ Nenhuma música encontrada no seu histórico!")
    else:
        st.dataframe(top_tracks_df)

        fig_top_tracks = px.bar(top_tracks_df, x="Música", y="Popularidade",
                                title="Top 100 Músicas Mais Ouvidas (4 Semanas)", text_auto=True, color="Popularidade",)

        # Adiciona a rotação de 45 graus no eixo X
        fig_top_tracks.update_layout(
            xaxis=dict(
                tickangle=45  # Rotação de 45 graus nos rótulos do eixo X
            )
        )

        st.plotly_chart(fig_top_tracks)

# Aba para as Top Tracks dos Últimos 6 Meses
elif option == "🔄 Mais ouvidas dos últimos 6 meses":
    st.header("Top Músicas dos Últimos 6 Meses")
    
    # Obtemos os dados das top tracks
    df_top_tracks_6m = get_top_tracks_6_months(access_token)

    if df_top_tracks_6m.empty:
        st.warning("❌ Nenhuma música encontrada no seu histórico dos últimos 6 meses!")
    else:
        # Exibe o DataFrame com as músicas
        st.dataframe(df_top_tracks_6m)

        # Cria o gráfico de barras de popularidade das músicas
        fig_top_tracks_6m = px.bar(df_top_tracks_6m, 
                                   x="Música", 
                                   y="Popularidade",
                                   title="Top 100 Músicas Mais Ouvidas nos Últimos 6 Meses", 
                                   text_auto=True, 
                                   color="Popularidade")
        
        # Adiciona a rotação de 45 graus no eixo X para melhorar a leitura
        fig_top_tracks_6m.update_layout(
            xaxis=dict(
                tickangle=45  # Rotação de 45 graus nos rótulos do eixo X
            )
        )
        
        # Exibe o gráfico
        st.plotly_chart(fig_top_tracks_6m)

# Aba para Histórico das Últimas Músicas Ouvidas
elif option == "📱 Histórico de músicas ouvidas":
    st.header("📜 Histórico de Reprodução")

    access_token = st.session_state.get("access_token")

    if not access_token:
        st.error("❌ Token de acesso não encontrado. Tente reiniciar o token.")
    else:
        df_history = get_recently_played(access_token)

        if df_history.empty:
            st.warning("❌ Nenhuma reprodução encontrada recentemente!")
        else:
            # Exibe a tabela do histórico
            st.dataframe(df_history)

            # Cria um gráfico de barras com os artistas mais tocados
            artist_counts = df_history["Artista"].value_counts().reset_index()
            artist_counts.columns = ["Artista", "Quantidade"]

            fig_history = px.bar(artist_counts, x="Artista", y="Quantidade",
                                 title="Artistas mais tocados recentemente",
                                 text_auto=True, color="Quantidade")

            st.plotly_chart(fig_history)

# Nova aba no Streamlit
elif option == "🎵 Gêneros mais ouvidos":
    st.header("🎵 Meus Gêneros Mais Ouvidos")

    # Obtém os gêneros mais ouvidos
    df_genres = get_top_genres(st.session_state.get("access_token"))

    if df_genres.empty:
        st.warning("❌ Nenhum gênero encontrado nos últimos 6 meses!")
    else:
        # Exibe a tabela dos gêneros mais ouvidos
        st.dataframe(df_genres)

        fig_history = px.bar(df_genres, x="Gênero", y="Frequência",
                        title="Frequência de gêneros",
                        text_auto=True, color="Frequência")

        st.plotly_chart(fig_history)


