import spotipy
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st
import os
import urllib.parse
import pandas as pd
import requests

# Configurações do seu app no Spotify
CLIENT_ID = st.secrets["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = st.secrets["SPOTIFY_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["SPOTIFY_REDIRECT_URI"]  # Ajuste conforme seu domínio público
SCOPE = "user-read-private user-read-email"  # Defina os escopos necessários

# URL de autorização do Spotify
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_ME = "https://api.spotify.com/v1/me"

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
    st.write("Usuário autenticado:", user_info)

if access_token:
    st.set_page_config(page_title="🎵 Analisador de Spotify", layout="wide")
    # Autenticação
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                client_secret=CLIENT_SECRET,
                                                redirect_uri=REDIRECT_URI,
                                                scope=SCOPE))

    # Função para buscar playlists do usuário
    def get_user_playlists():
        playlists = sp.current_user_playlists()
        return {p["name"]: p["id"] for p in playlists["items"]}

    # Função para buscar músicas e álbuns de uma playlist
    def get_playlist_tracks(playlist_id):
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
    def get_top_tracks():
        tracks_data = []
        results = sp.current_user_top_tracks(limit=50, time_range="short_term")  # Últimas 4 semanas
        
        while results:
            # Adiciona as músicas retornadas pela API
            tracks_data.extend([[track["name"], track["artists"][0]["name"], track["album"]["name"], 
                                track["album"]["artists"][0]["name"], track["popularity"]]
                                for track in results["items"]])
            
            # Verifica se há mais músicas para pegar
            if len(tracks_data) >= 500:
                break
            
            # Se houver mais músicas, continua a busca com a próxima página
            results = sp.next(results) if results["next"] else None
        
        # Limita a 500 músicas, caso a contagem ultrapasse
        return pd.DataFrame(tracks_data[:500], columns=["Música", "Artista", "Álbum", "Artista do Álbum", "Popularidade"])

    # Função para buscar as músicas mais ouvidas nos últimos 6 meses (agora com até 400 músicas)
    def get_top_tracks_6_months():
        tracks_data = []
        results = sp.current_user_top_tracks(limit=50, time_range="medium_term")  # Últimos 6 meses
        
        while results:
            # Adiciona as músicas retornadas pela API
            tracks_data.extend([[track["name"], track["artists"][0]["name"], track["album"]["name"], 
                                track["album"]["artists"][0]["name"], track["popularity"]]
                                for track in results["items"]])
            
            # Verifica se há mais músicas para pegar
            if len(tracks_data) >= 400:
                break
            
            # Se houver mais músicas, continua a busca com a próxima página
            results = sp.next(results) if results["next"] else None
        
        # Limita a 400 músicas, caso a contagem ultrapasse
        return pd.DataFrame(tracks_data[:400], columns=["Música", "Artista", "Álbum", "Artista do Álbum", "Popularidade"])

    # Função para buscar as músicas mais ouvidas no longo prazo
    def get_top_tracks_long_term():
        tracks_data = []
        results = sp.current_user_top_tracks(limit=50, time_range="long_term")  # Histórico completo (todas as músicas)
        
        while results:
            # Adiciona as músicas retornadas pela API
            tracks_data.extend([[track["name"], track["artists"][0]["name"], track["album"]["name"], 
                                track["album"]["artists"][0]["name"], track["popularity"]]
                                for track in results["items"]])
            
            # Verifica se há mais músicas para pegar
            if len(tracks_data) >= 400:
                break
            
            # Se houver mais músicas, continua a busca com a próxima página
            results = sp.next(results) if results["next"] else None
        
        # Limita a 400 músicas, caso a contagem ultrapasse
        return pd.DataFrame(tracks_data[:400], columns=["Música", "Artista", "Álbum", "Artista do Álbum", "Popularidade"])

    # Configuração do Streamlit
    st.title("🎵 Analisador de Spotify - Playlists & Músicas Mais Ouvidas")

    st.write("Clique no botão abaixo para autenticar outro usuário:")

    if st.button("🔑 Fazer login no Spotify"):
        auth_url = auth_manager.get_authorize_url()
        st.markdown(f"[Clique aqui para autenticar]( {auth_url} )", unsafe_allow_html=True)

    # Verificar se o token foi gerado e usuário está autenticado
    if sp.current_user():
        user_info = sp.current_user()
        st.success(f"✅ Logado como: {user_info['display_name']}")

        # Criar uma caixa de seleção de playlist fora das abas para que fique visível em todas as abas
        playlists = get_user_playlists()
        playlist_name = st.selectbox("Selecione uma playlist:", list(playlists.keys()))

        # Criar abas para visualizações
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🎤 Top 5 Artistas", 
                                                "📀 Top 5 Álbuns", 
                                                "🔥 Mais Ouvidas (Últimas 4 Semanas)", 
                                                "🔄 Mais Ouvidas (Últimos 6 Meses)", 
                                                "📊 Cruzamento Playlist X Mais Ouvidas (Últimas 4 Semanas)", 
                                                "🎨 Músicas mais ouvidas da conta"])

        # 🔹 Aba 1 - Análise de uma Playlist (Top Artistas)
        with tab1:
            st.subheader("🎤 Top 5 Artistas com Mais Músicas na Playlist")
            
            if playlist_name:
                playlist_id = playlists[playlist_name]
                df_tracks = get_playlist_tracks(playlist_id)

                if df_tracks.empty:
                    st.warning("❌ Essa playlist não contém músicas!")
                else:
                    artist_counts = df_tracks["Artista"].value_counts().reset_index()
                    artist_counts.columns = ["Artista", "Quantidade"]
                    top_5_artists = artist_counts.head(5)

                    st.dataframe(top_5_artists)

