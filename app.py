import streamlit as st
from streamlit_option_menu import option_menu
from db_config import init_db, get_db, Usuario
import hashlib

# ==========================================
# 1. Configuração Inicial da Página
# ==========================================
st.set_page_config(
    page_title="Crivo | Car Studio",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="auto"
)

# Inicializa o banco de dados (SQLite local para dev)
init_db()

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
        [data-testid="stSidebar"] * {
            color: rgba(255, 255, 255, 0.9) !important;
        }
        [data-testid="stSidebar"] hr {
            border-color: rgba(255, 255, 255, 0.1) !important;
        }
        
        /* Consertar contraste do Filtro de Data na Sidebar */
        [data-testid="stSidebar"] div[data-baseweb="input"] {
            background-color: transparent !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        [data-testid="stSidebar"] div[data-baseweb="input"] input {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
        }
        
        /* Estilizar st.radio para parecer um menu (esconder bolinhas) */
        [data-testid="stSidebar"] div[role="radiogroup"] > label {
            background-color: transparent !important;
            padding: 10px 15px !important;
            border-radius: 8px !important;
            margin-bottom: 4px !important;
            cursor: pointer !important;
            transition: background-color 0.2s !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
            background-color: rgba(255,255,255,0.1) !important;
        }
        /* Esconder o círculo do radio nativo */
        [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
            display: none !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] p {
            font-size: 14px !important;
            font-weight: 500 !important;
            color: rgba(255,255,255,0.85) !important;
        }
        /* Item Selecionado do Radio (cor Gold) */
        [data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
            background-color: var(--accent) !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] p {
            color: #FFFFFF !important;
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

        /* Estilo dos Cartões (Cards) - Glassmorphism Premium Claro */
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
        .premium-card:hover {
            box-shadow: 0 8px 32px rgba(0,0,0,0.04);
            border-color: rgba(0, 0, 0, 0.12);
        }

        /* Ajustes de Títulos e Textos */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-main) !important;
            font-weight: 500 !important;
            letter-spacing: -0.02em !important;
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

        /* Ajuste do divisor */
        hr {
            border-color: var(--border-color) !important;
            margin-top: 16px !important;
            margin-bottom: 16px !important;
        }

        /* Reduzir espaçamento vertical geral dos blocos do Streamlit */
        div[data-testid="stVerticalBlock"] {
            gap: 0.75rem !important;
        }

        /* Ajuste do botão para formato reduzido, compacto e com TATO (Física) */
        .stButton>button {
            border-radius: 8px !important;
            font-weight: 500 !important;
            font-size: 13px !important;
            padding: 6px 16px !important;
            white-space: nowrap !important;
            background-color: #FFFFFF !important;
            color: var(--text-main) !important;
            border: 1px solid var(--border-color) !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
            transition: transform 0.15s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s ease, border-color 0.2s ease !important;
        }
        .stButton>button:hover {
            border-color: rgba(0,0,0,0.15) !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
            color: var(--text-main) !important;
        }
        .stButton>button:active {
            transform: scale(0.96) !important; /* Física magnética/clique */
            box-shadow: 0 0px 0px rgba(0,0,0,0) !important;
        }

        /* Botão Primário (Gold) - Contraste exigido pela skill */
        button[kind="primary"] {
            background-color: var(--accent) !important;
            border-color: var(--accent) !important;
            color: #FFFFFF !important; 
        }
        button[kind="primary"]:hover {
            background-color: #D4B06A !important;
            color: #FFFFFF !important;
        }
        button[kind="primary"] p, button[kind="primary"] span {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }

        /* Melhorar contraste das caixas de preenchimento (inputs e selectbox) para Light Mode */
        div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
            border: 1px solid rgba(0,0,0,0.1) !important;
            border-radius: 8px !important;
            background-color: #FFFFFF !important;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.01) !important;
        }
        div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 1px var(--accent) !important;
        }
        div[data-baseweb="input"] input, div[data-baseweb="select"] div, div[data-baseweb="textarea"] textarea {
            color: var(--text-main) !important;
        }

        /* Modais/Dialogs do Streamlit adaptados para Clean Apple */
        div[role="dialog"] {
            background-color: #FFFFFF !important;
            color: var(--text-main) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 16px !important;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15) !important;
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
            
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        
        if st.button("Entrar", type="primary", use_container_width=True):
            db = next(get_db())
            user = db.query(Usuario).filter(Usuario.username == username).first()
            if user and user.password_hash == hash_password(password):
                st.session_state['logged_in'] = True
                st.session_state['user_role'] = user.role
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 4. Estrutura Principal e Menu Lateral
# ==========================================
def main():
    if not st.session_state['logged_in']:
        render_login()
        return

    # Sidebar
    with st.sidebar:
        # Imagem ainda menor (proporção 2:2:2 concentra no meio)
        col_img1, col_img2, col_img3 = st.columns([2, 2, 2])
        with col_img2:
            try:
                st.image("assets/logo.png", use_container_width=True)
            except:
                st.markdown(f"<h2 style='text-align: center; color: white; font-size: 22px;'>CRIVO</h2>", unsafe_allow_html=True)
            
        st.markdown(f"<p style='text-align: center; font-size: 11px; margin-top:-10px; color: rgba(255,255,255,0.7);'>Acesso: <b>{st.session_state['user_role'].upper()}</b></p>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        
        st.markdown("<p style='font-size: 13px; color: rgba(255,255,255,0.7); margin-bottom: 5px;'>Filtro Global</p>", unsafe_allow_html=True)
        global_date = st.date_input("Data de Referência", label_visibility="collapsed")
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        
        menu_options = [
            "⚡ Fluxo do dia", 
            "🔄 Transações", 
            "💰 Gestão Financeira", 
            "👥 Gestão de Pessoal",
            "🏆 CRM & Fidelidade",
            "🗃️ Cadastros",
            "🧾 Integração Fiscal",
            "☁️ Importar / Exportar",
            "📊 Central Analítica"
        ]
        
        # Menu Nativo via st.radio (fecha automaticamente no mobile)
        selected_raw = st.radio("Navegação", menu_options, label_visibility="collapsed")
        selected = selected_raw.split(" ", 1)[1] # Extrai o nome sem o emoji
        
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        if st.button("Sair", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['user_role'] = None
            st.rerun()

    # Injeta CSS dinâmico para centralizar apenas se for Fluxo do Dia
    if selected == "Fluxo do dia":
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
    if selected == "Fluxo do dia":
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
