import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add extra_streamlit_components import and global cookie manager
if "import extra_streamlit_components" not in content:
    content = content.replace(
        "import hashlib",
        "import hashlib\nimport extra_streamlit_components as stx\nfrom datetime import datetime, timedelta\n\n@st.cache_resource\ndef get_cookie_manager():\n    return stx.CookieManager()\ncookie_manager = get_cookie_manager()\n"
    )

# 2. Rewrite render_login
old_render_login = """def render_login():
    # Injetar background azul para a tela de login
    st.markdown(\"\"\"
        <style>
            .stApp { background-color: var(--crivo-blue) !important; }
            .premium-card { background-color: rgba(255, 255, 255, 0.95); }
        </style>
    \"\"\", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        try:
            st.image("assets/logo.png", use_container_width=True)
        except:
            st.markdown(f"<h1 style='text-align: center; color: white;'>CRIVO <br><span style='font-size:16px; color:var(--accent);'>CAR STUDIO</span></h1>", unsafe_allow_html=True)
            
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        
        if st.button("Entrar", type="primary", use_container_width=True):
            db = next(get_db())
            user = db.query(Usuario).filter(Usuario.username == username).first()
            if user and user.password_hash == hash_password(password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = user.username
                st.session_state['user_role'] = user.role
                st.session_state['permissoes'] = getattr(user, 'permissoes', 'todas')
                st.session_state['pode_excluir'] = getattr(user, 'pode_excluir', False) or user.role == "admin"
                from db_config import registrar_log
                registrar_log("Fez login no sistema")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")"""

new_render_login = """def render_login():
    # Injetar background azul para a tela de login
    st.markdown(\"\"\"
        <style>
            .stApp { background-color: var(--crivo-blue) !important; }
            .premium-card { background-color: rgba(255, 255, 255, 0.95); }
        </style>
    \"\"\", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        try:
            st.image("assets/logo.png", use_container_width=True)
        except:
            st.markdown(f"<h1 style='text-align: center; color: white;'>CRIVO <br><span style='font-size:16px; color:var(--accent);'>CAR STUDIO</span></h1>", unsafe_allow_html=True)
            
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        
        if st.button("Entrar", type="primary", use_container_width=True):
            db = next(get_db())
            user = db.query(Usuario).filter(Usuario.username == username).first()
            if user:
                agora = datetime.now()
                # Verifica bloqueio
                if user.bloqueado_ate:
                    try:
                        bloq_dt = datetime.fromisoformat(user.bloqueado_ate)
                        if agora < bloq_dt:
                            minutos_restantes = int((bloq_dt - agora).total_seconds() / 60) + 1
                            st.error(f"Conta bloqueada por segurança. Tente novamente em {minutos_restantes} minuto(s).")
                            return
                        else:
                            user.bloqueado_ate = None
                            user.tentativas_falhas = 0
                            db.commit()
                    except: pass
                
                # Check password
                if user.password_hash == hash_password(password):
                    user.tentativas_falhas = 0
                    user.bloqueado_ate = None
                    db.commit()
                    
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user.username
                    st.session_state['user_role'] = user.role
                    st.session_state['permissoes'] = getattr(user, 'permissoes', 'todas')
                    st.session_state['pode_excluir'] = getattr(user, 'pode_excluir', False) or user.role == "admin"
                    from db_config import registrar_log
                    registrar_log("Fez login no sistema")
                    
                    # Salva cookie por 30 dias
                    cookie_manager.set('auth_user', user.username, max_age=86400 * 30, key="set_auth")
                    st.rerun()
                else:
                    falhas = getattr(user, 'tentativas_falhas', 0) + 1
                    user.tentativas_falhas = falhas
                    
                    if falhas >= 5:
                        tempo_bloq = 15 if falhas <= 6 else 60
                        user.bloqueado_ate = (agora + timedelta(minutes=tempo_bloq)).isoformat()
                        db.commit()
                        st.error(f"Muitas tentativas! Acesso bloqueado por {tempo_bloq} minutos.")
                    else:
                        db.commit()
                        st.error(f"Senha incorreta! Restam {5 - falhas} tentativas antes do bloqueio.")
            else:
                st.error("Usuário ou senha inválidos.")"""
content = re.sub(
    r'def render_login\(\):.*?st\.error\("Usurio ou senha invlidos\."\)|def render_login\(\):.*?st\.error\("Usuário ou senha inválidos\."\)',
    new_render_login,
    content,
    flags=re.DOTALL
)


# 3. Update main() to check cookies first
old_main = """def main():
    if not st.session_state['logged_in']:
        render_login()
        return"""

new_main = """def main():
    # Tenta puxar o login do cookie antes de barrar
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
                st.rerun()
                
    if not st.session_state.get('logged_in'):
        render_login()
        return"""

if "auth_cookie = cookie_manager.get('auth_user')" not in content:
    content = content.replace(old_main, new_main)

# 4. Update Logout
old_logout = """        if st.sidebar.button("Sair"):
            st.session_state['logged_in'] = False
            st.session_state['user_role'] = None
            st.rerun()"""

new_logout = """        if st.sidebar.button("Sair"):
            cookie_manager.delete('auth_user', key="del_auth")
            st.session_state['logged_in'] = False
            st.session_state['user_role'] = None
            st.rerun()"""

content = content.replace(old_logout, new_logout)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Applied Auth Patch!')