#     # 🔹 Aba 2 - Análise de uma Playlist (Top Álbuns com Artista)
#     with tab2:
#         st.subheader("📀 Top 5 Álbuns com Mais Músicas na Playlist")
        
#         if playlist_name:
#             playlist_id = playlists[playlist_name]
#             df_tracks = get_playlist_tracks(playlist_id)

#             if df_tracks.empty:
#                 st.warning("❌ Essa playlist não contém músicas!")
#             else:
#                 # Contar a quantidade de músicas por álbum e artista
#                 album_counts = df_tracks.groupby(["Álbum", "Artista do Álbum"]).size().reset_index(name="Quantidade")
                
#                 # Ordenar para pegar os 5 álbuns mais populares
#                 top_5_albums = album_counts.sort_values(by="Quantidade", ascending=False).head(5)

#                 st.dataframe(top_5_albums)

#     # 🔹 Aba 3 - Músicas Mais Ouvidas (Últimas 4 Semanas)
#     with tab3:
#         st.subheader("🔥 Suas Músicas Mais Ouvidas nas Últimas 4 Semanas")

#         df_top_tracks = get_top_tracks()

#         if df_top_tracks.empty:
#             st.warning("❌ Nenhuma música encontrada no seu histórico!")
#         else:
#             st.dataframe(df_top_tracks)

#             fig_top_tracks = px.bar(df_top_tracks, x="Música", y="Popularidade",
#                                     title="Top 10 Músicas Mais Ouvidas (4 Semanas)", text_auto=True, color="Popularidade",)

#             # Adiciona a rotação de 45 graus no eixo X
#             fig_top_tracks.update_layout(
#                 xaxis=dict(
#                     tickangle=45  # Rotação de 45 graus nos rótulos do eixo X
#                 )
#             )

#             st.plotly_chart(fig_top_tracks)


#     # 🔹 Aba 4 - Músicas Mais Ouvidas (Últimos 6 Meses)
#     with tab4:
#         st.subheader("🔄 Suas Músicas Mais Ouvidas nos Últimos 6 Meses")

#         df_top_tracks_6m = get_top_tracks_6_months()

#         if df_top_tracks_6m.empty:
#             st.warning("❌ Nenhuma música encontrada no seu histórico!")
#         else:
#             st.dataframe(df_top_tracks_6m)

