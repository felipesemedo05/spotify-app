import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import webbrowser

# Configurações das credenciais para cada usuário
USERS = {
    "duduguima": {
        "CLIENT_ID": st.secrets['client_id_duduguima'],
        "CLIENT_SECRET": st.secrets['client_secret_duduguima'],
        "REDIRECT_URI": "https://spotify-app-qtnrmxu4qmnesgsgoyvvxg.streamlit.app/callback",
    },
    "smokyarts": {
        "CLIENT_ID": st.secrets['client_id_smokyarts'],
        "CLIENT_SECRET": st.secrets['client_secret_smokyarts'],
        "REDIRECT_URI": "https://spotify-app-qtnrmxu4qmnesgsgoyvvxg.streamlit.app/callback",
    },
}

# Definir escopos necessários
SCOPE = "user-library-read"

# Criar interface do Streamlit
st.title("Spotify API - Seleção de Usuário")

# Seleção do usuário
selected_user = st.selectbox("Selecione um usuário:", list(USERS.keys()))

if st.button("Iniciar Sessão"):
    user_data = USERS[selected_user]
    auth_manager = SpotifyOAuth(
        client_id=user_data["CLIENT_ID"],
        client_secret=user_data["CLIENT_SECRET"],
        redirect_uri=user_data["REDIRECT_URI"],
        scope=SCOPE,
    )
    webbrowser.open(auth_manager.get_authorize_url())
    
    token_info = auth_manager.get_access_token(as_dict=False)
    sp = spotipy.Spotify(auth=token_info)
    
    # Obter informações do usuário
    user_profile = sp.current_user()
    st.write("### Perfil do Usuário:")
    st.write(f"**Nome:** {user_profile['display_name']}")
    st.write(f"**ID do Usuário:** {user_profile['id']}")
    if user_profile['images']:
        st.image(user_profile['images'][0]['url'], width=150)
    
    # Exibir músicas salvas do usuário
    st.write("### Músicas Salvas:")
    saved_tracks = sp.current_user_saved_tracks(limit=5)
    for idx, item in enumerate(saved_tracks['items']):
        track = item['track']
        st.write(f"{idx + 1}. {track['name']} - {track['artists'][0]['name']}")

