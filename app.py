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


# Função para pegar o histórico das últimas músicas ouvidas
def get_recently_played_tracks(access_token, limit=50):
    url = f"https://api.spotify.com/v1/me/player/recently-played?limit={limit}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    results = requests.get(url, headers=headers).json()

    tracks_data = []
    for item in results["items"]:
        track = item["track"]
        tracks_data.append([
            track["name"], 
            track["artists"][0]["name"], 
            track["album"]["name"], 
            track["album"]["artists"][0]["name"], 
            track["played_at"]
        ])

    return pd.DataFrame(tracks_data, columns=["Música", "Artista", "Álbum", "Artista do Álbum", "Data de Reprodução"])

def get_artists_with_most_tracks(tracks):
    artists = [track['track']['artists'][0]['name'] for track in tracks if track['track']['artists']]
    artist_counts = Counter(artists)
    return artist_counts

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
                                                "📱 Histórico de músicas ouvidas"))

# Usuário selecionado
user = st.selectbox("Usuário", ["duduguima", "smokyarts"])

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
    st.header("Histórico das Últimas Músicas Ouvidas")
    
    # Obtemos os dados do histórico de músicas
    df_recent_tracks = get_recently_played_tracks(access_token)

    if df_recent_tracks.empty:
        st.warning("❌ Nenhuma música encontrada no seu histórico recente!")
    else:
        # Exibe o DataFrame com as músicas recentes
        st.dataframe(df_recent_tracks)

        # Cria o gráfico de barras para popularidade das músicas ouvidas
        fig_recent_tracks = px.bar(df_recent_tracks, 
                                   x="Música", 
                                   title="Últimas Músicas Ouvidas", 
                                   text_auto=True)

        # Adiciona a rotação de 45 graus no eixo X para melhorar a leitura
        fig_recent_tracks.update_layout(
            xaxis=dict(
                tickangle=45  # Rotação de 45 graus nos rótulos do eixo X
            )
        )

        # Exibe o gráfico
        st.plotly_chart(fig_recent_tracks)