#             fig_top_tracks_6m = px.bar(df_top_tracks_6m, x="Música", y="Popularidade",
#                                     title="Top 10 Músicas Mais Ouvidas (6 Meses)", text_auto=True, color="Popularidade")
#              # Adiciona a rotação de 45 graus no eixo X para melhorar a leitura
#             fig_top_tracks_6m.update_layout(
#                 xaxis=dict(
#                     tickangle=45  # Rotação de 45 graus nos rótulos do eixo X
#                 )
#             )
            
#             st.plotly_chart(fig_top_tracks_6m)

#     # 🔹 Aba 5 - Cruzamento entre Músicas Mais Ouvidas (Últimos 6 Meses) e Playlist
#     with tab5:
#         st.subheader("🎧 Cruzamento de Músicas Mais Ouvidas (Últimos 6 Meses) com Playlist")

#         if playlist_name:
#             playlist_id = playlists[playlist_name]
            
#             # Obter as músicas mais ouvidas dos últimos 6 meses
#             df_top_tracks_6m = get_top_tracks()
            
#             # Obter as músicas da playlist
#             df_playlist_tracks = get_playlist_tracks(playlist_id)

#             if df_top_tracks_6m.empty or df_playlist_tracks.empty:
#                 st.warning("❌ Nenhuma música encontrada no seu histórico ou na playlist!")
#             else:
#                 # Cruzando as músicas mais ouvidas com as da playlist
#                 # Verificar as músicas que estão nas duas listas (usando o nome da música e do artista)
#                 merged_df = pd.merge(df_top_tracks_6m, df_playlist_tracks, on=["Música", "Artista"], how="inner")
#                 merged_df = merged_df.drop(['Álbum_x', 'Artista do Álbum_x'], axis=1)
#                 merged_df = merged_df.rename(columns={'Álbum_y': 'Álbum',
#                                                     'Artista do Álbum_y': 'Artista do Álbum'})
#                 merged_df = merged_df.drop_duplicates('Música')
                
#                 if merged_df.empty:
#                     st.warning("❌ Nenhuma música encontrada em ambas as listas!")
#                 else:
#                     st.subheader("🔍 Músicas em Comum")
#                     st.dataframe(merged_df)
                    
#                     # Exibir um gráfico com as músicas em comum
#                     fig_merged = px.bar(merged_df, x="Música", y="Popularidade", color="Popularidade",
#                                         title="Músicas Mais Ouvidas nos Últimos 6 Meses que Estão na Playlist",
#                                         text_auto=True)
                    
#                     # Adiciona a rotação de 45 graus no eixo X para melhorar a leitura
#                     fig_merged.update_layout(
#                         xaxis=dict(
#                             tickangle=45  # Rotação de 45 graus nos rótulos do eixo X
#                         )
#                     )

#                     st.plotly_chart(fig_merged)

#     # 🔹 Aba 6 - Músicas Mais Ouvidas no Longo Prazo (Long Term)
#     with tab6:
#         st.subheader("🌟 Suas Músicas Mais Ouvidas de Sempre")

#         df_top_tracks_long_term = get_top_tracks_long_term()

#         if df_top_tracks_long_term.empty:
#             st.warning("❌ Nenhuma música encontrada no seu histórico!")
#         else:
#             df_top_tracks_long_term = df_top_tracks_long_term.drop_duplicates('Música')
#             st.dataframe(df_top_tracks_long_term)

#             fig_top_tracks_long_term = px.bar(df_top_tracks_long_term, x="Música", y="Popularidade",
#                                             title="Top 10 Músicas Mais Ouvidas de Sempre", text_auto=True, color="Popularidade")
            
#             # Adiciona a rotação de 45 graus no eixo X para melhorar a leitura
#             fig_top_tracks_long_term.update_layout(
#                 xaxis=dict(
#                     tickangle=45  # Rotação de 45 graus nos rótulos do eixo X
#                 )
#             )

#             st.plotly_chart(fig_top_tracks_long_term)