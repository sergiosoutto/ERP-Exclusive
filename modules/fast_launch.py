import streamlit as st
import pandas as pd
from db_config import get_db, Cliente, Servico, Produto, Atendimento, ItemAtendimento, FormaPagamento, ServicoInsumo
from datetime import datetime, timedelta, timezone
import unicodedata

# Helper para remover acentuação de strings
def remover_acentos(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

dialog_decorator = st.dialog if hasattr(st, "dialog") else st.experimental_dialog

def obter_hora_local():
    fuso_brasil = timezone(timedelta(hours=-3))
    return datetime.now(fuso_brasil).replace(tzinfo=None)

def formatar_telefone(tel_str):
    digitos = "".join([c for c in tel_str if c.isdigit()])
    if len(digitos) == 11: return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    elif len(digitos) == 10: return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    return tel_str

def formatar_tempo(delta):
    horas, resto = divmod(delta.seconds, 3600)
    minutos, _ = divmod(resto, 60)
    if delta.days > 0:
        return f"{delta.days}d {horas}h {minutos}m"
    if horas > 0:
        return f"{horas}h {minutos}m"
    return f"{minutos}m"

def gold_icon(icon_name):
    icons = {
        "user": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>',
        "service": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path></svg>',
        "payment": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect><line x1="1" y1="10" x2="23" y2="10"></line></svg>',
        "lightning": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>',
        "check": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:4px;"><polyline points="20 6 9 17 4 12"></polyline></svg>',
        "clock": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:4px;"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>',
        "chart": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
        "fire": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path></svg>',
        "wrench": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path></svg>'
    }
    return icons.get(icon_name, "")


@dialog_decorator("Cadastrar Novo Cliente")
def dialog_novo_cliente():
    db = next(get_db())
    qtd = db.query(Cliente).count()
    codigo_seq = f"CLI-{qtd+1:04d}"
    
    st.info(f"Código: **{codigo_seq}**")
    novo_nome = st.text_input("Nome do Cliente")
    novo_tel_num = st.text_input("Telefone com DDD", placeholder="61999999999")
    nova_placa = st.text_input("Placa do Veículo")
    novo_modelo = st.text_input("Modelo do Veículo")
    
    if st.button("Salvar Cliente", type="primary", use_container_width=True):
        if novo_nome:
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
            st.success(f"Cliente cadastrado com sucesso!")
            st.rerun()

@dialog_decorator("Confirmar Exclusão")
def dialog_excluir_os(at_id):
    st.warning("Tem certeza que deseja excluir esta OS permanentemente?")
    db = next(get_db())
    if st.button("Excluir Permanentemente", type="primary", use_container_width=True):
        at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
        if at:
            db.delete(at)
            db.commit()
            st.session_state['success_msg'] = f"OS excluída."
            st.rerun()

@dialog_decorator("Editar OS")
def dialog_editar_os(at_id):
    db = next(get_db())
    at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
    if not at: return
    
    st.write(f"Editando OS: **{at.codigo}**")
    
    # 1. Gerenciar Itens Atuais
    st.markdown("#### Serviços Lançados")
    itens = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id == at.id).all()
    
    # Dicionarios para capturar mudancas
    mudancas_valor = {}
    itens_para_excluir = set()
    
    if not itens:
        st.write("Nenhum serviço lançado.")
    else:
        for i in itens:
            s = db.query(Servico).filter(Servico.id == i.referencia_id).first()
            n = s.nome if s else "Desconhecido"
            
            # Usar colunas para alinhar input e botao de deletar
            c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
            with c1:
                novo_v = st.number_input(f"{n}", value=float(i.valor_cobrado), min_value=0.0, key=f"edit_v_{i.id}")
                mudancas_valor[i.id] = novo_v
            with c2:
                # Se o botao for clicado, nao exclui imediatamente para nao recarregar o form no meio
                deletar = st.checkbox("Excluir", key=f"del_{i.id}")
                if deletar:
                    itens_para_excluir.add(i.id)

    st.markdown("---")
    # 2. Adicionar Novos Serviços
    st.markdown("#### Adicionar Mais Serviços")
    servicos = db.query(Servico).all()
    servico_nomes = {s.nome: s for s in servicos}
    
    selecionados = st.multiselect("Selecione serviços adicionais", list(servico_nomes.keys()))
    
    novos_valores = {}
    for sel in selecionados:
        s_obj = servico_nomes[sel]
        val = st.number_input(f"Valor para {sel} (R$)", value=s_obj.preco_padrao, min_value=0.0, key=f"add_{sel}")
        novos_valores[s_obj.id] = val
        
    if st.button("Confirmar Alterações", type="primary", use_container_width=True):
        # Aplicar exclusões
        for i in itens:
            if i.id in itens_para_excluir:
                db.delete(i)
            else:
                # Atualizar valores alterados
                if i.id in mudancas_valor:
                    i.valor_cobrado = mudancas_valor[i.id]
                    
        # Inserir novos
        for s_id, v in novos_valores.items():
            novo_item = ItemAtendimento(atendimento_id=at.id, tipo="Serviço", referencia_id=s_id, valor_cobrado=v)
            db.add(novo_item)
            
        db.flush() # Para garantir que a soma abaixo pega tudo certo
        
        # Recalcular valor total da OS
        itens_finais = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id == at.id).all()
        soma = sum(i.valor_cobrado for i in itens_finais)
        at.valor_total = soma
        
        db.commit()
        st.session_state['success_msg'] = "OS atualizada com sucesso!"
        st.rerun()

