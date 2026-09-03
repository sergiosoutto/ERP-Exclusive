import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove extra_streamlit_components import and cookie_manager initialization
content = re.sub(r'import extra_streamlit_components as stx\n?', '', content)
content = re.sub(r'# Suppress CachedWidgetWarning.*?cookie_manager = get_cookie_manager\(\)', '', content, flags=re.DOTALL)
content = re.sub(r'cookie_manager = stx\.CookieManager\(.*?\)', '', content)
content = re.sub(r'@st\.cache_resource\(.*?\)\ndef get_cookie_manager\(\):\n    return stx\.CookieManager\(.*?\)\n\ncookie_manager = get_cookie_manager\(\)', '', content, flags=re.DOTALL)

# 2. Replace auth_cookie = cookie_manager.get('auth_user') with query params
old_login_check = """    # Tenta puxar o login do cookie antes de barrar
    if not st.session_state.get('logged_in'):
        auth_cookie = cookie_manager.get('auth_user')
        if auth_cookie:
            db = next(get_db())
            user = db.query(Usuario).filter(Usuario.username == auth_cookie).first()
            if user:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user.username
                st.session_state['user_role'] = user.role
                st.session_state['permissoes'] = getattr(user, 'permissoes', 'todas')
                st.session_state['pode_excluir'] = getattr(user, 'pode_excluir', False) or user.role == "admin"
                st.rerun()"""

new_login_check = """    # Recupera sessao pelos parametros da URL para sobreviver a inatividade
    if not st.session_state.get('logged_in'):
        auth_token = st.query_params.get('auth_user', None)
        if auth_token:
            db = next(get_db())
            user = db.query(Usuario).filter(Usuario.username == auth_token).first()
            if user:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user.username
                st.session_state['user_role'] = user.role
                st.session_state['permissoes'] = getattr(user, 'permissoes', 'todas')
                st.session_state['pode_excluir'] = getattr(user, 'pode_excluir', False) or user.role == "admin"
                # Não da rerun aqui senao entra em loop infinito, apenas aceita o login"""
                
content = content.replace(old_login_check, new_login_check)

# 3. Replace setting the cookie in render_login
old_set_cookie = """                        # Salva o cookie com durao de 30 dias para persistir aps inatividade
                        cookie_manager.set('auth_user', username, expires_at=datetime.now() + timedelta(days=30))
                        
                        st.rerun()"""
new_set_cookie = """                        # Salva na URL para sobreviver a inatividade na mesma aba
                        st.query_params['auth_user'] = username
                        
                        st.rerun()"""
content = content.replace(old_set_cookie, new_set_cookie)

# 4. Replace deleting the cookie in render_login
old_del_cookie = """        if st.sidebar.button(" Sair do Sistema"):
            st.session_state.clear()
            cookie_manager.delete('auth_user')
            st.rerun()"""
new_del_cookie = """        if st.sidebar.button(" Sair do Sistema"):
            st.session_state.clear()
            st.query_params.clear()
            st.rerun()"""
content = content.replace(old_del_cookie, new_del_cookie)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Stripped CookieManager entirely")
