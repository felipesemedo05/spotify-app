import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Acessando as credenciais dos clientes a partir de st.secrets
CLIENTS = {
    'duduguima': {
        'client_id': st.secrets["client_id_duduguima"],
        'client_secret': st.secrets["client_secret_duduguima"],
        'redirect_uri': st.secrets["redirect_uri"]
    },
    'smokyarts': {
        'client_id': st.secrets["client_id_smokyarts"],
        'client_secret': st.secrets["client_secret_smokyarts"],
        'redirect_uri': st.secrets["redirect_uri"]
    }
}

# Escopo de permissões do Spotify
SCOPE = "user-library-read user-read-email"

# Função para autenticar no Spotify
def authenticate_spotify(client_id, client_secret, redirect_uri):
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                   client_secret=client_secret,
                                                   redirect_uri=redirect_uri,
                                                   scope=SCOPE))
    return sp

# Interface Streamlit
st.title('Spotify Login e Informações do Usuário')

# Seleção do usuário
selected_user = st.selectbox('Escolha o cliente para autenticar:',
                             ['duduguima', 'smokyarts'])

# Obter as credenciais do cliente selecionado
client_info = CLIENTS[selected_user]

# Iniciar a autenticação
if 'token_info' not in st.session_state:
    # Não temos o token, então exibimos o botão de login
    auth_url = SpotifyOAuth(client_id=client_info['client_id'],
                             client_secret=client_info['client_secret'],
                             redirect_uri=client_info['redirect_uri'],
                             scope=SCOPE).get_authorize_url()
    st.write(f"Para acessar as informações de {selected_user}, faça login no Spotify:")
    st.markdown(f"[Clique aqui para login]({auth_url})")
else:
    # Se o token existe, autenticamos automaticamente
    sp = authenticate_spotify(client_info['client_id'],
                               client_info['client_secret'],
                               client_info['redirect_uri'])
    
    try:
        # Tentamos pegar as informações do usuário
        user_info = sp.current_user()
        st.subheader(f'Bem-vindo, {user_info["display_name"]}!')
        st.write(f'E-mail: {user_info["email"]}')
        st.write(f'ID de Usuário: {user_info["id"]}')
        st.write(f'País: {user_info["country"]}')
        
        # Mostrar imagem do usuário
        if user_info["images"]:
            st.image(user_info["images"][0]["url"], width=100)
    except spotipy.exceptions.SpotifyException as e:
        st.error(f"Erro ao acessar as informações do usuário: {e}")

# Caso o usuário já tenha feito login, mostramos uma mensagem
if 'token_info' in st.session_state:
    st.write(f"Você já está autenticado como {selected_user}.")