@dialog_decorator("Concluir OS")
def dialog_checkout(at_id):
    db = next(get_db())
    at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
    if not at: return
    
    st.write(f"Finalizando OS: **{at.codigo}**")
    
    # Formas de pagamento do DB
    fps = db.query(FormaPagamento).all()
    fp_nomes = [f.nome for f in fps]
    
    fp_selecionada = st.selectbox("Forma de Pagamento", fp_nomes)
    forma_obj = next((f for f in fps if f.nome == fp_selecionada), None)
    
    parcelas = 1
    if forma_obj and "Cartão" in forma_obj.nome:
        parcelas = st.number_input("Qtd Parcelas", min_value=1, max_value=12, value=1)
        
    valor_base = st.number_input("Valor Cobrado (Pode ser alterado p/ desconto/acréscimo)", value=at.valor_total, min_value=0.0)
    
    # Calculo Juros
    juros = 0.0
    if forma_obj:
        if parcelas == 1:
            juros = valor_base * (forma_obj.taxa_juros_vista / 100)
        else:
            juros = valor_base * (forma_obj.taxa_juros_parcela / 100) * parcelas
            
    valor_final = valor_base + juros
    
    if juros > 0:
        st.write(f"Juros Aplicados: R$ {juros:.2f}")
    st.markdown(f"### Total a Pagar: R$ {valor_final:.2f}")
    
    # Automate Observation based on discount/addition
    auto_obs = ""
    if valor_base < at.valor_total:
        auto_obs = f"[Desconto de R$ {at.valor_total - valor_base:.2f}] "
    elif valor_base > at.valor_total:
        auto_obs = f"[Acréscimo de R$ {valor_base - at.valor_total:.2f}] "
        
    obs = st.text_input("Observação", value=auto_obs, placeholder="Ex: Higienização impecável...")
    
    if st.button("Confirmar Pagamento e Baixar Estoque", type="primary", use_container_width=True):
        at.status = "Finalizado"
        at.data_conclusao = obter_hora_local().isoformat()
        at.observacoes = obs
        at.forma_pagamento = fp_selecionada
        at.parcelas = parcelas
        at.valor_total = valor_final # Atualiza valor final
        
        # Baixa de Insumos
        itens = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id == at.id).all()
        for i in itens:
            if i.tipo == "Serviço":
                # Acha os insumos do servico
                s_insumos = db.query(ServicoInsumo).filter(ServicoInsumo.servico_id == i.referencia_id).all()
                for si in s_insumos:
                    prod = db.query(Produto).filter(Produto.id == si.produto_id).first()
                    if prod:
                        prod.quantidade_estoque -= si.quantidade_utilizada
                        
        db.commit()
        
        try:
            from modules.financial import registrar_receita_pdv
            registrar_receita_pdv(at.id, db)
        except Exception as e: pass
        
        st.session_state['success_msg'] = f"Venda Finalizada! Baixa de insumos concluída."
        st.rerun()

