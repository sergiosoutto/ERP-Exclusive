import streamlit as st
import pandas as pd
from db_config import get_db, Cliente, Servico, Produto, Atendimento, ItemAtendimento, FormaPagamento, ServicoInsumo, MetaApp, registrar_log
from datetime import datetime, timedelta, timezone, time
import unicodedata
from sqlalchemy import func

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


def formatar_moeda(valor):
    try:
        return f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return '0,00'

def formatar_tempo(delta):
    horas, resto = divmod(delta.seconds, 3600)
    minutos, _ = divmod(resto, 60)
    if delta.days > 0:
        return f"{delta.days}d {horas}h {minutos}m"
    if horas > 0:
        return f"{horas}h {minutos}m"
    return f"{minutos}m"

def calcular_dias_uteis(inicio_date, fim_date):
    if inicio_date > fim_date:
        return 0
    dias = 0
    current = inicio_date
    while current <= fim_date:
        if current.weekday() < 6: # 0=Seg a 5=Sab
            dias += 1
        current += timedelta(days=1)
    return dias

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
    last_cli = db.query(Cliente).order_by(Cliente.id.desc()).first()
    next_id = (last_cli.id + 1) if last_cli else 1
    codigo_seq = f"CLI-{next_id:04d}"
    
    st.info(f"Código: **{codigo_seq}**")
    novo_nome = st.text_input("Nome do Cliente")
    novo_tel_num = st.text_input("Telefone com DDD", placeholder="61999999999")
    nova_placa = st.text_input("Placa do Veículo")
    novo_modelo = st.text_input("Modelo do Veículo")
    

    if st.button("Salvar Cliente", type="primary", use_container_width=True):
        if novo_nome:
            tel_formatado = formatar_telefone(novo_tel_num)
            
            if nova_placa and tel_formatado:
                existe = db.query(Cliente).filter(Cliente.placa_veiculo == nova_placa, Cliente.telefone == tel_formatado).first()
                if existe:
                    st.toast("Erro: Cliente já existe com esta placa e telefone!", icon='🚫')
                    return
            
            novo_cliente = Cliente(
                codigo=codigo_seq, 
                nome=novo_nome, 
                telefone=tel_formatado, 
                placa_veiculo=nova_placa,
                modelo_veiculo=novo_modelo
            )
            db.add(novo_cliente)
            db.commit()
            registrar_log(f"Cadastrou o cliente: {novo_nome}")
            st.session_state["success_msg"] = "Cliente cadastrado com sucesso!"
            st.session_state["novo_cliente_codigo"] = codigo_seq
            st.rerun()

@dialog_decorator("Confirmar Exclusão")
def dialog_excluir_os(at_id):
    st.warning("Tem certeza que deseja excluir esta OS permanentemente?")
    db = next(get_db())
    if st.button("Excluir Permanentemente", type="primary", use_container_width=True):
        at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
        if at:
            db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id == at.id).delete()
            db.delete(at)
            db.commit()
            st.session_state['success_msg'] = f"OS excluída."
            st.rerun()

@dialog_decorator("Editar OS")

@dialog_decorator("Reagendar Serviço")
def dialog_reagendar(at_id):
    db = next(get_db())
    at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
    
    if not at: return
    
    dt_atual = None
    if at.data_agendamento:
        try:
            dt_atual = datetime.fromisoformat(at.data_agendamento).date()
        except: pass
        
    nova_data = st.date_input("Nova Data", value=dt_atual)
    nova_hora = st.time_input("Nova Hora", value=time(9, 0))
    
    if st.button("Confirmar Reagendamento", type="primary", use_container_width=True):
        at.data_agendamento = f"{nova_data.isoformat()} {nova_hora.strftime('%H:%M')}"
        registrar_log(f"Reagendou a OS: {at.codigo}")
        db.commit()
        st.session_state['success_msg'] = "OS reagendada com sucesso!"
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
    
    # Cálculo Juros (Suspenso - O juros será cobrado internamente e não repassado ao cliente)
    juros = 0.0
    # if forma_obj:
    #     if parcelas == 1:
    #         juros = valor_base * (forma_obj.taxa_juros_vista / 100)
    #     else:
    #         juros = valor_base * (forma_obj.taxa_juros_parcela / 100) * parcelas
            
    valor_final = valor_base # + juros (Repasse desativado a pedido do usuário)
    
    # if juros > 0:
    #     st.write(f"Juros Aplicados: R$ {juros:.2f}")
    st.markdown(f"### Total a Pagar: R$ {valor_final:.2f}")
    
    # Automate Observation based on discount/addition
    auto_obs = ""
    if valor_base < at.valor_total:
        auto_obs = f"[Desconto de R$ {at.valor_total - valor_base:.2f}] "
    elif valor_base > at.valor_total:
        auto_obs = f"[Acréscimo de R$ {valor_base - at.valor_total:.2f}] "
        
    obs = st.text_input("Observação", value=auto_obs, placeholder="Ex: Higienização impecável...")
    
    if st.button("Confirmar Pagamento e Baixar Estoque", type="primary", use_container_width=True):
        registrar_log(f"Finalizou a OS: {at.codigo}")
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


