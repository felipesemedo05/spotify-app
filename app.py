import streamlit as st

# Dicionário com as informações dos usuários
users_info = {
    'client_id_duduguima': {
        'client_id': 'duduguima_id',
        'client_secret': 'duduguima_secret',
        'email': 'duduguima@example.com',
        'nome': 'Duduguima'
    },
    'client_id_smokyarts': {
        'client_id': 'smokyarts_id',
        'client_secret': 'smokyarts_secret',
        'email': 'smokyarts@example.com',
        'nome': 'Smoky Arts'
    }
}

# Interface do usuário
st.title('Selecione as Informações do Usuário')

# Seleção do usuário
selected_user = st.selectbox(
    'Escolha o usuário para exibir as informações:',
    ['client_id_duduguima', 'client_id_smokyarts']
)

# Exibir as informações do usuário selecionado
user_info = users_info[selected_user]

st.subheader(f'Informações de {user_info["nome"]}')
st.write(f'**ID do Cliente:** {user_info["client_id"]}')
st.write(f'**Segredo do Cliente:** {user_info["client_secret"]}')
st.write(f'**E-mail:** {user_info["email"]}')