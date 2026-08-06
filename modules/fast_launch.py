import streamlit as st
from db_config import get_db, Cliente, Servico, Produto, Atendimento, ItemAtendimento
from datetime import datetime, timedelta, timezone
import unicodedata

# Helper para remover acentuação de strings para pesquisa insensível a acentos
def remover_acentos(texto):
    if not texto:
        return ""
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

# Tratamento para st.dialog independente da versão exata 1.34/1.35+
dialog_decorator = st.dialog if hasattr(st, "dialog") else st.experimental_dialog

# Helper para retornar hora no fuso horário do usuário (UTC-3 - Brasília) como ingênua (naive)
def obter_hora_local():
    fuso_brasil = timezone(timedelta(hours=-3))
    return datetime.now(fuso_brasil).replace(tzinfo=None)

# Helper para formatar telefones de forma inteligente
def formatar_telefone(tel_str):
    digitos = "".join([c for c in tel_str if c.isdigit()])
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    elif len(digitos) == 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    elif len(digitos) == 9:
        return f"(61) {digitos[:5]}-{digitos[5:]}"
    elif len(digitos) == 8:
        if digitos.startswith('9'):
            return f"(61) 9{digitos[1:5]}-{digitos[5:]}"
        return f"(61) {digitos[:4]}-{digitos[4:]}"
    return tel_str

# Helper de ícones dourados elegantes (Referência: Imagem 1)
def gold_icon(icon_name):
    icons = {
        "user": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>',
        "service": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path></svg>',
        "payment": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect><line x1="1" y1="10" x2="23" y2="10"></line></svg>',
        "diamond": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:4px;"><polygon points="6 3 18 3 22 9 12 22 2 9 6 3"></polygon></svg>',
        "box": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>',
        "calendar": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',
        "clock": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:4px;"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>',
        "lightning": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>',
        "car": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"></path><circle cx="7" cy="17" r="2"></circle><circle cx="17" cy="17" r="2"></circle><path d="M13 17H9"></path></svg>',
        "plus": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:4px;"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>',
        "edit": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:4px;"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>',
        "trash": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:4px;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>',
        "check": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:4px;"><polyline points="20 6 9 17 4 12"></polyline></svg>',
        "alert": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
        "settings": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2 2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.5 1z"></path></svg>',
        "chart": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
        "fire": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path></svg>',
        "snowflake": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><line x1="2" y1="12" x2="22" y2="12"></line><line x1="12" y1="2" x2="12" y2="22"></line><path d="m20 16-4-4 4-4"></path><path d="m4 8 4 4-4 4"></path><path d="m16 4-4 4-4-4"></path><path d="m8 20 4-4 4 4"></path></svg>',
        "arrow-left-right": '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:8px;"><path d="M7 16V4M7 4L3 8M7 4L11 8M17 8V20M17 20L21 16M17 20L13 16"></path></svg>',
        "wallet2": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M20 12V8H6a2 2 0 0 1-2-2c0-1.1.9-2 2-2h12v4"></path><path d="M4 6v12c0 1.1.9 2 2 2h14v-4"></path><path d="M18 12a2 2 0 0 0-2 2c0 1.1.9 2 2 2h4v-4h-4z"></path></svg>'
    }
    return icons.get(icon_name, "")


@dialog_decorator("Cadastrar Novo Cliente")
def dialog_novo_cliente():
    db = next(get_db())
    # Gerar código automático e sequencial
    qtd = db.query(Cliente).count()
    codigo_seq = f"CLI-{qtd+1:04d}"
    
    st.info(f"Código do Cliente: **{codigo_seq}**")
    novo_nome = st.text_input("Nome do Cliente")
    
    # Campo de telefone dividido para travar o DDD 61 e permitir tabulação direta (TAB pula o campo desabilitado)
    col_ddd, col_tel = st.columns([1, 3], vertical_alignment="bottom")
    col_ddd.text_input("DDD", value="61", disabled=True)
    novo_tel_num = col_tel.text_input("Telefone", placeholder="99571-7073")
    
    nova_placa = st.text_input("Placa do Veículo")
    novo_modelo = st.text_input("Modelo do Veículo")
    
    if st.button("Salvar Cliente", type="primary", use_container_width=True):
        if novo_nome:
            # Garante formatação com o DDD 61
            tel_formatado = formatar_telefone(novo_tel_num)
            novo_cliente = Cliente(
                codigo=codigo_seq, 
                nome=novo_nome, 
                telefone=tel_formatado, 
                placa_veiculo=nova_placa,
                modelo_veiculo=novo_modelo
            )
            db.add(novo_cliente)
            db.commit()
            st.success(f"Cliente {codigo_seq} cadastrado com sucesso!")
            st.rerun()

@dialog_decorator("Cancelar Atendimento")
def dialog_cancelar_atendimento(at_id):
    st.warning("Para cancelar este serviço, é necessária a senha do gerente.")
    senha = st.text_input("Senha do Gerente", type="password", key=f"senha_canc_{at_id}")
    if st.button("Confirmar Cancelamento", type="primary", use_container_width=True):
        if senha == "admin":
            db = next(get_db())
            at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
            if at:
                at.status = "Cancelado"
                db.commit()
                st.success("Atendimento cancelado com sucesso!")
                st.rerun()
        else:
            st.error("Senha incorreta!")

@dialog_decorator("Editar Atendimento")
def dialog_editar_atendimento(at_id):
    db = next(get_db())
    at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
    if not at:
        return
        
    st.write(f"Editando OS: **{at.codigo}**")
    
    # Exige senha do gerente para QUALQUER alteração/remoção
    senha_gerente = st.text_input("Senha do Gerente para Alterações", type="password", key=f"edit_senha_{at_id}")
    gerente_autorizado = (senha_gerente == "admin")
    
    if not gerente_autorizado:
        st.warning("⚠️ Insira a senha do gerente ('admin') para liberar a edição ou remoção de itens.")
        
    # Lista de itens atuais
    itens = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id == at_id).all()
    st.markdown("#### Itens Lançados:")
    for i in itens:
        nome_ref = ""
        if i.tipo == "Serviço":
            s = db.query(Servico).filter(Servico.id == i.referencia_id).first()
            nome_ref = s.nome if s else "Desconhecido"
        else:
            p = db.query(Produto).filter(Produto.id == i.referencia_id).first()
            nome_ref = p.nome if p else "Desconhecido"
            
        col1, col2 = st.columns([3, 1], vertical_alignment="center")
        col1.write(f"- {i.tipo}: {nome_ref} (R$ {i.valor_cobrado:.2f})")
        if col2.button("Remover", key=f"rem_{i.id}", use_container_width=True, disabled=not gerente_autorizado):
            if senha_gerente == "admin":
                db.delete(i)
                # Recalcula total
                at.valor_total -= i.valor_cobrado
                db.commit()
                st.rerun()
            
    st.markdown("---")
    st.markdown("#### Adicionar Novo Item")
    servicos = db.query(Servico).all()
    produtos = db.query(Produto).all()
    
    tipo_novo = st.selectbox("Tipo", ["Serviço", "Produto"], key="edit_tipo")
    if tipo_novo == "Serviço":
        item_novo = st.selectbox("Serviço", [s.nome for s in servicos], key="edit_serv")
    else:
        item_novo = st.selectbox("Produto", [p.nome for p in produtos], key="edit_prod")
        
    valor_novo = st.number_input("Valor", min_value=0.0, key="edit_valor")
    
    if st.button("Adicionar Item ao Atendimento Existente", use_container_width=True, disabled=not gerente_autorizado):
        if senha_gerente == "admin":
            ref_id = 0
            if tipo_novo == "Serviço":
                ref_id = db.query(Servico).filter(Servico.nome == item_novo).first().id
            else:
                ref_id = db.query(Produto).filter(Produto.nome == item_novo).first().id
                
            n_item = ItemAtendimento(atendimento_id=at.id, tipo=tipo_novo, referencia_id=ref_id, valor_cobrado=valor_novo)
            db.add(n_item)
            at.valor_total += valor_novo
            db.commit()
            st.success("Item adicionado!")
            st.rerun()

