import streamlit as st
from streamlit_option_menu import option_menu
from db_config import init_db, get_db, Usuario
import hashlib
import extra_streamlit_components as stx
from datetime import datetime, timedelta

@st.cache_resource
def get_cookie_manager():
    return stx.CookieManager()
cookie_manager = get_cookie_manager()


# ==========================================
# 1. Configuração Inicial da Página
# ==========================================
from PIL import Image

st.set_page_config(
    page_title="Crivo | Car Studio",
    page_icon=Image.open("icon.png"),
    layout="wide",
    initial_sidebar_state="auto"
)

# Inicializa o banco de dados apenas uma vez para não gerar lentidão na nuvem
@st.cache_resource(show_spinner=False)
def initialize_database_v5():
    init_db()

initialize_database_v5()

# ==========================================
# 2. Injeção de CSS Customizado (Design Apple)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

        /* Variáveis de Cores - Clean Apple (Taste-Skill) + Crivo Blue */
        :root {
            --bg-color: #F5F5F7; /* Fundo Apple padrão */
            --card-bg: #FFFFFF;
            --text-main: #1D1D1F;
            --text-sec: #86868B;
            --border-color: rgba(0, 0, 0, 0.08);
            --success: #34C759;
            --danger: #FF3B30;
            --warning: #FF9500;
            --accent: #C5A059; /* Gold */
            --crivo-blue: #001C25; /* Cor exata do fundo da logo */
        }

        /* Estilo da área de conteúdo (Full width adaptável) */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            padding-left: 3rem !important;
            padding-right: 3rem !important;
        }

        /* Fontes e Fundo do App */
        .stApp, .stApp > header {
            font-family: 'Outfit', -apple-system, sans-serif !important;
            background-color: var(--bg-color) !important;
            color: var(--text-main) !important;
        }
        
        /* Cor de fundo do Menu Lateral */
        [data-testid="stSidebar"] {
            background-color: var(--crivo-blue) !important;
        }
        /* Fundo escuro para o input de data na sidebar */
        [data-testid="stSidebar"] div[data-baseweb="input"] {
            background-color: rgba(0,0,0,0.2) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 8px !important;
        }
        [data-testid="stSidebar"] div[data-baseweb="input"] input {
            color: white !important;
            -webkit-text-fill-color: white !important;
        }
        
        /* Remover bordas de iframes para o option_menu ficar 100% limpo */
        iframe {
            border: none !important;
            outline: none !important;
        }

        /* Botões na sidebar transparentes com borda clara */
        [data-testid="stSidebar"] .stButton > button {
            background-color: transparent !important;
            color: white !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            border-color: white !important;
            background-color: rgba(255,255,255,0.1) !important;
        }

        /* Esconder Menu Hamburguer e Footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Estilo dos Cartões (Cards) */
        .premium-card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 16px !important;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            box-shadow: 0 4px 24px rgba(0,0,0,0.02);
            margin-bottom: 8px !important;
            transition: all 0.3s ease;
        }

        /* Ajustes de Títulos e Textos */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-main) !important;
            font-weight: 500 !important;
            margin-top: 4px !important;
            margin-bottom: 4px !important;
        }
        p, span, label {
            color: var(--text-sec);
            font-weight: 400;
        }
        strong, b {
            color: var(--text-main);
            font-weight: 500;
        }

        /* Reduzir espaçamento vertical geral dos blocos do Streamlit */
        div[data-testid="stVerticalBlock"] {
            gap: 0.75rem !important;
        }

        /* Ajuste do botão genérico */
        .stButton>button {
            border-radius: 8px !important;
            font-weight: 500 !important;
            font-size: 13px !important;
            padding: 6px 16px !important;
            background-color: #FFFFFF !important;
            color: var(--text-main) !important;
            border: 1px solid var(--border-color) !important;
        }

        /* Botão Primário (Gold) */
        button[kind="primary"] {
            background-color: var(--accent) !important;
            border-color: var(--accent) !important;
            color: #FFFFFF !important; 
        }
        button[kind="primary"] p, button[kind="primary"] span {
            color: #FFFFFF !important;
        }

    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==========================================
# 3. Gestão de Estado da Sessão (SPA Feeling)
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def render_login():
    # Injetar background azul para a tela de login
    st.markdown("""
        <style>
            .stApp { background-color: var(--crivo-blue) !important; }
            .premium-card { background-color: rgba(255, 255, 255, 0.95); }
        </style>
    """, unsafe_allow_html=True)
    
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
                st.error("Usuário ou senha inválidos.")

