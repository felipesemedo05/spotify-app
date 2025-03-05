import streamlit as st
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import plotly.express as px

# Interface Streamlit
st.title('Spotify Analysis')

# Seleção do usuário
selected_user = st.selectbox('Escolha o cliente para autenticar:',
                             ['duduguima', 'smokyarts'])