@dialog_decorator("Concluir Atendimento")
def dialog_concluir_atendimento(at_id):
    db = next(get_db())
    at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
    if not at:
        return
        
    st.write(f"Deseja realmente concluir a **{at.codigo}**?")
    obs = st.text_input("Observação (Opcional)", placeholder="Ex: Higienização impecável concluída...")
    
    if st.button("Confirmar Conclusão", type="primary", use_container_width=True):
        at.status = "Finalizado"
        at.data_conclusao = obter_hora_local().isoformat()
        at.observacoes = obs
        db.commit()
        
        # Integration with Financial Module
        try:
            from modules.financial import registrar_receita_pdv
            registrar_receita_pdv(at.id, db)
        except Exception as e:
            pass
        
        # Salva a mensagem no estado da sessão para persistir no diálogo de sucesso
        st.session_state['success_msg'] = f"Atendimento {at.codigo} concluído com sucesso!"
        st.rerun()

@dialog_decorator("Lançamento Confirmado")
def dialog_sucesso_lancamento(mensagem):
    st.success(mensagem)
    if st.button("Entendido", type="primary", use_container_width=True):
        st.session_state['success_msg'] = None
        st.rerun()

def render_fast_launch():
    # Mensagem de confirmação persistente em modal
    if 'success_msg' not in st.session_state:
        st.session_state['success_msg'] = None
        
    if st.session_state['success_msg']:
        dialog_sucesso_lancamento(st.session_state['success_msg'])

    # Inicializando estados
    if 'caixa_aberto' not in st.session_state:
        st.session_state['caixa_aberto'] = True
    if 'pdv_cart' not in st.session_state:
        st.session_state['pdv_cart'] = []
    if 'selected_payment' not in st.session_state:
        st.session_state['selected_payment'] = 'Pix'

    col_t, col_s = st.columns([1.8, 1.2], vertical_alignment="center")
    with col_t:
        st.markdown(f"<h2 style='margin:0; padding:0; font-size: 24px;'>{gold_icon('lightning')} Fluxo do dia</h2>", unsafe_allow_html=True)
    with col_s:
        # Toggle Caixa Aberto/Fechado (estilizado como um pill elegante)
        caixa_status = st.session_state.get('caixa_aberto', True)
        bg_color = "#34C759" if caixa_status else "#FF3B30"
        
        st.markdown(f"""
        <style>
            .st-key-btn_caixa_toggle button {{
                background-color: {bg_color} !important;
                color: #FFFFFF !important;
                border: 1px solid {bg_color} !important;
                border-radius: 20px !important;
                font-weight: bold !important;
                font-size: 11px !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
                height: 32px !important;
                white-space: nowrap !important;
                transition: background-color 0.2s ease-in-out !important;
            }}
            .st-key-btn_caixa_toggle button:hover, 
            .st-key-btn_caixa_toggle button:active, 
            .st-key-btn_caixa_toggle button:focus {{
                background-color: {bg_color} !important;
                color: #FFFFFF !important;
                border-color: {bg_color} !important;
            }}
            /* Forçar a cor branca para os elementos de texto internos do Streamlit */
            .st-key-btn_caixa_toggle button * {{
                color: #FFFFFF !important;
            }}
        </style>
        """, unsafe_allow_html=True)
        
        label = "🟢 CAIXA ABERTO" if caixa_status else "🔴 CAIXA FECHADO"
        if st.button(label, use_container_width=True, key="btn_caixa_toggle"):
            st.session_state['caixa_aberto'] = not caixa_status
            st.rerun()
    
    # Obter sessão do DB
    db = next(get_db())

    # Carregar dados
    clientes = db.query(Cliente).all()
    servicos = db.query(Servico).all()
    produtos = db.query(Produto).all()
    
    # Estrutura de Abas (Lançamento -> Novo Atendimento, Finalizado -> Concluído, Resumo)
    tab1, tab2, tab3, tab4 = st.tabs(["Novo Atendimento", "Em andamento", "Concluído", "Resumo"])
    
    # ==========================================
    # ABA 1: Novo Atendimento
    # ==========================================
    with tab1:
        # Alerta e verificação se o caixa estiver fechado
        caixa_aberto = st.session_state.get('caixa_aberto', True)
        if not caixa_aberto:
            st.warning("⚠️ Caixa Fechado! Lançamentos desabilitados. Abra o caixa no botão verde no topo direito para continuar.")
            
        with st.container(border=True):
            st.markdown(f"<h3 style='margin:0 0 12px 0; font-size:18px;'>{gold_icon('user')} Novo Atendimento</h3>", unsafe_allow_html=True)
            
            # Passo 1: Selecionar Cliente
            cliente_atendimentos = {}
            for c in clientes:
                count = db.query(Atendimento).filter(
                    Atendimento.cliente_id == c.id, 
                    Atendimento.status == "Finalizado"
                ).count()
                cliente_atendimentos[c.id] = count
                
            # Campo de Pesquisa Textual - Sempre abre o teclado nativo no celular
            col_search, col_new = st.columns([2.5, 1], vertical_alignment="bottom")
            with col_search:
                busca_cliente = st.text_input("🔍 Pesquisar Cliente (Digite Nome, Placa ou Modelo e aperte Enter)", placeholder="Ex: Corolla, ABC-1234, João...", disabled=not caixa_aberto)
            with col_new:
                if st.button("+ Novo Cliente", use_container_width=True, disabled=not caixa_aberto):
                    dialog_novo_cliente()
            
            # Filtrar a lista de opções com base na pesquisa (ignorando acentuação)
            termo = busca_cliente.strip().lower()
            cliente_opcoes = ["-- Selecione o Cliente --"]
            for c in clientes:
                if c.codigo == "CLI-0000":
                    continue # Não permite cliente avulso
                
                nome = remover_acentos(c.nome or "").lower()
                placa = remover_acentos(c.placa_veiculo or "").lower()
                modelo = remover_acentos(c.modelo_veiculo or "").lower()
                codigo = remover_acentos(c.codigo or "").lower()
                
                termo_limpo = remover_acentos(termo)
                if termo_limpo and (termo_limpo not in nome and termo_limpo not in placa and termo_limpo not in modelo and termo_limpo not in codigo):
                    continue
                    
                tag_fidelidade = ""
                if cliente_atendimentos.get(c.id, 0) > 10:
                    tag_fidelidade = " 💎 [Diamante]"
                    
                cliente_opcoes.append(
                    f"{c.codigo} | {c.nome}{tag_fidelidade} - {c.modelo_veiculo or 'Sem Modelo'} ({c.placa_veiculo or 'Sem Placa'})"
                )
            
            st.markdown(f"<label style='font-size:13px; font-weight:500; color:var(--text-main); margin-bottom:-4px; display:block;'>{gold_icon('user')} Selecionar Cliente</label>", unsafe_allow_html=True)
            # Pré-seleção automática e imediata caso haja exatamente uma única correspondência
            index_sel = 1 if len(cliente_opcoes) == 2 else 0
            cliente_selecionado = st.selectbox("Selecione o Cliente", cliente_opcoes, index=index_sel, label_visibility="collapsed", disabled=not caixa_aberto)
                
            st.markdown("<hr style='margin:8px 0; border:0; border-top:1px solid #E5E5EA;'>", unsafe_allow_html=True)

            # Passo 2: O que está lançando (Permite vender Serviço ou Produto individual)
            tipo_venda = st.radio("O que está vendendo?", ["Serviço", "Produto"], horizontal=True, disabled=not caixa_aberto)
            
            if tipo_venda == "Serviço":
                st.markdown(f"<label style='font-size:13px; font-weight:500; color:var(--text-main); margin-bottom:-4px; display:block;'>{gold_icon('service')} Selecionar Serviço Principal</label>", unsafe_allow_html=True)
                servico_opcoes = [s.nome for s in servicos]
                item_selecionado = st.selectbox("Serviço Principal", servico_opcoes if servico_opcoes else ["Nenhum serviço cadastrado"], label_visibility="collapsed", disabled=not caixa_aberto)
                
                valor_sugerido = 0.0
                if item_selecionado and item_selecionado != "Nenhum serviço cadastrado":
                    serv = next((s for s in servicos if s.nome == item_selecionado), None)
                    valor_sugerido = serv.preco_padrao if serv else 0.0
            else:
                st.markdown(f"<label style='font-size:13px; font-weight:500; color:var(--text-main); margin-bottom:-4px; display:block;'>{gold_icon('box')} Selecionar Produto</label>", unsafe_allow_html=True)
                produto_opcoes = [p.nome for p in produtos]
                item_selecionado = st.selectbox("Produto Principal", produto_opcoes if produto_opcoes else ["Nenhum produto cadastrado"], label_visibility="collapsed", disabled=not caixa_aberto)
                
                valor_sugerido = 0.0
                if item_selecionado and item_selecionado != "Nenhum produto cadastrado":
                    prod = next((p for p in produtos if p.nome == item_selecionado), None)
                    valor_sugerido = prod.preco_venda if prod else 0.0
            
            col_preco, col_space = st.columns([1.5, 2], vertical_alignment="bottom")
            valor_final = col_preco.number_input("Valor (R$)", value=valor_sugerido, min_value=0.0, disabled=not caixa_aberto)
            
            st.markdown("<hr style='margin:8px 0; border:0; border-top:1px solid #E5E5EA;'>", unsafe_allow_html=True)
            
            # Passo 3: Forma de Pagamento em Botões/Quadrados elegantes lado a lado (Débito, Pix, Crédito, Dinheiro)
            st.markdown(f"<label style='font-size:13px; font-weight:500; color:var(--text-main); margin-bottom:-4px; display:block;'>{gold_icon('payment')} Selecionar Forma de Pagamento</label>", unsafe_allow_html=True)
            
            st.markdown("""
            <style>
                /* Configuração base dos botões de pagamento */
                .st-key-pay_deb button,
                .st-key-pay_pix button,
                .st-key-pay_cred button,
                .st-key-pay_din button {
                    height: 110px !important;
                    display: flex !important;
                    flex-direction: column !important;
                    align-items: center !important;
                    justify-content: flex-end !important;
                    padding-bottom: 14px !important;
                    border-radius: 12px !important;
                    border: 1.5px solid #86868B !important;
                    background-color: #FFFFFF !important;
                    transition: all 0.2s ease-in-out !important;
                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06) !important;
                    background-repeat: no-repeat !important;
                    background-position: center top 20px !important;
                    background-size: 32px 32px !important;
                }
                
                /* Efeito hover geral */
                .st-key-pay_deb button:hover,
                .st-key-pay_pix button:hover,
                .st-key-pay_cred button:hover,
                .st-key-pay_din button:hover {
                    border-color: #007AFF !important;
                    background-color: #F5F5F7 !important;
                    box-shadow: 0 6px 14px rgba(0, 0, 0, 0.1) !important;
                }
                
                /* Estilos para o estado selecionado (primary) */
                .st-key-pay_deb button[kind="primary"],
                .st-key-pay_pix button[kind="primary"],
                .st-key-pay_cred button[kind="primary"],
                .st-key-pay_din button[kind="primary"] {
                    background-color: #007AFF !important;
                    border-color: #007AFF !important;
                    box-shadow: 0 6px 16px rgba(0, 122, 255, 0.25) !important;
                }
                
                /* Forçar a cor e fonte dos elementos de texto internos do Streamlit */
                .st-key-pay_deb button p, .st-key-pay_deb button span,
                .st-key-pay_pix button p, .st-key-pay_pix button span,
                .st-key-pay_cred button p, .st-key-pay_cred button span,
                .st-key-pay_din button p, .st-key-pay_din button span {
                    margin: 0 !important;
                    line-height: 1.3 !important;
                    font-size: 13px !important;
                    font-weight: 700 !important;
                    color: #1D1D1F !important;
                    text-align: center !important;
                    white-space: normal !important;
                }
                
                .st-key-pay_deb button[kind="primary"] p, .st-key-pay_deb button[kind="primary"] span,
                .st-key-pay_pix button[kind="primary"] p, .st-key-pay_pix button[kind="primary"] span,
                .st-key-pay_cred button[kind="primary"] p, .st-key-pay_cred button[kind="primary"] span,
                .st-key-pay_din button[kind="primary"] p, .st-key-pay_din button[kind="primary"] span {
                    color: #FFFFFF !important;
                }

                /* Ícones específicos por botão (Normal / Secondary) */
                .st-key-pay_deb button {
                    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24' fill='none' stroke='%23C5A059' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='2' y='5' width='20' height='14' rx='2' ry='2'></rect><line x1='2' y1='10' x2='22' y2='10'></line><path d='M6 14h.01M10 14h.01'></path></svg>") !important;
                }
                .st-key-pay_pix button {
                    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24' fill='none' stroke='%23C5A059' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 3L4 11h5l3-3 3 3h5zM12 21l-8-8h5l3 3 3-3h5z'></path></svg>") !important;
                }
                .st-key-pay_cred button {
                    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24' fill='none' stroke='%23C5A059' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='2' y='5' width='20' height='14' rx='2' ry='2'></rect><line x1='2' y1='10' x2='22' y2='10'></line><circle cx='6' cy='15' r='1.5'></circle><circle cx='18' cy='15' r='1.5'></circle></svg>") !important;
                }
                .st-key-pay_din button {
                    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24' fill='none' stroke='%23C5A059' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='2' y='6' width='20' height='12' rx='2'></rect><circle cx='12' cy='12' r='2.5'></circle><line x1='6' y1='12' x2='6.01' y2='12'></line><line x1='18' y1='12' x2='18.01' y2='12'></line></svg>") !important;
                }

                /* Ícones específicos para botões SELECIONADOS (Brancos para contraste com azul) */
                .st-key-pay_deb button[kind="primary"] {
                    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='2' y='5' width='20' height='14' rx='2' ry='2'></rect><line x1='2' y1='10' x2='22' y2='10'></line><path d='M6 14h.01M10 14h.01'></path></svg>") !important;
                }
                .st-key-pay_pix button[kind="primary"] {
                    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 3L4 11h5l3-3 3 3h5zM12 21l-8-8h5l3 3 3-3h5z'></path></svg>") !important;
                }
                .st-key-pay_cred button[kind="primary"] {
                    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='2' y='5' width='20' height='14' rx='2' ry='2'></rect><line x1='2' y1='10' x2='22' y2='10'></line><circle cx='6' cy='15' r='1.5'></circle><circle cx='18' cy='15' r='1.5'></circle></svg>") !important;
                }
                .st-key-pay_din button[kind="primary"] {
                    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='2' y='6' width='20' height='12' rx='2'></rect><circle cx='12' cy='12' r='2.5'></circle><line x1='6' y1='12' x2='6.01' y2='12'></line><line x1='18' y1='12' x2='18.01' y2='12'></line></svg>") !important;
                }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="payment-method-container">', unsafe_allow_html=True)
            col_p1, col_p2, col_p3, col_p4 = st.columns(4)
            
            with col_p1:
                is_sel = st.session_state['selected_payment'] == 'Débito'
                if st.button("Cartão de Débito", type="primary" if is_sel else "secondary", use_container_width=True, key="pay_deb", disabled=not caixa_aberto):
                    st.session_state['selected_payment'] = 'Débito'
                    st.rerun()
            with col_p2:
                is_sel = st.session_state['selected_payment'] == 'Pix'
                if st.button("PIX", type="primary" if is_sel else "secondary", use_container_width=True, key="pay_pix", disabled=not caixa_aberto):
                    st.session_state['selected_payment'] = 'Pix'
                    st.rerun()
            with col_p3:
                is_sel = st.session_state['selected_payment'] == 'Crédito'
                if st.button("Cartão de Crédito", type="primary" if is_sel else "secondary", use_container_width=True, key="pay_cred", disabled=not caixa_aberto):
                    st.session_state['selected_payment'] = 'Crédito'
                    st.rerun()
            with col_p4:
                is_sel = st.session_state['selected_payment'] == 'Dinheiro'
                if st.button("Dinheiro", type="primary" if is_sel else "secondary", use_container_width=True, key="pay_din", disabled=not caixa_aberto):
                    st.session_state['selected_payment'] = 'Dinheiro'
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<hr style='margin:8px 0; border:0; border-top:1px solid #E5E5EA;'>", unsafe_allow_html=True)
            
            # Passo 4: Lançamento (Permite venda direta ou patio para produtos)
            if tipo_venda == "Produto":
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    btn_patio = st.button("Enviar ao Pátio", type="secondary", use_container_width=True, key="btn_prod_patio", disabled=not caixa_aberto)
                with col_b2:
                    btn_direta = st.button("Finalizar Venda Direta", type="primary", use_container_width=True, key="btn_prod_direta", disabled=not caixa_aberto)
                    
                if btn_patio or btn_direta:
                    if cliente_selecionado and not cliente_selecionado.startswith("-- Selecione"):
                        cli_codigo = cliente_selecionado.split(" |")[0]
                        cliente_ref = db.query(Cliente).filter(Cliente.codigo == cli_codigo).first()
                        cliente_id = cliente_ref.id if cliente_ref else None
                        
                        qtd = db.query(Atendimento).count()
                        codigo_seq = f"OS-{qtd+1:04d}"
                        
                        status_at = "Em andamento" if btn_patio else "Finalizado"
                        conclusao_at = None if btn_patio else obter_hora_local().isoformat()
                        
                        novo_atendimento = Atendimento(
                            codigo=codigo_seq,
                            cliente_id=cliente_id,
                            status=status_at,
                            desconto_total=0.0,
                            valor_total=valor_final,
                            forma_pagamento=st.session_state['selected_payment'],
                            data_criacao=obter_hora_local().isoformat(),
                            data_conclusao=conclusao_at
                        )
                        db.add(novo_atendimento)
                        db.flush()
                        
                        item_ref = db.query(Produto).filter(Produto.nome == item_selecionado).first()
                        ref_id = item_ref.id if item_ref else 0
                        if ref_id > 0:
                            novo_item = ItemAtendimento(
                                atendimento_id=novo_atendimento.id,
                                tipo="Produto",
                                referencia_id=ref_id,
                                valor_cobrado=valor_final
                            )
                            db.add(novo_item)
                        
                        
                        db.commit()
                        
                        # Integration with Financial Module
                        try:
                            if status_at == "Finalizado":
                                from modules.financial import registrar_receita_pdv
                                registrar_receita_pdv(novo_atendimento.id, db)
                        except Exception as e:
                            pass
                        st.session_state['success_msg'] = f"Venda de {item_selecionado} ({codigo_seq}) registrada com sucesso!"
                        st.rerun()
                    else:
                        st.error("Por favor, selecione um cliente cadastrado ou clique em + Novo Cliente para cadastrar um novo.")
            else:
                if st.button("Iniciar Lavagem (Enviar ao Pátio)", type="primary", use_container_width=True, key="btn_serv_patio", disabled=not caixa_aberto):
                    if cliente_selecionado and not cliente_selecionado.startswith("-- Selecione"):
                        cli_codigo = cliente_selecionado.split(" |")[0]
                        cliente_ref = db.query(Cliente).filter(Cliente.codigo == cli_codigo).first()
                        cliente_id = cliente_ref.id if cliente_ref else None
                        
                        qtd = db.query(Atendimento).count()
                        codigo_seq = f"OS-{qtd+1:04d}"
                        
                        novo_atendimento = Atendimento(
                            codigo=codigo_seq,
                            cliente_id=cliente_id,
                            status="Em andamento",
                            desconto_total=0.0,
                            valor_total=valor_final,
                            forma_pagamento=st.session_state['selected_payment'],
                            data_criacao=obter_hora_local().isoformat()
                        )
                        db.add(novo_atendimento)
                        db.flush()
                        
                        item_ref = db.query(Servico).filter(Servico.nome == item_selecionado).first()
                        ref_id = item_ref.id if item_ref else 0
                        if ref_id > 0:
                            novo_item = ItemAtendimento(
                                atendimento_id=novo_atendimento.id,
                                tipo="Serviço",
                                referencia_id=ref_id,
                                valor_cobrado=valor_final
                            )
                            db.add(novo_item)
                        
                        db.commit()
                        st.session_state['success_msg'] = f"Atendimento {codigo_seq} lançado com sucesso no pátio!"
                        st.rerun()
                    else:
                        st.error("Por favor, selecione um cliente cadastrado ou clique em + Novo Cliente para cadastrar um novo.")
                    
        # Passo 4: Opções Avançadas (Carrinho, Descontos, Produtos)
        with st.expander("⚙️ Mais Opções (Vendas complexas, Vários itens, Produtos ou Descontos)"):
            st.markdown("Use esta área apenas para vendas complexas que exijam múltiplos itens ou descontos autorizados.")
            
            # Checkbox para ativar o modo avançado
            modo_avancado = st.checkbox("Ativar Lançamento com Carrinho de Compras", value=False)
            
            if modo_avancado:
                # Seleção de tipo, item, valor e botão Adicionar
                col_tipo, col_item, col_valor = st.columns([1, 2, 1], vertical_alignment="bottom")
                tipo_item = col_tipo.selectbox("Tipo Item", ["Serviço", "Produto"], key="cart_tipo")
                
                item_opcoes = []
                valor_sugerido_c = 0.0
                
                if tipo_item == "Serviço":
                    item_opcoes = [s.nome for s in servicos]
                    item_selecionado = col_item.selectbox("Serviço Item", item_opcoes if item_opcoes else ["Nenhum serviço"], key="cart_serv")
                    if item_selecionado and item_selecionado != "Nenhum serviço":
                        serv = next((s for s in servicos if s.nome == item_selecionado), None)
                        valor_sugerido_c = serv.preco_padrao if serv else 0.0
                else:
                    item_opcoes = [p.nome for p in produtos]
                    item_selecionado = col_item.selectbox("Produto Item", item_opcoes if item_opcoes else ["Nenhum produto"], key="cart_prod")
                    if item_selecionado and item_selecionado != "Nenhum produto":
                        prod = next((p for p in produtos if p.nome == item_selecionado), None)
                        valor_sugerido_c = prod.preco_venda if prod else 0.0
                        
                valor_final_c = col_valor.number_input("Valor Item", value=valor_sugerido_c, min_value=0.0, key="cart_valor")
                
                col_btn_add, col_check = st.columns([1, 1], vertical_alignment="bottom")
                mais_itens = col_check.checkbox("Há mais itens neste atendimento?", value=True, key="cart_mais_itens")
                
                if col_btn_add.button("Adicionar Item ao Carrinho", type="secondary", use_container_width=True, key="cart_add_btn"):
                    if item_selecionado and "Nenhum" not in item_selecionado:
                        st.session_state['pdv_cart'].append({
                            "tipo": tipo_item,
                            "nome": item_selecionado,
                            "valor": valor_final_c
                        })
                        st.success(f"{item_selecionado} adicionado!")
                        if not mais_itens:
                            st.rerun()
                
                # Exibir Carrinho
                if st.session_state['pdv_cart']:
                    st.markdown("#### Itens no Carrinho:")
                    total = 0.0
                    for idx_i, item in enumerate(st.session_state['pdv_cart']):
                        st.markdown(f"- **{item['tipo']}**: {item['nome']} - R$ {item['valor']:.2f}")
                        total += item['valor']
                    
                    st.markdown(f"**Subtotal: R$ {total:.2f}**")
                    
                    col_f, col_d = st.columns(2)
                    forma_pagamento_c = col_f.selectbox("Forma de Pagamento (Carrinho)", ["Dinheiro", "Pix", "Débito", "Crédito"], key="cart_pgto")
                    desconto = col_d.number_input("Desconto (%)", min_value=0.0, max_value=100.0, value=0.0, key="cart_desconto")
                    
                    desconto_valor = total * (desconto / 100)
                    total_com_desconto = total - desconto_valor
                    
                    # Senha do Gerente se desconto > 5% (Senha: "admin")
                    gerente_aprovado = True
                    if desconto > 5.0:
                        st.warning("⚠️ Desconto maior que 5% exige autorização do gerente.")
                        senha = st.text_input("Senha do Gerente", type="password", key="cart_senha_gerente")
                        if senha != "admin": # Alterado para "admin"
                            gerente_aprovado = False
                            if senha:
                                st.error("Senha incorreta!")
                    
                    st.markdown(f"<h3 style='color: var(--success);'>Total Final: R$ {total_com_desconto:.2f}</h3>", unsafe_allow_html=True)
                    
                    # Salvar Ordem Avançada
                    if st.button("SALVAR ATENDIMENTO (Carrinho)", type="primary", disabled=not gerente_aprovado, use_container_width=True, key="cart_save_btn"):
                        if cliente_selecionado and not cliente_selecionado.startswith("-- Selecione"):
                            # Extrair código do cliente
                            cli_codigo = cliente_selecionado.split(" |")[0]
                            cliente_ref = db.query(Cliente).filter(Cliente.codigo == cli_codigo).first()
                            cliente_id = cliente_ref.id if cliente_ref else None
                            
                            # Gerar codigo sequencial OS
                            qtd = db.query(Atendimento).count()
                            codigo_seq = f"OS-{qtd+1:04d}"
                            
                            novo_atendimento = Atendimento(
                                codigo=codigo_seq,
                                cliente_id=cliente_id,
                                status="Em andamento",
                                desconto_total=desconto_valor,
                                valor_total=total_com_desconto,
                                forma_pagamento=forma_pagamento_c,
                                data_criacao=obter_hora_local().isoformat() # Fuso Brasília
                            )
                            db.add(novo_atendimento)
                            db.flush()
                            
                            for cart_item in st.session_state['pdv_cart']:
                                ref_id = 0
                                if cart_item['tipo'] == "Serviço":
                                    ref_id = db.query(Servico).filter(Servico.nome == cart_item['nome']).first().id
                                else:
                                    ref_id = db.query(Produto).filter(Produto.nome == cart_item['nome']).first().id
                                    
                                novo_item = ItemAtendimento(
                                    atendimento_id=novo_atendimento.id,
                                    tipo=cart_item['tipo'],
                                    referencia_id=ref_id,
                                    valor_cobrado=cart_item['valor']
                                )
                                db.add(novo_item)
                                
                            db.commit()
                            st.session_state['pdv_cart'] = [] # Limpa o carrinho
                            st.session_state['success_msg'] = f"Atendimento {codigo_seq} lançado com sucesso no pátio!"
                            st.rerun()
                    if st.button("Limpar Carrinho", key="cart_clear_btn"):
                        st.session_state['pdv_cart'] = []
                        st.rerun()
    # ABA 2: Em Andamento
    # ==========================================
    with tab2:
        st.markdown(f"<h3 style='margin:12px 0;'>{gold_icon('car')} Pátio (Em Andamento)</h3>", unsafe_allow_html=True)
        atendimentos_abertos = db.query(Atendimento).filter(Atendimento.status == "Em andamento").all()
        
        if not atendimentos_abertos:
            st.info("Nenhum veículo em andamento no momento.")
            
        for at in atendimentos_abertos:
            cliente_at = db.query(Cliente).filter(Cliente.id == at.cliente_id).first()
            itens_at = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id == at.id).all()
            
            # Calcular horário de entrada e tempo decorrido (usando naive UTC-3 datetimes)
            try:
                entrada_dt = datetime.fromisoformat(at.data_criacao).replace(tzinfo=None)
                decorrido = obter_hora_local() - entrada_dt
                horas, resto = divmod(decorrido.total_seconds(), 3600)
                minutos, _ = divmod(resto, 60)
                if horas > 0:
                    tempo_decorrido = f"há {int(horas)}h {int(minutos)}m"
                else:
                    tempo_decorrido = f"há {int(minutos)}m"
                hora_entrada = entrada_dt.strftime("%H:%M")
            except Exception:
                hora_entrada = "--:--"
                tempo_decorrido = "tempo desconhecido"
            
            with st.container(border=True):
                col1, col2 = st.columns([1.1, 1.4], vertical_alignment="center")
                with col1:
                    cliente_nome = cliente_at.nome if cliente_at else 'Desconhecido'
                    cliente_veiculo = f"{cliente_at.modelo_veiculo} - {cliente_at.placa_veiculo}" if (cliente_at and cliente_at.modelo_veiculo) else (cliente_at.placa_veiculo if cliente_at else '')
                    
                    st.markdown(f"<div style='margin-bottom: 2px; font-size: 15px; font-weight: bold; color: var(--text-main);'>{gold_icon('car')} [{at.codigo}] {cliente_nome}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='margin-bottom: 2px; font-size: 12px; color: var(--text-sec);'><b>Veículo:</b> {cliente_veiculo}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='margin-bottom: 2px; font-size: 12px; color: var(--text-sec);'>{gold_icon('clock')} <b>Entrada:</b> {hora_entrada} <span style='color: var(--warning); font-weight: bold;'>({tempo_decorrido})</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='margin-bottom: 2px; font-size: 12px; color: var(--text-sec);'><b>Total:</b> R$ {at.valor_total:.2f} | <b>Pgto:</b> {at.forma_pagamento}</div>", unsafe_allow_html=True)
                    
                    detalhes = []
                    for i in itens_at:
                        if i.tipo == "Serviço":
                            s = db.query(Servico).filter(Servico.id == i.referencia_id).first()
                            detalhes.append(f"{gold_icon('service')} {s.nome if s else 'Serviço'}")
                        else:
                            p = db.query(Produto).filter(Produto.id == i.referencia_id).first()
                            detalhes.append(f"{gold_icon('box')} {p.nome if p else 'Produto'}")
                    st.markdown(f"<div style='font-size: 12px; color: var(--text-sec);'>{' | '.join(detalhes)}</div>", unsafe_allow_html=True)
                    
                with col2:
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    if col_btn1.button("Concluir", key=f"concluir_{at.id}", use_container_width=True):
                        dialog_concluir_atendimento(at.id)
                        
                    if col_btn2.button("Editar", key=f"editar_{at.id}", use_container_width=True):
                        dialog_editar_atendimento(at.id)
                        
                    if col_btn3.button("Excluir", key=f"excluir_{at.id}", use_container_width=True):
                        dialog_cancelar_atendimento(at.id)

    # ==========================================
    # ABA 3: Concluído (Histórico)
    # ==========================================
    with tab3:
        st.markdown(f"<h3 style='margin:12px 0;'>{gold_icon('calendar')} Histórico de Atendimentos</h3>", unsafe_allow_html=True)
        
        # Filtros (adicionando filtro por Serviço/Produto)
        with st.container(border=True):
            col_f1, col_f2, col_f3 = st.columns(3)
            filtro_cliente = col_f1.selectbox("Filtrar por Cliente", ["Todos"] + [c.nome for c in clientes if c.codigo != "CLI-0000"])
            
            # Lista de serviços e produtos cadastrados para filtrar
            opcoes_itens = ["Todos os Itens"]
            opcoes_itens += [f"[Serviço] {s.nome}" for s in servicos]
            opcoes_itens += [f"[Produto] {p.nome}" for p in produtos]
            filtro_item = col_f2.selectbox("Filtrar por Serviço/Produto", opcoes_itens)
            
            filtro_status = col_f3.selectbox("Status", ["Finalizado", "Cancelado"])
        
        # Ordenação de cima para baixo pelo último serviço concluído (data_conclusao desc)
        query_finalizados = db.query(Atendimento).filter(Atendimento.status == filtro_status).order_by(Atendimento.data_conclusao.desc(), Atendimento.id.desc())
        
        if filtro_cliente != "Todos":
            c_ref = db.query(Cliente).filter(Cliente.nome == filtro_cliente).first()
            if c_ref:
                query_finalizados = query_finalizados.filter(Atendimento.cliente_id == c_ref.id)
                
        # Filtro adicional de Item (Serviço ou Produto)
        if filtro_item != "Todos os Itens":
            tipo_filtro = "Serviço" if filtro_item.startswith("[Serviço]") else "Produto"
            nome_filtro = filtro_item[10:] # Remove o prefixo '[Serviço] ' ou '[Produto] '
            
            if tipo_filtro == "Serviço":
                item_ref = db.query(Servico).filter(Servico.nome == nome_filtro).first()
            else:
                item_ref = db.query(Produto).filter(Produto.nome == nome_filtro).first()
                
            if item_ref:
                # Buscar IDs de atendimentos que contêm este item
                at_ids_com_item = db.query(ItemAtendimento.atendimento_id).filter(
                    ItemAtendimento.tipo == tipo_filtro,
                    ItemAtendimento.referencia_id == item_ref.id
                ).all()
                ids_lista = [r[0] for r in at_ids_com_item]
                query_finalizados = query_finalizados.filter(Atendimento.id.in_(ids_lista))
            else:
                # Se o item não for encontrado, força retorno vazio
                query_finalizados = query_finalizados.filter(Atendimento.id == -1)
            
        atendimentos_finalizados = query_finalizados.all()
        
        if not atendimentos_finalizados:
            st.info(f"Nenhum atendimento {filtro_status.lower()} encontrado.")
            
        for at in atendimentos_finalizados:
            cliente_at = db.query(Cliente).filter(Cliente.id == at.cliente_id).first()
            itens_at = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id == at.id).all()
            
            # Calcular entrada, saída e duração (usando naive UTC-3 datetimes)
            try:
                entrada_dt = datetime.fromisoformat(at.data_criacao).replace(tzinfo=None)
                hora_entrada = entrada_dt.strftime("%d/%m %H:%M")
                if at.data_conclusao:
                    conclusao_dt = datetime.fromisoformat(at.data_conclusao).replace(tzinfo=None)
                    hora_saida = conclusao_dt.strftime("%H:%M")
                    duracao = conclusao_dt - entrada_dt
                    horas, resto = divmod(duracao.total_seconds(), 3600)
                    minutos, _ = divmod(resto, 60)
                    if horas > 0:
                        duracao_str = f"{int(horas)}h {int(minutos)}m"
                    else:
                        duracao_str = f"{int(minutos)}m"
                else:
                    hora_saida = "--:--"
                    duracao_str = "Desconhecido"
            except Exception:
                hora_entrada = "--:--"
                hora_saida = "--:--"
                duracao_str = "Desconhecido"
            
            cliente_nome = cliente_at.nome if cliente_at else 'Desconhecido'
            cliente_veiculo = f"{cliente_at.modelo_veiculo} - {cliente_at.placa_veiculo}" if (cliente_at and cliente_at.modelo_veiculo) else (cliente_at.placa_veiculo if cliente_at else '')
            
            # Buscar detalhes dos itens concluídos para exibição
            detalhes = []
            for i in itens_at:
                if i.tipo == "Serviço":
                    s = db.query(Servico).filter(Servico.id == i.referencia_id).first()
                    detalhes.append(f"{gold_icon('service')} {s.nome if s else 'Serviço'}")
                else:
                    p = db.query(Produto).filter(Produto.id == i.referencia_id).first()
                    detalhes.append(f"{gold_icon('box')} {p.nome if p else 'Produto'}")
            detalhes_str = f"<div style='font-size: 12px; color: #86868B; margin-top: 3px;'><b>Itens:</b> {' | '.join(detalhes)}</div>" if detalhes else ""
            
            # Layout super compacto em HTML para o histórico
            obs_html = f"<div style='font-size: 11px; color: #86868B; font-style: italic; background-color: #F5F5F7; padding: 4px 8px; border-radius: 4px; margin-top: 4px;'>Obs: {at.observacoes}</div>" if at.observacoes else ""
            status_dot = f"<span style='color: var(--success); font-weight: bold;'>● Concluído</span>" if at.status == "Finalizado" else f"<span style='color: var(--danger); font-weight: bold;'>● Cancelado</span>"
            
            tempo_html = ""
            if at.status == "Finalizado":
                tempo_html = f"| {gold_icon('clock')} <b>Entrada:</b> {hora_entrada} | <b>Saída:</b> {hora_saida} <i>({duracao_str})</i>"
            else:
                tempo_html = f"| {gold_icon('calendar')} <b>Data:</b> {hora_entrada}"

            st.markdown(f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E5E5EA; border-radius: 8px; padding: 6px 12px; margin-bottom: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.01);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                    <span style="font-size: 14px; font-weight: bold; color: #1D1D1F;">{gold_icon('car')} [{at.codigo}] {cliente_nome}</span>
                    <span style="font-size: 12px;">{status_dot}</span>
                </div>
                <div style="font-size: 12px; color: #86868B; line-height: 1.4;">
                    <b>Veículo:</b> {cliente_veiculo} | <b>Total:</b> R$ {at.valor_total:.2f} | <b>Pgto:</b> {at.forma_pagamento} {tempo_html}
                </div>
                {detalhes_str}
                {obs_html}
            </div>
            """, unsafe_allow_html=True)

    # ==========================================
    # ABA 4: Resumo do Dia
    # ==========================================
    with tab4:
        st.markdown(f"<h3 style='margin:12px 0;'>{gold_icon('chart')} Resumo Operacional</h3>", unsafe_allow_html=True)
        
        # Filtro de data para garantir que se trata do dia específico
        filtro_data_resumo = st.date_input("Data do Resumo", value=obter_hora_local().date(), key="dia_resumo_filter")
        data_busca = filtro_data_resumo.isoformat()
        
        # Consultar atendimentos concluídos na data selecionada
        atendimentos_dia = db.query(Atendimento).filter(
            Atendimento.status == "Finalizado",
            Atendimento.data_conclusao.like(f"{data_busca}%")
        ).all()
        
        # Estatísticas do dia
        qtd_atendimentos = len(atendimentos_dia)
        qtd_servicos = 0
        qtd_produtos = 0
        valor_servicos = 0.0
        valor_produtos = 0.0
        tempos_servicos = []
        
        # Agrupamento de itens executados
        itens_executados = {} # { (tipo, nome): { "qtd": 0, "valor": 0.0 } }
        
        # Contagem por hora para o gráfico (24h)
        volume_por_hora = [0] * 24
        
        for at in atendimentos_dia:
            # Registrar hora de conclusão para o gráfico
            if at.data_conclusao:
                try:
                    dt_con = datetime.fromisoformat(at.data_conclusao)
                    volume_por_hora[dt_con.hour] += 1
                except Exception:
                    pass
            
            # Calcular duração (Naive datetimes)
            if at.data_criacao and at.data_conclusao:
                try:
                    ent = datetime.fromisoformat(at.data_criacao).replace(tzinfo=None)
                    con = datetime.fromisoformat(at.data_conclusao).replace(tzinfo=None)
                    duracao_min = (con - ent).total_seconds() / 60.0
                    tempos_servicos.append(duracao_min)
                except Exception:
                    pass
            
            # Carregar itens
            itens = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id == at.id).all()
            for i in itens:
                if i.tipo == "Serviço":
                    qtd_servicos += 1
                    valor_servicos += i.valor_cobrado
                    s = db.query(Servico).filter(Servico.id == i.referencia_id).first()
                    nome_item = s.nome if s else "Serviço Desconhecido"
                else:
                    qtd_produtos += 1
                    valor_produtos += i.valor_cobrado
                    p = db.query(Produto).filter(Produto.id == i.referencia_id).first()
                    nome_item = p.nome if p else "Produto Desconhecido"
                
                key = (i.tipo, nome_item)
                if key not in itens_executados:
                    itens_executados[key] = {"qtd": 0, "valor": 0.0}
                itens_executados[key]["qtd"] += 1
                itens_executados[key]["valor"] += i.valor_cobrado

        # Calcular tempo médio dos serviços
        if tempos_servicos:
            media_min = sum(tempos_servicos) / len(tempos_servicos)
            if media_min >= 60:
                h, m = divmod(media_min, 60)
                tempo_medio_str = f"{int(h)}h {int(m)}m"
            else:
                tempo_medio_str = f"{int(media_min)} min"
        else:
            tempo_medio_str = "Sem registros"
            
        valor_total = valor_servicos + valor_produtos
        
        # Renderizar cartões de resumo
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.markdown(f"""
            <div style="background-color:#FFFFFF; padding:12px; border-radius:10px; border:1px solid #E5E5EA; text-align:center; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <div style="font-size:12px; color:#86868B; font-weight:bold;">SERVIÇOS</div>
                <div style="font-size:20px; font-weight:bold; color:#1D1D1F; margin:4px 0;">R$ {valor_servicos:.2f}</div>
                <div style="font-size:11px; color:#34C759; font-weight:bold;">{qtd_servicos} executados</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_c2:
            st.markdown(f"""
            <div style="background-color:#FFFFFF; padding:12px; border-radius:10px; border:1px solid #E5E5EA; text-align:center; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <div style="font-size:12px; color:#86868B; font-weight:bold;">PRODUTOS</div>
                <div style="font-size:20px; font-weight:bold; color:#1D1D1F; margin:4px 0;">R$ {valor_produtos:.2f}</div>
                <div style="font-size:11px; color:#34C759; font-weight:bold;">{qtd_produtos} vendidos</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_c3:
            st.markdown(f"""
            <div style="background-color:#FFFFFF; padding:12px; border-radius:10px; border:1px solid #E5E5EA; text-align:center; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <div style="font-size:12px; color:#86868B; font-weight:bold;">TEMPO MÉDIO</div>
                <div style="font-size:20px; font-weight:bold; color:#1D1D1F; margin:4px 0;">{tempo_medio_str}</div>
                <div style="font-size:11px; color:#86868B;">{qtd_atendimentos} concluídos</div>
            </div>
            """, unsafe_allow_html=True)
            
        # Totalizador de Faturamento
        st.markdown(f"""
        <div style="background-color:#F5F5F7; padding:10px 16px; border-radius:8px; border:1px solid #E5E5EA; margin-top:12px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:bold; font-size:14px; color:#1D1D1F;">VALOR TOTAL FATURADO:</span>
            <span style="font-weight:bold; font-size:18px; color:#007AFF;">R$ {valor_total:.2f}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Lista com serviços e produtos executados
        st.markdown(f"<h4 style='margin:12px 0;'>{gold_icon('service')} Serviços e Produtos Executados</h4>", unsafe_allow_html=True)
        if itens_executados:
            for (tipo, nome_item), dados in itens_executados.items():
                icon_tipo = gold_icon('service') if tipo == "Serviço" else gold_icon('box')
                st.markdown(f"""
                <div style="background-color:#FFFFFF; border:1px solid #E5E5EA; border-radius:6px; padding:6px 12px; margin-bottom:4px; display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:13px; color:#1D1D1F;">{icon_tipo} <b>{nome_item}</b> <span style='color:#86868B;'>(x{dados['qtd']})</span></span>
                    <span style="font-size:13px; font-weight:bold; color:#1D1D1F;">R$ {dados['valor']:.2f}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhum serviço ou produto executado/vendido nesta data.")
            
        st.markdown("---")
        
        # Gráfico do dia mostrando volume de serviços por hora
        st.markdown(f"<h4 style='margin:12px 0;'>{gold_icon('clock')} Volume de Atendimento por Hora</h4>", unsafe_allow_html=True)
        
        # Preparar dataframe para gráfico
        import pandas as pd
        df_horas = pd.DataFrame({
            "Horário": [f"{h:02d}:00" for h in range(24)],
            "Volume": volume_por_hora
        })
        # Mostrar o intervalo de horário de pico padrão (07h às 20h)
        df_comercial = df_horas.iloc[7:21]
        
        st.bar_chart(df_comercial, x="Horário", y="Volume", use_container_width=True)
        
        # Identificação de Horas Quentes e Frias
        horas_ativas = [(h, vol) for h, vol in enumerate(volume_por_hora) if vol > 0]
        
        if horas_ativas:
            max_vol = max(vol for h, vol in horas_ativas)
            quentes_lista = [f"{h:02d}:00" for h, vol in horas_ativas if vol == max_vol]
            quentes_str = ", ".join(quentes_lista)
            
            # Horas frias: intervalo comercial padrão (08h às 18h) com menor volume
            frias_lista = []
            for h in range(8, 19):
                vol = volume_por_hora[h]
                if vol < max_vol:
                    frias_lista.append((h, vol))
            
            if frias_lista:
                min_vol_comercial = min(vol for h, vol in frias_lista)
                frias_filtradas = [f"{h:02d}:00" for h, vol in frias_lista if vol == min_vol_comercial]
                frias_str = ", ".join(frias_filtradas)
            else:
                frias_str = "Nenhuma"
        else:
            quentes_str = "Sem atividades faturadas"
            frias_str = "Sem atividades faturadas"
            
        col_q, col_f = st.columns(2)
        with col_q:
            st.markdown(f"""
            <div style="background-color:#FFF2E6; border-left:4px solid #FF9500; padding:10px; border-radius:4px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                <span style="font-weight:bold; font-size:12px; color:#FF9500;">{gold_icon('fire')} HORAS QUENTES (PICO)</span><br>
                <span style="font-size:13px; font-weight:bold; color:#1D1D1F;">{quentes_str}</span>
            </div>
            """, unsafe_allow_html=True)
            
        with col_f:
            st.markdown(f"""
            <div style="background-color:#EBF5FF; border-left:4px solid #007AFF; padding:10px; border-radius:4px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                <span style="font-weight:bold; font-size:12px; color:#007AFF;">{gold_icon('snowflake')} HORAS FRIAS (OCIOSIDADE)</span><br>
                <span style="font-size:13px; font-weight:bold; color:#1D1D1F;">{frias_str}</span>
            </div>
            """, unsafe_allow_html=True)

