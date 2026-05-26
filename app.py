import streamlit as st
from streamlit_option_menu import option_menu
from db_config import init_db

# ==========================================
# 1. Configuração Inicial da Página
# ==========================================
st.set_page_config(
    page_title="ERP Premium | Estética Automotiva",
    page_icon="🚘",
    layout="centered",
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
        /* Variáveis de Cores */
        :root {
            --bg-color: #F5F5F7;
            --card-bg: #FFFFFF;
            --text-main: #1D1D1F;
            --text-sec: #86868B;
            --border-color: #E5E5EA;
            --success: #34C759;
            --danger: #FF3B30;
            --warning: #FF9500;
            --accent: #5E5CE6;
        }

        /* Estilo da área de conteúdo (Centralizado e Compacto para Tablet) */
        .block-container {
            max-width: 760px !important;
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            margin: 0 auto !important;
        }

        /* Fontes e Fundo do App */
        .stApp {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
            background-color: var(--bg-color) !important;
        }

        /* Esconder Menu Hamburguer e Footer, mantendo a seta do sidebar visível */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {
            background-color: transparent !important;
        }

        /* Estilo dos Cartões (Cards) - UX Master */
        .premium-card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 18px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
            margin-bottom: 16px;
            transition: box-shadow 0.3s ease;
        }
        .premium-card:hover {
            box-shadow: 0 6px 16px rgba(0,0,0,0.06);
        }

        /* Ajustes de Títulos e Textos */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-main) !important;
            font-weight: 600 !important;
        }
        p, span, label {
            color: var(--text-main);
        }

        /* Ajuste do botão para formato reduzido e elegante */
        .stButton>button {
            border-radius: 8px !important;
            font-weight: 500 !important;
        }

        /* Forçar texto branco para botões primários (primary) para garantir excelente contraste */
        button[kind="primary"], button[kind="primary"] p, button[kind="primary"] span {
            color: #FFFFFF !important;
        }

        /* Força fundo branco nos modais/dialogs do Streamlit para evitar restos de dark mode */
        div[role="dialog"] {
            background-color: #FFFFFF !important;
            color: #1D1D1F !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 12px !important;
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==========================================
# 3. Gestão de Estado da Sessão (SPA Feeling)
# ==========================================
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = 'Admin' # Temporário para desenvolvimento
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = True # Bypass temporário

# ==========================================
# 4. Estrutura Principal e Menu Lateral
# ==========================================
def main():
    if not st.session_state['logged_in']:
        st.title("Login Seguro")
        st.write("Módulo de Controle de Acesso (RBAC) em desenvolvimento...")
        return

    # Sidebar
    with st.sidebar:
        st.markdown("<h2 style='text-align: center; color: #1D1D1F;'>🚘 ERP Premium</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'>Acesso: <b>{st.session_state['user_role']}</b></p>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Filtros Globais Persistentes
        st.markdown("<p style='font-size: 14px; color: #86868B; margin-bottom: 5px;'>Filtro Global</p>", unsafe_allow_html=True)
        global_date = st.date_input("Data de Referência", label_visibility="collapsed")
        st.markdown("---")
        
        # Menu de Navegação (Ícones explicativos)
        menu_options = [
            "Fast Launch (PDV)", 
            "Transações", 
            "Gestão Financeira", 
            "Estoque Fracionado",
            "Gestão de Pessoal",
            "CRM & Fidelidade",
            "Cadastros Base",
            "Integração Fiscal",
            "Importar / Exportar",
            "Central Analítica"
        ]
        
        icons = [
            "cart-plus", "arrow-left-right", "wallet2", "box-seam",
            "people", "person-badge", "database-add", "receipt",
            "cloud-arrow-up", "bar-chart-line"
        ]
        
        selected = option_menu(
            menu_title=None,
            options=menu_options,
            icons=icons,
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#5E5CE6", "font-size": "18px"}, 
                "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px", "--hover-color": "#E5E5EA", "color": "#1D1D1F"},
                "nav-link-selected": {"background-color": "#5E5CE6", "color": "white", "font-weight": "normal"},
            }
        )

    # ==========================================
    # 5. Roteamento de Módulos (Views)
    # ==========================================
    if selected == "Fast Launch (PDV)":
        from modules.fast_launch import render_fast_launch
        render_fast_launch()


    elif selected == "Gestão Financeira":
        st.title("💼 Gestão Financeira")
        st.markdown("""
        <div class="premium-card">
            <h3 style='margin-top: 0;'>Posição Consolidada</h3>
            <p>Trifurcação Bancária Lógica (B2B, B2C, Reserva PIX) e Controle de Pró-labore.</p>
            <hr style='border: 0.5px solid #E5E5EA;'>
            <p style="color: var(--accent);"><i>Aguardando comando para desenvolvimento deste módulo...</i></p>
        </div>
        """, unsafe_allow_html=True)
        
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