@dialog_decorator("Iniciar Serviço")
def dialog_iniciar_lavagem(at_id):
    db = next(get_db())
    at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
    if not at: return
    
    st.write(f"Iniciando: **{at.codigo}**")
    
    agora = obter_hora_local()
    dt_atual = st.date_input("Data de Início", value=agora.date())
    hr_atual = st.time_input("Hora de Início", value=agora.time())
    
    if st.button("Confirmar Início", type="primary", use_container_width=True):
        at.status = "Lavando"
        dt_final = datetime.combine(dt_atual, hr_atual).astimezone(timezone(timedelta(hours=-3))).isoformat()
        at.data_inicio = dt_final
        registrar_log(f"Iniciou a OS: {at.codigo}")
        db.commit()
        st.session_state['success_msg'] = f"OS {at.codigo} em execução!"
        st.rerun()

@dialog_decorator("Sinalizar Pronto")
def dialog_sinalizar_pronto(at_id):
    db = next(get_db())
    at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
    if not at: return
    
    st.write(f"Concluindo etapa: **{at.codigo}**")
    
    agora = obter_hora_local()
    dt_atual = st.date_input("Data de Conclusão", value=agora.date())
    hr_atual = st.time_input("Hora de Conclusão", value=agora.time())
    
    if st.button("Confirmar Conclusão", type="primary", use_container_width=True):
        at.status = "Pronto"
        dt_final = datetime.combine(dt_atual, hr_atual).astimezone(timezone(timedelta(hours=-3))).isoformat()
        at.data_pronto = dt_final
        registrar_log(f"Marcou OS como pronta: {at.codigo}")
        db.commit()
        st.session_state['success_msg'] = f"OS {at.codigo} concluída!"
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
        st.toast(st.session_state['success_msg'], icon='✅')
        st.session_state['success_msg'] = None

    db = next(get_db())
    hoje = datetime.now()
    hoje_inicio = hoje.replace(hour=0, minute=0, second=0, microsecond=0)
    
    st.markdown(f"### {gold_icon('rocket')} Lançamento Rápido de OS")
    
    # Reimplementando a obtenção das OS do patio e os contadores corretos
    hoje_str_patio = hoje.strftime("%Y-%m-%d")
    em_andamento = db.query(Atendimento).filter(Atendimento.status.in_(["Aguardando", "Em Andamento", "Lavando", "Pronto"])).order_by(Atendimento.id.asc()).all()
    qtd_andamento = len(em_andamento)
    valor_patio = sum(a.valor_total for a in em_andamento) if em_andamento else 0.0

    
    concluidos_hoje = db.query(Atendimento).filter(Atendimento.status == "Finalizado", Atendimento.data_criacao.like(f"{hoje_str_patio}%")).all()
    qtd_concluido = len(concluidos_hoje)
    
    lbl_patio = f"Pátio ({qtd_andamento})" if qtd_andamento > 0 else "Pátio"
    lbl_hist = f"Histórico ({qtd_concluido})" if qtd_concluido > 0 else "Histórico"
    
    # --- CÁLCULO GLOBAL DE METAS (Para uso em toda a tela) ---
    hoje_str = hoje.strftime("%Y-%m-%d")
    meta_atual = db.query(MetaApp).filter(MetaApp.data_inicial <= hoje_str, MetaApp.data_final >= hoje_str).order_by(MetaApp.id.desc()).first()
    if meta_atual:
        d1_meta = meta_atual.data_inicial
        d2_meta = meta_atual.data_final
        
        # Helper de pesos
        def get_peso(meta, date_obj):
            wd = date_obj.weekday()
            if wd == 0: return getattr(meta, "peso_seg", 16.66)
            if wd == 1: return getattr(meta, "peso_ter", 16.66)
            if wd == 2: return getattr(meta, "peso_qua", 16.66)
            if wd == 3: return getattr(meta, "peso_qui", 16.66)
            if wd == 4: return getattr(meta, "peso_sex", 16.66)
            if wd == 5: return getattr(meta, "peso_sab", 16.70)
            return 0
            
        peso_total_periodo = sum(get_peso(meta_atual, d1_meta + timedelta(days=i)) for i in range((d2_meta - d1_meta).days + 1))
        valor_por_peso = meta_atual.valor / peso_total_periodo if peso_total_periodo > 0 else 0
        
        segunda_atual = hoje.date() - timedelta(days=hoje.weekday())
        
        # Calcula meta apenas para os dias desta semana que estão dentro do período da meta
        meta_semanal = sum(get_peso(meta_atual, segunda_atual + timedelta(days=i)) * valor_por_peso for i in range(6) if d1_meta <= (segunda_atual + timedelta(days=i)) <= d2_meta)
        
        # Optimized Metas using func.sum
        fat_mes = db.query(func.sum(Atendimento.valor_total)).filter(Atendimento.data_criacao >= d1_meta.strftime("%Y-%m-%d"), Atendimento.data_criacao <= d2_meta.strftime("%Y-%m-%dT23:59:59"), Atendimento.status == "Finalizado").scalar() or 0.0
        
        seg_str = segunda_atual.strftime("%Y-%m-%d")
        fat_semana = db.query(func.sum(Atendimento.valor_total)).filter(Atendimento.data_criacao >= seg_str, Atendimento.data_criacao <= d2_meta.strftime("%Y-%m-%dT23:59:59"), Atendimento.status == "Finalizado").scalar() or 0.0
        fat_semana_ate_ontem = db.query(func.sum(Atendimento.valor_total)).filter(Atendimento.data_criacao >= seg_str, Atendimento.data_criacao < hoje_str, Atendimento.status == "Finalizado").scalar() or 0.0
        fat_hoje = db.query(func.sum(Atendimento.valor_total)).filter(Atendimento.data_criacao.like(f"{hoje_str}%"), Atendimento.status == "Finalizado").scalar() or 0.0
        
        # Pesos para cálculo diário
        peso_restante_semana = sum(get_peso(meta_atual, hoje.date() + timedelta(days=i)) for i in range(6 - hoje.weekday()) if d1_meta <= (hoje.date() + timedelta(days=i)) <= d2_meta)
        peso_hoje = get_peso(meta_atual, hoje.date()) if (d1_meta <= hoje.date() <= d2_meta) else 0
        
        if peso_restante_semana > 0:
            valor_restante_semana = meta_semanal - fat_semana_ate_ontem
            meta_diaria = max(0, valor_restante_semana * (peso_hoje / peso_restante_semana))
        else:
            meta_diaria = 0
            
        peso_trabalhado_semana = sum(get_peso(meta_atual, segunda_atual + timedelta(days=i)) for i in range(hoje.weekday() + 1) if d1_meta <= (segunda_atual + timedelta(days=i)) <= d2_meta)
        peso_total_semana = sum(get_peso(meta_atual, segunda_atual + timedelta(days=i)) for i in range(6) if d1_meta <= (segunda_atual + timedelta(days=i)) <= d2_meta)
        
        if peso_trabalhado_semana > 0:
            eficiencia = fat_semana / peso_trabalhado_semana
            run_rate = eficiencia * peso_total_semana
        else:
            run_rate = 0
            
        perc_total = (fat_mes / meta_atual.valor) * 100 if meta_atual.valor > 0 else 100
        perc_semana = (fat_semana / meta_semanal) * 100 if meta_semanal > 0 else 100
        
        diff = run_rate - meta_semanal
        
        diff_dia = fat_hoje - meta_diaria
        diff_semana = fat_semana - meta_semanal
        
        if diff_dia >= 0:
            txt_dia = f"Excedente: R$ {formatar_moeda(diff_dia)}"
            cor_dia = "#2ecc71"
        else:
            txt_dia = f"Falta: R$ {formatar_moeda(abs(diff_dia))}"
            if valor_patio > 0:
                txt_dia += f" <span style='font-size:10px; color:#555;'> (+ R$ {formatar_moeda(valor_patio)} no pátio)</span>"
            cor_dia = "#e74c3c"
            
        if diff_semana >= 0:
            txt_sem = f"Excedente: R$ {formatar_moeda(diff_semana)}"
            cor_sem = "#2ecc71"
        else:
            txt_sem = f"Falta: R$ {formatar_moeda(abs(diff_semana))}"
            if valor_patio > 0:
                txt_sem += f" <span style='font-size:10px; color:#555;'> (+ R$ {formatar_moeda(valor_patio)} no pátio)</span>"
            cor_sem = "#e74c3c"
        
        # MINI BOX FLUXO GERAL
        st.markdown(f"""
        <div style='background:#fcfcfc; border:1px solid #eee; border-radius:8px; padding:12px; margin-bottom:15px; display:flex; justify-content:space-around; align-items:center; box-shadow:0 2px 4px rgba(0,0,0,0.02);'>
            <div style='text-align:center;'>
                <div style='font-size:10px; font-weight:700; color:#888; text-transform:uppercase;'>Alvo do Dia</div>
                <div style='font-size:16px; font-weight:800; color:#333;'>R$ {formatar_moeda(meta_diaria)}</div>
                <div style='font-size:11px; font-weight:600; color:{cor_dia};'>{txt_dia}</div>
            </div>
            <div style='width:1px; height:40px; background:#e0e0e0;'></div>
            <div style='text-align:center;'>
                <div style='font-size:10px; font-weight:700; color:#888; text-transform:uppercase;'>Meta da Semana</div>
                <div style='font-size:16px; font-weight:800; color:#333;'>R$ {formatar_moeda(meta_semanal)}</div>
                <div style='font-size:11px; font-weight:600; color:{cor_sem};'>{txt_sem}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    

    # Contagem de Agendados para hoje
    agendados_hoje = db.query(Atendimento).filter(Atendimento.status == "Agendado").count()
    if agendados_hoje > 0:
        lbl_agenda = f"{gold_icon('bell-fill')} Agenda ({agendados_hoje})"
    else:
        lbl_agenda = f"{gold_icon('bell')} Agenda"
    abas_disponiveis = ["Novo", lbl_patio, lbl_hist, lbl_agenda, "Resumo"]


    aba_selecionada = st.pills("Submenu", abas_disponiveis, default="Novo", label_visibility="collapsed")
    
    # ==========================================
    # ABA 1: NOVO ATENDIMENTO
    # ==========================================
    # Pré-carregar dicionários globais
    todos_cli = db.query(Cliente).all()
    clientes_map = {c.id: c for c in todos_cli}
    
    todos_servs = db.query(Servico).all()
    servico_map = {s.id: s for s in todos_servs}
    
    if aba_selecionada == "Novo":
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
            if 'novo_cliente_codigo' in st.session_state:
                for idx, op in enumerate(cliente_opcoes):
                    if op.startswith(st.session_state['novo_cliente_codigo']):
                        index_sel = idx
                        break
                # Only use once
                del st.session_state['novo_cliente_codigo']
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
            hora_prevista = st.text_input("Previsão de Saída (Ex: Imediato, 17:30, Fim da Tarde)", value="Imediato")
            st.markdown("<br>", unsafe_allow_html=True)

            c_ag1, c_ag2, c_ag3 = st.columns([1, 1.5, 1.5])
            with c_ag1:
                is_agendamento = st.checkbox("Agendar OS?", value=False)
            
            data_agendamento = None
            hora_agendamento = None
            if is_agendamento:
                with c_ag2:
                    data_agendamento = st.date_input("Data do Serviço")
                with c_ag3:
                    hora_agendamento = st.time_input("Hora", value=time(9, 0))
                    
            btn_label = "Agendar Serviço" if is_agendamento else "Enviar para o Pátio"
            if st.button(btn_label, type="primary", use_container_width=True):

                if cliente_selecionado and not cliente_selecionado.startswith("--"):
                    cli_codigo = cliente_selecionado.split(" |")[0]
                    cliente_ref = db.query(Cliente).filter(Cliente.codigo == cli_codigo).first()
                    
                    last_at = db.query(Atendimento).order_by(Atendimento.id.desc()).first()
                    next_id = (last_at.id + 1) if last_at else 1
                    codigo_seq = f"OS-{next_id:04d}"
                    
                    total_atendimento = valor_final + sum(servicos_extra.values())
                    
                    stts = "Agendado" if is_agendamento else "Aguardando"
                    dt_agend = f"{data_agendamento.isoformat()} {hora_agendamento.strftime('%H:%M')}" if is_agendamento and data_agendamento and hora_agendamento else (data_agendamento.isoformat() if is_agendamento and data_agendamento else None)
                    novo_at = Atendimento(
                        codigo=codigo_seq, cliente_id=cliente_ref.id, status=stts,
                        valor_total=total_atendimento, data_criacao=obter_hora_local().isoformat(),
                        data_agendamento=dt_agend, hora_prevista_saida=hora_prevista
                    )
                    db.add(novo_at)
                    db.flush()
                    
                    if item_selecionado != "Nenhum serviço":
                        db.add(ItemAtendimento(atendimento_id=novo_at.id, tipo="Serviço", referencia_id=servico_opcoes[item_selecionado].id, valor_cobrado=valor_final))
                        
                    for s_id, v in servicos_extra.items():
                        db.add(ItemAtendimento(atendimento_id=novo_at.id, tipo="Serviço", referencia_id=s_id, valor_cobrado=v))
                        
                    db.commit()
                    registrar_log(f"Lançou a {codigo_seq} para {cliente_ref.nome}")
                    st.session_state['success_msg'] = f"OS {codigo_seq} enviada ao Pátio!"
                    st.rerun()
                else:
                    st.error("Selecione um cliente.")

    # ==========================================
    # ABA 2: PÁTIO (EM ANDAMENTO)
    # ==========================================
    elif aba_selecionada == lbl_patio:
        st.markdown(f"### {gold_icon('clock')} Veículos no Pátio", unsafe_allow_html=True)
        
        if em_andamento:
            fila = [a for a in em_andamento if a.status in ("Aguardando", "Em Andamento")]
            lavando = [a for a in em_andamento if a.status == "Lavando"]
            prontos = [a for a in em_andamento if a.status == "Pronto"]
            
            at_ids = [a.id for a in em_andamento]
            todos_itens = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id.in_(at_ids)).all() if at_ids else []
            itens_map = {}
            for item in todos_itens:
                itens_map.setdefault(item.atendimento_id, []).append(item)
            
            def render_os_card(at):
                cli = clientes_map.get(at.cliente_id)
                itens_at = itens_map.get(at.id, [])
                total_val = sum(i.valor_cobrado for i in itens_at)
                
                servs = []
                for i in itens_at:
                    s_nome = "Item"
                    if i.tipo == "Serviço" and i.referencia_id in servico_map:
                        s_nome = servico_map[i.referencia_id].nome
                    servs.append(s_nome)
                
                dt_str = "Agora"
                if at.data_criacao:
                    try:
                        dt = datetime.fromisoformat(at.data_criacao)
                        dt_str = dt.strftime('%H:%M')
                    except: pass
                
                carro_info = cli.modelo_veiculo if cli and cli.modelo_veiculo else "Sem Veículo"
                placa_info = cli.placa_veiculo if cli and cli.placa_veiculo else "Sem Placa"
                
                with st.container(border=True):
                    st.markdown(f"<p style='margin:0; font-size:14px; font-weight:600;'>{cli.nome if cli else 'Desconhecido'} <span style='font-size:10px; font-weight:normal; color:var(--text-sec);'>({at.codigo})</span></p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:0; font-size:12px; color:var(--text-sec);'>*{carro_info} | Placa: {placa_info}*</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:2px 0 6px 0; font-size:12px;'>{gold_icon('clock')} {dt_str} &nbsp;|&nbsp; <b>R$ {formatar_moeda(total_val)}</b></p>", unsafe_allow_html=True)
                    
                    # Ações Dinâmicas por Status
                    if at.status in ("Aguardando", "Em Andamento"):
                        if st.button(f"▶ Iniciar Lavagem", key=f"btn_ini_{at.id}", type="primary", use_container_width=True):
                            at.status = "Lavando"
                            at.data_inicio = obter_hora_local().isoformat()
                            db.commit()
                            st.toast(f"OS {at.codigo} em execução!")
                            st.rerun()
                    elif at.status == "Lavando":
                        if st.button(f"✔ Sinalizar Pronto", key=f"btn_pro_{at.id}", type="primary", use_container_width=True):
                            at.status = "Pronto"
                            at.data_pronto = obter_hora_local().isoformat()
                            db.commit()
                            st.toast(f"OS {at.codigo} concluída! Aguardando entrega.")
                            st.rerun()
                    elif at.status == "Pronto":
                        if st.button(f"💲 Entregar e Receber", key=f"btn_rec_{at.id}", type="primary", use_container_width=True):
                            dialog_checkout(at.id)
                    
                    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
                    
                    # Pulo Dinâmico / Ações Secundárias
                    options = ["Checkout Direto", "Editar", "Excluir"] if st.session_state.get("pode_excluir", False) else ["Checkout Direto", "Editar"]
                    if at.status == "Pronto": options.remove("Checkout Direto") # Já é a ação principal
                    
                    if options:
                        op_os = st.pills("Outras Ações", options=options, key=f"pill_sec_{at.id}", label_visibility="collapsed")
                        if op_os == "Checkout Direto":
                            dialog_checkout(at.id)
                        elif op_os == "Editar":
                            dialog_editar_os(at.id)
                        elif op_os == "Excluir":
                            dialog_excluir_os(at.id)
            
            # Layout em abas (Pills) para não amassar os cards
            lbl_f = f"🚗 Fila ({len(fila)})"
            lbl_l = f"💦 Lavando ({len(lavando)})"
            lbl_p = f"✨ Prontos ({len(prontos)})"
            
            aba_fase = st.pills("Fase do Pátio", [lbl_f, lbl_l, lbl_p], default=lbl_f, label_visibility="collapsed")
            
            if aba_fase == lbl_f:
                for a in fila: render_os_card(a)
                if not fila: st.info("Nenhum carro na fila.")
            elif aba_fase == lbl_l:
                for a in lavando: render_os_card(a)
                if not lavando: st.info("Nenhum carro sendo lavado.")
            elif aba_fase == lbl_p:
                for a in prontos: render_os_card(a)
                if not prontos: st.info("Nenhum carro pronto aguardando entrega.")
                
        else:
            st.info("Nenhuma OS no pátio.")

    # ==========================================
    # ABA 3: HISTÓRICO CONCLUÍDOS
    # ==========================================
    elif aba_selecionada == lbl_hist:
        st.markdown(f"<div style='margin-top:10px; margin-bottom:12px;'><span style='font-size:16px; font-weight:500;'>Finalizados</span> <span style='background:#f0f0f0; color:#333; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:600; margin-left:4px;'>{len(concluidos_hoje)}</span></div>", unsafe_allow_html=True)
        
        concluidos = db.query(Atendimento).filter(Atendimento.status == "Finalizado", Atendimento.data_criacao.like(f"{hoje_str_patio}%")).order_by(Atendimento.id.desc()).all()
        if concluidos:
            for at in concluidos:
                cli = clientes_map.get(at.cliente_id)
                dt_c = datetime.fromisoformat(at.data_conclusao) if at.data_conclusao else None
                dt_str = dt_c.strftime('%d/%m/%Y às %H:%M') if dt_c else '-'
                with st.container(border=True):
                    st.markdown(f"""
                    <div style='display: flex; justify-content: space-between; align-items: center; margin: -5px 0;'>
                        <div>
                            <span style='font-size:13px; font-weight:600;'>{cli.nome if cli else 'Desconhecido'}</span> 
                            <span style='font-size:11px; color:#888;'>({at.codigo})</span><br>
                            <span style='font-size:11px; color:#888;'>*{cli.modelo_veiculo if cli and cli.modelo_veiculo else "Sem Veículo"}*</span><br>
                            <span style='font-size:11px; color:#555;'>{gold_icon('check')} {dt_str} | {at.forma_pagamento}</span>
                        </div>
                        <div style='text-align: right;'>
                            <span style='font-size:13px; font-weight:700; color:var(--text-main);'>R$ {at.valor_total:.2f}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                    if st.session_state.get("pode_excluir", False) and st.button("Excluir", key=f"hist_del_{at.id}"):
                        dialog_excluir_os(at.id)
        else:
            st.info("Nenhum concluído hoje.")

    # ==========================================
    # ABA 4: RESUMO (GRÁFICOS E KPIs)
    # ==========================================

    # ==========================================
    # ABA: AGENDA (Agendados)
    # ==========================================
    elif aba_selecionada == lbl_agenda:
        st.markdown(f"### {gold_icon('calendar')} Serviços Agendados", unsafe_allow_html=True)
        agendados = agendados_raw # Já buscado no lazy load acima
        
        if not agendados:
            st.info("Nenhum serviço agendado.")
        else:
            total_agendado = sum(a.valor_total for a in agendados)
            st.markdown(f"<div style='background:#fcfcfc; border:1px solid #eee; border-radius:8px; padding:12px; margin-bottom:15px; display:flex; justify-content:space-between; align-items:center;'><div><span style='font-size:12px; font-weight:700; color:#888; text-transform:uppercase;'>Volume Futuro</span><br><span style='font-size:18px; font-weight:800; color:var(--accent);'>R$ {formatar_moeda(total_agendado)}</span></div><div style='text-align:right;'><span style='font-size:12px; color:#888;'>Total de Veículos</span><br><span style='font-size:18px; font-weight:800;'>{len(agendados)}</span></div></div>", unsafe_allow_html=True)
            
            for at in agendados:
                cli = clientes_map.get(at.cliente_id)
                cli_nome = cli.nome if cli else "Desconhecido"
                carro = cli.modelo_veiculo if cli and cli.modelo_veiculo else "Sem Veículo"
                placa = cli.placa_veiculo if cli and cli.placa_veiculo else "Sem Placa"
                dt_str = "Data não definida"
                if at.data_agendamento:
                    try:
                        # PODE ESTAR EM YYYY-MM-DD ou YYYY-MM-DD HH:MM
                        if " " in at.data_agendamento:
                            dt_str = datetime.strptime(at.data_agendamento, "%Y-%m-%d %H:%M").strftime('%d/%m/%Y às %H:%M')
                        else:
                            dt_obj = datetime.fromisoformat(at.data_agendamento)
                            dt_str = dt_obj.strftime('%d/%m/%Y')
                    except Exception as e:
                        dt_str = str(at.data_agendamento)
                        
                with st.container(border=True):
                    st.markdown(f"<p style='margin:0; font-size:14px; font-weight:600;'>{cli_nome} <span style='font-size:10px; font-weight:normal; color:var(--text-sec);'>({at.codigo})</span></p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:0; font-size:12px; color:var(--text-sec);'>*{carro} | Placa: {placa}*</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:2px 0 6px 0; font-size:12px;'>{gold_icon('calendar-check')} <b>{dt_str}</b> &nbsp;|&nbsp; <b>R$ {formatar_moeda(at.valor_total)}</b></p>", unsafe_allow_html=True)
                    
                    options = ["Iniciar OS", "Reagendar", "Excluir"] if st.session_state.get("pode_excluir", False) else ["Iniciar OS", "Reagendar"]
                    op_ag = st.pills("Ações Agenda", options=options, key=f"pill_ag_{at.id}", label_visibility="collapsed")
                    
                    if op_ag == "Iniciar OS":
                        at.status = "Aguardando"
                        at.data_agendamento = None
                        at.data_criacao = obter_hora_local().isoformat()
                        db.commit()
                        st.rerun()
                    elif op_ag == "Reagendar":
                        dialog_reagendar(at.id)
                    elif op_ag == "Excluir":
                        db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id == at.id).delete()
                        db.delete(at)
                        db.commit()
                        st.rerun()

    elif aba_selecionada == "Resumo":
        st.markdown(f"<div style='margin-top:10px; margin-bottom:12px;'><span style='font-size:16px; font-weight:500;'>{gold_icon('chart')} Relatório Executivo</span></div>", unsafe_allow_html=True)
        
        data_resumo = st.date_input("Filtrar por data", value=hoje.date())
        data_resumo_str = data_resumo.strftime("%Y-%m-%d")
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        
        # --- DASHBOARD DE METAS ---
        if meta_atual:
            cor_diff = "#2ecc71" if diff >= 0 else "#e74c3c"
            msg_diff = f"Parabéns! Projetando superar a meta semanal em R$ {formatar_moeda(diff)}" if diff >= 0 else f"Atenção! Projetando um déficit de R$ {formatar_moeda(abs(diff))} na meta semanal"
            dias_trabalhados_semana = hoje.weekday() + 1
            media_dia = fat_semana / dias_trabalhados_semana if dias_trabalhados_semana > 0 else 0
            
            st.markdown(f"""
            <div style='display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-bottom:10px;'>
                <div class='premium-card' style='padding:12px!important; text-align:center;'>
                    <div style='font-size:10px; font-weight:700; color:var(--text-sec); text-transform:uppercase;'>Meta Total ({meta_atual.descricao})</div>
                    <div style='font-size:16px; font-weight:800; color:var(--text-main); margin-top:2px;'>R$ {formatar_moeda(fat_mes)} / R$ {formatar_moeda(meta_atual.valor)}</div>
                    <div style='font-size:11px; font-weight:700; color:var(--accent); margin-top:2px;'>{perc_total:.1f}% Concluído</div>
                </div>
                <div class='premium-card' style='padding:12px!important; text-align:center;'>
                    <div style='font-size:10px; font-weight:700; color:var(--text-sec); text-transform:uppercase;'>Meta da Semana</div>
                    <div style='font-size:16px; font-weight:800; color:var(--text-main); margin-top:2px;'>R$ {formatar_moeda(fat_semana)} / R$ {formatar_moeda(meta_semanal)}</div>
                    <div style='font-size:11px; font-weight:700; color:var(--accent); margin-top:2px;'>{perc_semana:.1f}% Concluído</div>
                </div>
            </div>
            
            <div class='premium-card' style='padding:12px 16px!important; margin-bottom:15px;'>
                <div style='font-size:12px; font-weight:700; color:#555; margin-bottom:8px;'>{gold_icon('graph-up')} Projeção de Fechamento da Semana (Run Rate)</div>
                <div style='background:#f4f6f8; border-radius:6px; padding:10px; display:flex; justify-content:space-between; margin-bottom:10px;'>
                    <div style='text-align:left;'><div style='font-size:9px; font-weight:700; color:#888; text-transform:uppercase;'>Status Atual</div><div style='font-size:12px; font-weight:800; color:{cor_diff};'>{msg_diff}</div></div>
                    <div style='text-align:right;'><div style='font-size:9px; font-weight:700; color:#888; text-transform:uppercase;'>Média / Dia (Semana)</div><div style='font-size:14px; font-weight:800; color:#444;'>R$ {formatar_moeda(media_dia)}</div></div>
                </div>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div style='font-size:12px; color:#888;'>Faturamento projetado (Fim da Semana):</div>
                    <div style='font-size:16px; font-weight:800; color:{cor_diff};'>R$ {formatar_moeda(run_rate)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Nenhuma Meta ativa para hoje.")
            
        total_dia = db.query(Atendimento).filter(Atendimento.data_criacao.like(f"{data_resumo_str}%"), Atendimento.status == "Finalizado").all()
        
        faturamento = sum(a.valor_total for a in total_dia)
        tkm = (faturamento / len(total_dia)) if total_dia else 0
        
        # Agrupar Pagamentos
        pgtos = {}
        for a in total_dia:
            fp = a.forma_pagamento or "Não Informado"
            pgtos[fp] = pgtos.get(fp, 0) + a.valor_total
            
        pgtos_sorted = sorted(pgtos.items(), key=lambda x: x[1], reverse=True)[:3]
        pgto_html = "".join([f"<div style='display:flex; justify-content:space-between; font-size:11px; margin-top:3px; color:var(--text-sec); border-bottom: 1px dashed rgba(0,0,0,0.05); padding-bottom: 2px;'><span>{k}</span> <b>R$ {formatar_moeda(v)}</b></div>" for k, v in pgtos_sorted])
        if not pgto_html: pgto_html = "<div style='font-size:11px; color:#999; text-align:center;'>Sem pagamentos hoje</div>"
        
        # Processar Tempos e Serviços
        total_servicos_entregues = 0
        tempos_servicos = {}
        servicos_count = {}
        horas_count = {}
        tempo_total_min = []
        
        # OTIMIZAÇÃO: Buscar todos os itens e serviços de uma vez
        atendimentos_ids = [a.id for a in total_dia]
        todos_itens = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id.in_(atendimentos_ids)).all() if atendimentos_ids else []
        
        # Mapear itens por atendimento
        itens_por_atendimento = {}
        for item in todos_itens:
            itens_por_atendimento.setdefault(item.atendimento_id, []).append(item)
            
        # Mapear serviços globalmente
        todos_servicos = db.query(Servico).all()
        servico_map = {s.id: s for s in todos_servicos}

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
                    itens_at = itens_por_atendimento.get(a.id, [])
                    for i in itens_at:
                        s_nome = "Serviço Avulso"
                        eh_servico = False
                        
                        if i.referencia_id:
                            s = servico_map.get(i.referencia_id)
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
                <div style='font-size:18px; font-weight:800; color:var(--success); text-align:center; margin-bottom:8px;'>R$ {formatar_moeda(faturamento)}</div>
                <div style='border-top:1px solid #eee; padding-top:6px;'>
                    {pgto_html}
                </div>
            </div>
            <div class='premium-card' style='padding:12px!important; text-align:center; display:flex; flex-direction:column; justify-content:center;'>
                <div style='font-size:10px; font-weight:700; color:var(--text-sec); text-transform:uppercase;'>Ticket Médio (TKM)</div>
                <div style='font-size:20px; font-weight:800; color:var(--accent); margin-top:4px;'>R$ {formatar_moeda(tkm)}</div>
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
                html_lista += f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;'>"
                html_lista += f"<span style='font-size:12px; font-weight:600; color:#333;'>{s_nome}</span>"
                html_lista += f"<div style='text-align:right;'>"
                html_lista += f"<span style='font-size:10px; background:#f0f0f0; padding:2px 6px; border-radius:10px; margin-right:4px; color:#555;'>{q_s} un</span>"
                html_lista += f"<span style='font-size:10px; color:white; background:var(--accent); padding:2px 6px; border-radius:10px; font-weight:600;'>{m_min} min/méd</span>"
                html_lista += f"</div></div>"
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
            
            if meta_atual:
                if diff < 0:
                    percep += f" Atenção: O ritmo atual projeta fechar R$ {formatar_moeda(abs(diff))} abaixo da meta ({meta_atual.descricao})."
                    melhoria = "Focar em upsell para recuperar o déficit."
                else:
                    percep += f" Ótimo: O ritmo está superando a meta em R$ {formatar_moeda(diff)} projetados."
                    melhoria = "Manter a excelente constância."
            
            if tempo_medio_global > 90:
                melhoria = "Atenção ao tempo de box. A média passou de 1h30. Tente otimizar a triagem e transição de veículos para reduzir o gargalo de 90+ min."
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
