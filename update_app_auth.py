import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update cache buster to v5 to force migration
content = content.replace('def initialize_database_v4():', 'def initialize_database_v5():')
content = content.replace('initialize_database_v4()', 'initialize_database_v5()')

# 2. Add extra_streamlit_components and login logic
new_login_logic = """
from db_config import get_db, Usuario, hash_password
from datetime import datetime, timedelta
import extra_streamlit_components as stx

@st.cache_resource
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

def login():
    # Esconder sidebar durante login
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(f"<h1 style='text-align: center; color: white;'>CRIVO</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: rgba(255,255,255,0.7);'>Acesso ao Sistema</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            st.markdown("<br>", unsafe_allow_html=True)
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            
            if st.button("Entrar", type="primary", use_container_width=True):
                db = next(get_db())
                user = db.query(Usuario).filter(Usuario.username == username).first()
                
                if user:
                    # Rate Limiting Logic
                    agora = datetime.now()
                    
                    if user.bloqueado_ate:
                        try:
                            bloq_dt = datetime.fromisoformat(user.bloqueado_ate)
                            if agora < bloq_dt:
                                minutos_restantes = int((bloq_dt - agora).total_seconds() / 60)
                                st.error(f"Conta bloqueada por segurança. Tente novamente em {minutos_restantes} minuto(s).")
                                return
                            else:
                                # Tempo de bloqueio expirou, limpar
                                user.bloqueado_ate = None
                                user.tentativas_falhas = 0
                                db.commit()
                        except: pass
                    
                    if user.password == hash_password(password):
                        # Resetar falhas
                        user.tentativas_falhas = 0
                        user.bloqueado_ate = None
                        db.commit()
                        
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = user.username
                        st.session_state['user_role'] = user.role
                        st.session_state['permissoes'] = getattr(user, 'permissoes', 'todas')
                        st.session_state['pode_excluir'] = getattr(user, 'pode_excluir', False) or user.role == "admin"
                        
                        # Salvar cookie por 30 dias (manter logado sempre)
                        cookie_manager.set('auth_user', user.username, max_age=86400 * 30, key="set_auth")
                        st.rerun()
                    else:
                        # Errou a senha
                        falhas = getattr(user, 'tentativas_falhas', 0) + 1
                        user.tentativas_falhas = falhas
                        
                        if falhas >= 5:
                            # Bloqueio progressivo ou fixo (15 min)
                            tempo_bloq = 15 if falhas <= 6 else 60
                            user.bloqueado_ate = (agora + timedelta(minutes=tempo_bloq)).isoformat()
                            db.commit()
                            st.error(f"Muitas tentativas! Acesso bloqueado por {tempo_bloq} minutos.")
                        else:
                            db.commit()
                            st.error(f"Senha incorreta! Restam {5 - falhas} tentativas antes do bloqueio.")
                else:
                    st.error("Usuário incorreto.")

# Verificar se já tem cookie logado
auth_cookie = cookie_manager.get('auth_user')
if not st.session_state.get('logged_in') and auth_cookie:
    db = next(get_db())
    user = db.query(Usuario).filter(Usuario.username == auth_cookie).first()
    if user:
        st.session_state['logged_in'] = True
        st.session_state['username'] = user.username
        st.session_state['user_role'] = user.role
        st.session_state['permissoes'] = getattr(user, 'permissoes', 'todas')
        st.session_state['pode_excluir'] = getattr(user, 'pode_excluir', False) or user.role == "admin"
"""

# Replace existing login logic
login_pattern = re.compile(
    r'from db_config import get_db, Usuario, hash_password.*?def login\(\):.*?(?=\ndef main\(\):)',
    re.DOTALL
)

content = login_pattern.sub(new_login_logic, content)

# 3. Update the Logout button
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
print('Updated app.py with Cookies and Rate Limiting')
