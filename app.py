import streamlit as st
import requests
import urllib.parse

# Configurações do seu app no Spotify
CLIENT_ID = st.secrets['SPOTIFY_CLIENT_ID']
CLIENT_SECRET = st.secrets['SPOTIFY_CLIENT_SECRET']
REDIRECT_URI = st.secrets['SPOTIFY_REDIRECT_URI'] # Ajuste conforme seu domínio público
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