import streamlit as st
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
        "edit": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:4px;"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>',
        "trash": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:4px;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>',
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


@dialog_decorator("Gerenciar OS")
def dialog_checkout(at_id):
    db = next(get_db())
    at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
    if not at: return
    
    st.write(f"Gerenciando OS: **{at.codigo}**")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button(f"{gold_icon('edit')} Editar Itens (Apenas Admin)", key=f"edit_os_{at.id}", use_container_width=True):
            st.warning("Função de edição avançada na aba Histórico.")
    with col_btn2:
        if st.button(f"{gold_icon('trash')} Excluir OS", key=f"del_os_{at.id}", use_container_width=True):
            db.delete(at)
            db.commit()
            st.session_state['success_msg'] = f"OS excluída."
            st.rerun()

    st.markdown("---")
    
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
    if 'success_msg' not in st.session_state:
        st.session_state['success_msg'] = None
        
    if st.session_state['success_msg']:
        st.success(st.session_state['success_msg'])
        if st.button("OK", use_container_width=True):
            st.session_state['success_msg'] = None
            st.rerun()

    db = next(get_db())
    
    # Contadores
    hoje = obter_hora_local().date()
    # Atendimentos de hoje
    atendimentos_hoje = db.query(Atendimento).filter(Atendimento.data_criacao >= hoje.strftime("%Y-%m-%d")).all()
    qtd_andamento = sum(1 for a in atendimentos_hoje if a.status == "Em andamento")
    qtd_concluido = sum(1 for a in atendimentos_hoje if a.status == "Finalizado")
    
    c1, c2, c3 = st.columns([2, 1, 1], vertical_alignment="center")
    with c1:
        st.markdown(f"<h2 style='margin:0; padding:0; font-size: 24px;'>{gold_icon('lightning')} PDV</h2>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='premium-card' style='padding:8px!important; text-align:center;'><span style='font-size:12px; color:var(--warning);'>Andamento</span><br><b>{qtd_andamento}</b></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='premium-card' style='padding:8px!important; text-align:center;'><span style='font-size:12px; color:var(--success);'>Concluído</span><br><b>{qtd_concluido}</b></div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    clientes = db.query(Cliente).all()
    servicos = db.query(Servico).all()
    
    tab1, tab2, tab3, tab4 = st.tabs(["Novo", "Pátio", "Histórico", "Resumo"])
    
    # ==========================================
    # ABA 1: NOVO ATENDIMENTO
    # ==========================================
    with tab1:
        with st.container(border=True):
            busca_cliente = st.text_input("🔍 Pesquisar Cliente", placeholder="Nome ou Placa...")
            if st.button("+ Novo Cliente", use_container_width=True): dialog_novo_cliente()
            
            termo = remover_acentos(busca_cliente.strip().lower())
            cliente_opcoes = ["-- Selecione o Cliente --"]
            for c in clientes:
                if c.codigo == "CLI-0000": continue
                nome = remover_acentos(c.nome or "").lower()
                placa = remover_acentos(c.placa_veiculo or "").lower()
                if termo and (termo not in nome and termo not in placa): continue
                cliente_opcoes.append(f"{c.codigo} | {c.nome} ({c.placa_veiculo or 'Sem Placa'})")
            
            index_sel = 1 if len(cliente_opcoes) == 2 else 0
            cliente_selecionado = st.selectbox("Cliente", cliente_opcoes, index=index_sel, label_visibility="collapsed")
            
            st.markdown("<hr style='margin:16px 0;'>", unsafe_allow_html=True)
            
            st.markdown(f"<label style='font-size:13px; font-weight:500;'>{gold_icon('service')} Serviço</label>", unsafe_allow_html=True)
            servico_opcoes = [s.nome for s in servicos]
            item_selecionado = st.selectbox("Serviço Principal", servico_opcoes if servico_opcoes else ["Nenhum serviço"], label_visibility="collapsed")
            
            valor_sugerido = 0.0
            if item_selecionado and item_selecionado != "Nenhum serviço":
                serv = next((s for s in servicos if s.nome == item_selecionado), None)
                valor_sugerido = serv.preco_padrao if serv else 0.0
                
            valor_final = st.number_input("Valor Cobrado (R$)", value=valor_sugerido, min_value=0.0)
            
            # Adicional checkbox
            mais_servico = st.checkbox("Adicionar mais um serviço?")
            item_selecionado_2 = None
            valor_final_2 = 0.0
            if mais_servico:
                item_selecionado_2 = st.selectbox("2º Serviço", servico_opcoes if servico_opcoes else ["Nenhum serviço"], key="serv2")
                if item_selecionado_2 and item_selecionado_2 != "Nenhum serviço":
                    serv2 = next((s for s in servicos if s.nome == item_selecionado_2), None)
                    valor_final_2 = st.number_input("Valor 2º Serviço (R$)", value=serv2.preco_padrao if serv2 else 0.0, min_value=0.0)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("Enviar para o Pátio", type="primary", use_container_width=True):
                if cliente_selecionado and not cliente_selecionado.startswith("--"):
                    cli_codigo = cliente_selecionado.split(" |")[0]
                    cliente_ref = db.query(Cliente).filter(Cliente.codigo == cli_codigo).first()
                    
                    codigo_seq = f"OS-{db.query(Atendimento).count()+1:04d}"
                    total_atendimento = valor_final + valor_final_2
                    
                    novo_at = Atendimento(
                        codigo=codigo_seq, cliente_id=cliente_ref.id, status="Em andamento",
                        valor_total=total_atendimento, data_criacao=obter_hora_local().isoformat()
                    )
                    db.add(novo_at)
                    db.flush()
                    
                    serv_ref = db.query(Servico).filter(Servico.nome == item_selecionado).first()
                    if serv_ref:
                        db.add(ItemAtendimento(atendimento_id=novo_at.id, tipo="Serviço", referencia_id=serv_ref.id, valor_cobrado=valor_final))
                        
                    if mais_servico and item_selecionado_2:
                        serv_ref_2 = db.query(Servico).filter(Servico.nome == item_selecionado_2).first()
                        if serv_ref_2:
                            db.add(ItemAtendimento(atendimento_id=novo_at.id, tipo="Serviço", referencia_id=serv_ref_2.id, valor_cobrado=valor_final_2))
                        
                    db.commit()
                    st.session_state['success_msg'] = f"Serviço enviado ao Pátio!"
                    st.rerun()
                else:
                    st.error("Selecione um cliente.")

    # ==========================================
    # ABA 2: PÁTIO (EM ANDAMENTO)
    # ==========================================
    with tab2:
        # Ordena do mais antigo para o mais novo
        andamento = db.query(Atendimento).filter(Atendimento.status == "Em andamento").order_by(Atendimento.id.asc()).all()
        if andamento:
            now = obter_hora_local()
            for at in andamento:
                cli = db.query(Cliente).filter(Cliente.id == at.cliente_id).first()
                cli_nome = cli.nome if cli else "Desconhecido"
                carro = cli.modelo_veiculo if cli and cli.modelo_veiculo else "Sem Carro"
                placa = cli.placa_veiculo if cli and cli.placa_veiculo else "Sem Placa"
                
                dt_criacao = datetime.fromisoformat(at.data_criacao)
                tempo_decorrido = formatar_tempo(now - dt_criacao)
                
                with st.container(border=True):
                    # Cliente em destaque, OS minúscula
                    st.markdown(f"<h4 style='margin:0;'>{cli_nome} <span style='font-size:10px; font-weight:normal; color:var(--text-sec);'>({at.codigo})</span></h4>", unsafe_allow_html=True)
                    st.markdown(f"*{carro} | Placa: {placa}*")
                    
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.markdown(f"{gold_icon('clock')} Início: {dt_criacao.strftime('%H:%M')} (⏳ **{tempo_decorrido}**)", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"**Total: R$ {at.valor_total:.2f}**")
                        
                    if st.button("Concluir Serviço", key=f"fin_{at.id}", type="primary", use_container_width=True):
                        dialog_checkout(at.id)
        else:
            st.info("Pátio vazio.")

    # ==========================================
    # ABA 3: HISTÓRICO CONCLUÍDOS
    # ==========================================
    with tab3:
        concluidos = db.query(Atendimento).filter(Atendimento.status == "Finalizado").order_by(Atendimento.id.desc()).limit(20).all()
        if concluidos:
            for at in concluidos:
                cli = db.query(Cliente).filter(Cliente.id == at.cliente_id).first()
                with st.container(border=True):
                    st.markdown(f"**{cli.nome if cli else 'Desconhecido'}** | {at.codigo}")
                    st.markdown(f"{gold_icon('check')} *Finalizado: {datetime.fromisoformat(at.data_conclusao).strftime('%d/%m %H:%M') if at.data_conclusao else '-'}*", unsafe_allow_html=True)
                    st.markdown(f"**Pagamento:** {at.forma_pagamento} - R$ {at.valor_total:.2f}")
                    if st.button("Excluir (Admin)", key=f"hist_del_{at.id}"):
                        db.delete(at)
                        db.commit()
                        st.rerun()
        else:
            st.info("Nenhum concluído hoje.")

    # ==========================================
    # ABA 4: RESUMO
    # ==========================================
    with tab4:
        st.markdown(f"### {gold_icon('chart')} Resumo Diário", unsafe_allow_html=True)
        hoje_str = hoje.strftime("%Y-%m-%d")
        total_dia = db.query(Atendimento).filter(Atendimento.data_criacao >= hoje_str, Atendimento.status == "Finalizado").all()
        
        valor_total = sum(a.valor_total for a in total_dia)
        ticket_medio = (valor_total / len(total_dia)) if total_dia else 0
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div class='premium-card' style='text-align:center;'><span style='font-size:14px;'>Faturamento Hoje</span><br><b style='font-size:22px; color:var(--success);'>R$ " + f"{valor_total:,.2f}" + "</b></div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div class='premium-card' style='text-align:center;'><span style='font-size:14px;'>Ticket Médio</span><br><b style='font-size:22px; color:var(--accent);'>R$ " + f"{ticket_medio:,.2f}" + "</b></div>", unsafe_allow_html=True)
            
        st.markdown("---")
        st.write(f"Total de Atendimentos Finalizados: **{len(total_dia)}**")