# ==========================================
# 4. Estrutura Principal e Menu Lateral
# ==========================================
def main():
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
        return

    # Sidebar
    with st.sidebar:
        try:
            import base64
            with open("assets/logo.png", "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            
            st.markdown(
                f"""
                <div style="display: flex; justify-content: center; width: 100%; margin-bottom: 20px;">
                    <img src="data:image/png;base64,{encoded_string}" style="max-width: 150px; width: 100%;">
                </div>
                """, 
                unsafe_allow_html=True
            )
        except:
            st.markdown(f"<h2 style='text-align: center; color: white; font-size: 22px;'>CRIVO</h2>", unsafe_allow_html=True)
            
        st.markdown(f"<p style='text-align: center; font-size: 11px; margin-top:-10px; color: rgba(255,255,255,0.7);'>Acesso: <span style='color: white; font-weight: 800;'>{st.session_state['user_role'].upper()}</span></p>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        
        all_menu_options = [
            "Fluxo do Dia",
            "Transações",
            "Gestão Financeira",
            "Estoque & Insumos",
            "Gestão de Pessoal",
            "CRM & Fidelidade",
            "Cadastros",
            "Central Analítica"
        ]
        
        # Filtrar menus baseados nas permissões
        user_perms = st.session_state.get('permissoes', 'todas')
        if user_perms == "todas" or st.session_state.get('user_role') == 'admin':
            menu_options = all_menu_options
        else:
            perms_list = user_perms.split(",")
            map_perms = {
                "Fluxo do Dia": ["Fluxo do Dia", "Transações"],
                "Financeiro": ["Gestão Financeira"],
                "Estoque": ["Estoque & Insumos"],
                "Gestão de Pessoal": ["Gestão de Pessoal"],
                "CRM": ["CRM & Fidelidade"],
                "Cadastros": ["Cadastros", "Central Analítica"]
            }
            menu_options = []
            for k, v_list in map_perms.items():
                if k in perms_list:
                    menu_options.extend(v_list)
        
        # Icons matching the final menu_options list
        all_icons = {
            "Fluxo do Dia": "cart-plus",
            "Transações": "arrow-left-right",
            "Gestão Financeira": "wallet2",
            "Estoque & Insumos": "box-seam",
            "Gestão de Pessoal": "people",
            "CRM & Fidelidade": "person-badge",
            "Cadastros": "database-add",
            "Central Analítica": "bar-chart-line"
        }
        icons = [all_icons[m] for m in menu_options]
        
        from streamlit_option_menu import option_menu
        selected = option_menu(
            menu_title=None,
            options=menu_options,
            icons=icons,
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#001C25", "border": "none", "border-radius": "0px"},
                "icon": {"color": "#C5A059", "font-size": "18px"}, 
                "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px", "--hover-color": "rgba(255,255,255,0.1)", "color": "rgba(255,255,255,0.85)"},
                "nav-link-selected": {"background-color": "#C5A059", "color": "white", "font-weight": "normal"},
            }
        )
        
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        
        # DEBUG INDICATOR
        from db_config import DATABASE_URL, debug_msg
        db_type = "☁️ Supabase (Nuvem)" if "postgres" in DATABASE_URL else "💻 SQLite (Local)"
        st.caption(f"Banco: {db_type}")
        if db_type == "💻 SQLite (Local)":
            st.caption(f"Debug: {debug_msg}")
        
        if st.button("Sair", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['user_role'] = None
            st.rerun()

    # Injeta CSS dinâmico para centralizar apenas se for Fluxo do Dia
    if selected == "Fluxo do Dia":
        st.markdown("""
        <style>
            .block-container {
                max-width: 500px !important;
                margin: 0 auto !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
        </style>
        """, unsafe_allow_html=True)

    # ==========================================
    # 5. Roteamento de Módulos (Views)
    # ==========================================
    if selected == "Fluxo do Dia":
        from modules.fast_launch import render_fast_launch
        render_fast_launch()

    elif selected == "Transações":
        from modules.transactions import render_transactions
        render_transactions()


    elif selected == "Gestão Financeira":
        from modules.financial import render_financial
        render_financial()

    elif selected == "Cadastros":
        from modules.cadastros import render_cadastros
        render_cadastros()
        
    elif selected == "Gestão de Pessoal":
        from modules.personnel import render_personnel
        render_personnel()
        
    elif selected == "Estoque & Insumos":
        from modules.inventory import render_inventory
        render_inventory()
        
    elif selected == "CRM & Fidelidade":
        from modules.crm import render_crm
        render_crm()
        
    else:
        st.title(selected)
        st.markdown(f"""
        <div class='premium-card'>
            <h3 style='margin-top: 0;'>Status: Na Fila</h3>
            <p>O módulo de <b>{selected}</b> será construído conforme a arquitetura modular solicitada.</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