def render_fast_launch():
    # CSS Customizado mínimo e seguro
    st.markdown("""
        <style>
            div[data-testid="stVerticalBlockBorderWrapper"] > div {
                padding: 6px 10px !important;
                gap: 2px !important;
            }
            div[data-testid="stVerticalBlockBorderWrapper"] {
                margin-bottom: -10px !important;
            }
            
            /* Estilo exato do seu outro App para manter as "Pílulas" em linha perfeitamente */
            div[data-testid="stPills"] > div { 
                display: flex; 
                justify-content: center; 
                gap: 5px; 
                width: 100%;
            }
            div[data-testid="stPills"] button { 
                flex: 1 1 0px !important;
                padding: 0 4px !important; 
                min-height: 35px !important;
                border-radius: 8px !important; /* Estética um pouco menos arredondada para remeter a botão */
                font-size: 11px !important;
                font-weight: 500 !important;
                background-color: white !important;
                border: 1px solid #e0e6eb !important;
                color: #4a5568 !important;
                white-space: nowrap !important;
            }
            
            /* Fazer a primeira pílula (Concluir) ficar dourada por padrão (Cobertura Ampla Absoluta) */
            div[data-testid="stPills"] button:first-child,
            div[data-testid="stPills"] > div > button:first-child,
            div[data-testid="stPills"] > div > div > button:first-child,
            div[data-testid="stPills"] [role="radiogroup"] button:nth-child(1),
            div[data-testid="stPills"] button[data-testid="stPill"]:nth-of-type(1) {
                background-color: #C5A059 !important;
                color: white !important;
                border-color: #C5A059 !important;
            }
            div[data-testid="stPills"] button:first-child *,
            div[data-testid="stPills"] > div > button:first-child *,
            div[data-testid="stPills"] > div > div > button:first-child *,
            div[data-testid="stPills"] [role="radiogroup"] button:nth-child(1) *,
            div[data-testid="stPills"] button[data-testid="stPill"]:nth-of-type(1) * {
                color: white !important;
            }
            
            /* Pílula ativa (genérica caso clique em outra) */
            div[data-testid="stPills"] button[data-testid="stPillActive"] {
                opacity: 0.8 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    if 'success_msg' not in st.session_state:
        st.session_state['success_msg'] = None
        
    if st.session_state['success_msg']:
        st.success(st.session_state['success_msg'])
        if st.button("OK", use_container_width=True):
            st.session_state['success_msg'] = None
            st.rerun()

    db = next(get_db())
    hoje = datetime.now()
    hoje_inicio = hoje.replace(hour=0, minute=0, second=0, microsecond=0)
    
    st.markdown(f"### {gold_icon('rocket')} Lançamento Rápido de OS")
    
    # Reimplementando a obtenção das OS do patio e os contadores corretos
    em_andamento = db.query(Atendimento).filter(Atendimento.status == "Em Andamento").order_by(Atendimento.id.asc()).all()
    qtd_andamento = len(em_andamento)
    
    concluidos_hoje = db.query(Atendimento).filter(Atendimento.status == "Finalizado").all()
    qtd_concluido = len(concluidos_hoje)
    
    lbl_patio = f"Pátio ({qtd_andamento})" if qtd_andamento > 0 else "Pátio"
    lbl_hist = f"Histórico ({qtd_concluido})" if qtd_concluido > 0 else "Histórico"
    
    tab1, aba_patio, tab3, tab4 = st.tabs(["Novo", lbl_patio, lbl_hist, "Resumo"])
    
    # ==========================================
    # ABA 1: NOVO ATENDIMENTO
    # ==========================================
    with tab1:
        st.markdown(f"<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            busca_cliente = st.text_input("Pesquisar Cliente", placeholder="Nome ou Placa...")
            if st.button("Novo Cliente", use_container_width=True): dialog_novo_cliente()
            
            termo = remover_acentos(busca_cliente.strip().lower())
            cliente_opcoes = ["-- Selecione o Cliente --"]
            clientes = db.query(Cliente).all()
            for c in clientes:
                if c.codigo == "CLI-0000": continue
                nome = remover_acentos(c.nome or "").lower()
                placa = remover_acentos(c.placa_veiculo or "").lower()
                if termo and (termo not in nome and termo not in placa): continue
                cliente_opcoes.append(f"{c.codigo} | {c.nome or 'Desconhecido'} ({c.placa_veiculo or 'Sem Placa'})")
            
            index_sel = 1 if len(cliente_opcoes) == 2 else 0
            cliente_selecionado = st.selectbox("Cliente", cliente_opcoes, index=index_sel, label_visibility="collapsed")
            
            st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
            
            st.markdown(f"<label style='font-size:13px; font-weight:500;'>{gold_icon('service')} Serviço Principal</label>", unsafe_allow_html=True)
            servicos = db.query(Servico).all()
            servico_opcoes = {s.nome: s for s in servicos}
            item_selecionado = st.selectbox("Serviço Principal", list(servico_opcoes.keys()) if servico_opcoes else ["Nenhum serviço"], label_visibility="collapsed")
            
            valor_sugerido = 0.0
            if item_selecionado and item_selecionado != "Nenhum serviço":
                valor_sugerido = servico_opcoes[item_selecionado].preco_padrao
                
            valor_final = st.number_input("Valor Cobrado (R$)", value=valor_sugerido, min_value=0.0)
            
            mais_servico = st.checkbox("Adicionar múltiplos serviços?")
            servicos_extra = {}
            if mais_servico:
                selecionados_extra = st.multiselect("Serviços Adicionais", list(servico_opcoes.keys()))
                for sel in selecionados_extra:
                    v = st.number_input(f"Valor {sel} (R$)", value=servico_opcoes[sel].preco_padrao, min_value=0.0)
                    servicos_extra[servico_opcoes[sel].id] = v
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("Enviar para o Pátio", type="primary", use_container_width=True):
                if cliente_selecionado and not cliente_selecionado.startswith("--"):
                    cli_codigo = cliente_selecionado.split(" |")[0]
                    cliente_ref = db.query(Cliente).filter(Cliente.codigo == cli_codigo).first()
                    
                    codigo_seq = f"OS-{db.query(Atendimento).count()+1:04d}"
                    total_atendimento = valor_final + sum(servicos_extra.values())
                    
                    novo_at = Atendimento(
                        codigo=codigo_seq, cliente_id=cliente_ref.id, status="Em Andamento",
                        valor_total=total_atendimento, data_criacao=obter_hora_local().isoformat()
                    )
                    db.add(novo_at)
                    db.flush()
                    
                    if item_selecionado != "Nenhum serviço":
                        db.add(ItemAtendimento(atendimento_id=novo_at.id, tipo="Serviço", referencia_id=servico_opcoes[item_selecionado].id, valor_cobrado=valor_final))
                        
                    for s_id, v in servicos_extra.items():
                        db.add(ItemAtendimento(atendimento_id=novo_at.id, tipo="Serviço", referencia_id=s_id, valor_cobrado=v))
                        
                    db.commit()
                    st.session_state['success_msg'] = f"OS {codigo_seq} enviada ao Pátio!"
                    st.rerun()
                else:
                    st.error("Selecione um cliente.")

    # ==========================================
    # ABA 2: PÁTIO (EM ANDAMENTO)
    # ==========================================
    with aba_patio:
        st.markdown(f"<div style='margin-top:10px; margin-bottom:12px;'><span style='font-size:16px; font-weight:500;'>Em Andamento</span> <span class='red-badge'>{qtd_andamento}</span></div>", unsafe_allow_html=True)
        if em_andamento:
            now = datetime.now()
            for at in em_andamento:
                cli = db.query(Cliente).filter(Cliente.id == at.cliente_id).first()
                cli_nome = cli.nome if cli else "Desconhecido"
                carro = cli.modelo_veiculo if cli and cli.modelo_veiculo else "Sem Veículo"
                placa = cli.placa_veiculo if cli and cli.placa_veiculo else "Sem Placa"
                
                dt_criacao = datetime.fromisoformat(at.data_criacao) if at.data_criacao else now
                tempo_decorrido = formatar_tempo(now - dt_criacao)
                
                with st.container(border=True):
                    # Textos ultra compactos
                    st.markdown(f"<p style='margin:0; font-size:14px; font-weight:600;'>{cli_nome} <span style='font-size:10px; font-weight:normal; color:var(--text-sec);'>({at.codigo})</span></p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:0; font-size:12px; color:var(--text-sec);'>*{carro} | Placa: {placa}*</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:2px 0 6px 0; font-size:12px;'>{gold_icon('clock')} {dt_criacao.strftime('%H:%M')} (<b>{tempo_decorrido}</b>) &nbsp;|&nbsp; <b>R$ {at.valor_total:.2f}</b></p>", unsafe_allow_html=True)
                    
                    # Ações da OS usando a Lógica Exata do seu outro app (Pills)
                    action = st.pills("Ações", ["Concluir", "Editar", "Excluir"], label_visibility="collapsed", key=f"act_os_{at.id}")
                    if action == "Concluir":
                        dialog_checkout(at.id)
                    elif action == "Editar":
                        dialog_editar_os(at.id)
                    elif action == "Excluir":
                        dialog_excluir_os(at.id)
        else:
            st.info("Pátio vazio.")

    # ==========================================
    # ABA 3: HISTÓRICO CONCLUÍDOS
    # ==========================================
    with tab3:
        st.markdown(f"<div style='margin-top:10px; margin-bottom:12px;'><span style='font-size:16px; font-weight:500;'>Concluídos Hoje</span> <span class='red-badge'>{qtd_concluido}</span></div>", unsafe_allow_html=True)
        
        concluidos = db.query(Atendimento).filter(Atendimento.status == "Finalizado").order_by(Atendimento.id.desc()).limit(20).all()
        if concluidos:
            for at in concluidos:
                cli = db.query(Cliente).filter(Cliente.id == at.cliente_id).first()
                with st.container(border=True):
                    st.markdown(f"<p style='margin:0; font-size:14px; font-weight:600;'>{cli.nome if cli else 'Desconhecido'} <span style='font-size:10px; font-weight:normal; color:var(--text-sec);'>({at.codigo})</span></p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:2px 0; font-size:12px;'>{gold_icon('check')} Finalizado: {datetime.fromisoformat(at.data_conclusao).strftime('%H:%M') if at.data_conclusao else '-'}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:0; font-size:12px;'>{at.forma_pagamento} &nbsp;|&nbsp; <b>R$ {at.valor_total:.2f}</b></p>", unsafe_allow_html=True)
                    # Use margin top for the button visually by separating it.
                    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                    if st.button("Excluir", key=f"hist_del_{at.id}"):
                        dialog_excluir_os(at.id)
        else:
            st.info("Nenhum concluído hoje.")

    # ==========================================
    # ABA 4: RESUMO (GRÁFICOS E KPIs)
    # ==========================================
    with tab4:
        st.markdown(f"<div style='margin-top:10px; margin-bottom:12px;'><span style='font-size:16px; font-weight:500;'>{gold_icon('chart')} Relatório Executivo</span></div>", unsafe_allow_html=True)
        hoje_str = hoje.strftime("%Y-%m-%d")
        total_dia = db.query(Atendimento).filter(Atendimento.data_criacao >= hoje_str, Atendimento.status == "Finalizado").all()
        
        faturamento = sum(a.valor_total for a in total_dia)
        tkm = (faturamento / len(total_dia)) if total_dia else 0
        
        # Agrupar Pagamentos
        pgtos = {}
        for a in total_dia:
            fp = a.forma_pagamento or "Não Informado"
            pgtos[fp] = pgtos.get(fp, 0) + a.valor_total
            
        pgtos_sorted = sorted(pgtos.items(), key=lambda x: x[1], reverse=True)[:3]
        pgto_html = "".join([f"<div style='display:flex; justify-content:space-between; font-size:11px; margin-top:3px; color:var(--text-sec); border-bottom: 1px dashed rgba(0,0,0,0.05); padding-bottom: 2px;'><span>{k}</span> <b>R$ {v:,.2f}</b></div>" for k, v in pgtos_sorted])
        if not pgto_html: pgto_html = "<div style='font-size:11px; color:#999; text-align:center;'>Sem pagamentos hoje</div>"
        
        # Processar Tempos e Serviços
        total_servicos_entregues = 0
        tempos_servicos = {}
        servicos_count = {}
        horas_count = {}
        tempo_total_min = []
        
        for a in total_dia:
            if a.data_conclusao and a.data_criacao:
                try:
                    dt_cria = datetime.fromisoformat(a.data_criacao)
                    dt_fim = datetime.fromisoformat(a.data_conclusao)
                    h = dt_fim.hour
                    horas_count[f"{h}h"] = horas_count.get(f"{h}h", 0) + 1
                    
                    delta_min = (dt_fim - dt_cria).total_seconds() / 60.0
                    tempo_total_min.append(delta_min)
                    
                    # Incluir todos os itens que remetem a um serviço, ignorando restrição de texto
                    itens_at = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id == a.id).all()
                    for i in itens_at:
                        s_nome = "Serviço Avulso"
                        eh_servico = False
                        
                        if i.referencia_id:
                            s = db.query(Servico).filter(Servico.id == i.referencia_id).first()
                            if s:
                                s_nome = s.nome
                                eh_servico = True
                        
                        if eh_servico or (i.tipo and "Serv" in i.tipo):
                            total_servicos_entregues += 1
                            servicos_count[s_nome] = servicos_count.get(s_nome, 0) + 1
                            if s_nome not in tempos_servicos: tempos_servicos[s_nome] = []
                            tempos_servicos[s_nome].append(delta_min)
                except: pass

        tempo_medio_global = int(sum(tempo_total_min)/len(tempo_total_min)) if tempo_total_min else 0
        
        # Bloco 1: KPIs Básicos
        st.markdown(f"""
        <div style='display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-bottom:10px;'>
            <div class='premium-card' style='padding:12px!important; text-align:center;'>
                <div style='font-size:10px; font-weight:700; color:var(--text-sec); text-transform:uppercase;'>Serviços Entregues</div>
                <div style='font-size:22px; font-weight:800; color:var(--text-main); margin-top:2px;'>{total_servicos_entregues}</div>
            </div>
            <div class='premium-card' style='padding:12px!important; text-align:center;'>
                <div style='font-size:10px; font-weight:700; color:var(--text-sec); text-transform:uppercase;'>Tempo Médio Geral</div>
                <div style='font-size:22px; font-weight:800; color:var(--text-main); margin-top:2px;'>{tempo_medio_global} min</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Bloco 2: Faturamento e TKM
        st.markdown(f"""
        <div style='display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-bottom:15px;'>
            <div class='premium-card' style='padding:12px!important;'>
                <div style='font-size:10px; font-weight:700; color:var(--text-sec); text-transform:uppercase; text-align:center;'>Faturamento Total</div>
                <div style='font-size:18px; font-weight:800; color:var(--success); text-align:center; margin-bottom:8px;'>R$ {faturamento:,.2f}</div>
                <div style='border-top:1px solid #eee; padding-top:6px;'>
                    {pgto_html}
                </div>
            </div>
            <div class='premium-card' style='padding:12px!important; text-align:center; display:flex; flex-direction:column; justify-content:center;'>
                <div style='font-size:10px; font-weight:700; color:var(--text-sec); text-transform:uppercase;'>Ticket Médio (TKM)</div>
                <div style='font-size:20px; font-weight:800; color:var(--accent); margin-top:4px;'>R$ {tkm:,.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Bloco 3: Horas Quentes
        st.markdown(f"<div style='font-size:13px; font-weight:700; margin-bottom:5px; color:var(--text-main);'>{gold_icon('fire')} Horas Quentes</div>", unsafe_allow_html=True)
        if horas_count:
            df_h = pd.DataFrame(list(horas_count.items()), columns=["Hora", "OSs"]).set_index("Hora")
            st.bar_chart(df_h, height=130)
            pico = max(horas_count, key=horas_count.get)
            st.markdown(f"<div style='background:#fcfcfc; padding:8px 12px; border-left:3px solid var(--accent); font-size:11px; color:#555; margin-top:-15px; border-radius:4px;'><b>Insight:</b> Pico de fluxo às <b>{pico}</b> ({horas_count[pico]} entregas).</div>", unsafe_allow_html=True)
        else:
            st.info("Sem dados suficientes.")
            
        st.markdown("<br>", unsafe_allow_html=True)
            
        # Bloco 4: Serviços Executados
        st.markdown(f"<div style='font-size:13px; font-weight:700; margin-bottom:5px; color:var(--text-main);'>{gold_icon('wrench')} Execução por Serviço</div>", unsafe_allow_html=True)
        if servicos_count:
            df_s = pd.DataFrame(list(servicos_count.items()), columns=["Serviço", "Qtd"]).set_index("Serviço")
            st.bar_chart(df_s, color="#C5A059", height=130)
            top_s = max(servicos_count, key=servicos_count.get)
            st.markdown(f"<div style='background:#fcfcfc; padding:8px 12px; border-left:3px solid var(--accent); font-size:11px; color:#555; margin-top:-15px; border-radius:4px; margin-bottom:15px;'><b>Insight:</b> <b>{top_s}</b> foi o carro-chefe hoje.</div>", unsafe_allow_html=True)
            
            # Lista Detalhada
            html_lista = "<div style='background:white; border:1px solid #eee; border-radius:8px; padding:10px;'>"
            html_lista += f"<div style='font-size:11px; font-weight:700; color:var(--text-sec); margin-bottom:8px; border-bottom:1px solid #eee; padding-bottom:4px;'>Total: {total_servicos_entregues} un | Média Geral: {tempo_medio_global} min</div>"
            
            for s_nome, t_list in tempos_servicos.items():
                m_min = int(sum(t_list)/len(t_list))
                q_s = servicos_count[s_nome]
                html_lista += f"""
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;'>
                    <span style='font-size:12px; font-weight:600; color:#333;'>{s_nome}</span>
                    <div style='text-align:right;'>
                        <span style='font-size:10px; background:#f0f0f0; padding:2px 6px; border-radius:10px; margin-right:4px; color:#555;'>{q_s} un</span>
                        <span style='font-size:10px; color:white; background:var(--accent); padding:2px 6px; border-radius:10px; font-weight:600;'>{m_min} min/méd</span>
                    </div>
                </div>
                """
            html_lista += "</div>"
            st.markdown(html_lista, unsafe_allow_html=True)
        else:
            st.info("Nenhum serviço registrado.")
            
        st.markdown("<br>", unsafe_allow_html=True)
            
        # Bloco 5: Insight Geral
        if total_dia:
            percep = "Rotatividade altíssima" if len(total_dia) >= 8 else "Fluxo constante" if len(total_dia) >= 4 else "Movimento leve"
            percep += " focado em serviços premium." if tkm > 150 else " focado em volume e giro rápido."
            
            melhoria = "Manter o ritmo operacional."
            if tempo_medio_global > 90:
                melhoria = "Tempo médio elevado. Tente otimizar a triagem e transição de veículos para reduzir o gargalo de 90+ min."
            elif tkm < 50:
                melhoria = "Ticket médio baixo. Oportunidade para ofertar serviços adicionais (cross-sell) no balcão."
                
            html_insight = f"""
            <div style='background: linear-gradient(145deg, #001C25, #002B38); padding:15px; border-radius:12px; color:white; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>
                <div style='display:flex; align-items:center; gap:6px; margin-bottom:8px;'>
                    <span style='font-size:16px;'>🤖</span>
                    <span style='font-size:12px; color:#C5A059; font-weight:700; text-transform:uppercase;'>Insight Gerencial</span>
                </div>
                <p style='font-size:12px; line-height:1.5; color:rgba(255,255,255,0.9); margin:0;'>
                    <b style='color:#C5A059;'>Percepção:</b> <span style='color: white;'>{percep}</span><br><br>
                    <b style='color:#C5A059;'>Melhoria Sugerida:</b> <span style='color: white;'>{melhoria}</span>
                </p>
            </div>
            """
            st.markdown(html_insight, unsafe_allow_html=True)
        else:
            st.write("Sem dados.")
