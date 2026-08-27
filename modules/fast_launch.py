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
        "chart": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
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
    
    # Mostrar Itens atuais
    itens = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id == at.id).all()
    if itens:
        st.markdown("#### Itens Lançados:")
        for i in itens:
            s = db.query(Servico).filter(Servico.id == i.referencia_id).first()
            n = s.nome if s else "Desconhecido"
            st.write(f"- {n} (R$ {i.valor_cobrado:.2f})")
    
    st.markdown("---")
    st.markdown("#### Adicionar Mais Serviços")
    servicos = db.query(Servico).all()
    servico_nomes = {s.nome: s for s in servicos}
    
    selecionados = st.multiselect("Selecione serviços adicionais", list(servico_nomes.keys()))
    
    novos_valores = {}
    total_adicional = 0.0
    for sel in selecionados:
        s_obj = servico_nomes[sel]
        val = st.number_input(f"Valor para {sel} (R$)", value=s_obj.preco_padrao, min_value=0.0, key=f"add_{sel}")
        novos_valores[s_obj.id] = val
        total_adicional += val
        
    st.write(f"Total Adicional: **R$ {total_adicional:.2f}**")
    
    if st.button("Confirmar Edição", type="primary", use_container_width=True):
        for s_id, v in novos_valores.items():
            novo_item = ItemAtendimento(atendimento_id=at.id, tipo="Serviço", referencia_id=s_id, valor_cobrado=v)
            db.add(novo_item)
            
        at.valor_total += total_adicional
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
    # CSS Customizado para compactar cards e abas no fluxo do dia
    st.markdown("""
        <style>
            /* Diminuir padding dos containers com borda na tela do PDV */
            div[data-testid="stVerticalBlockBorderWrapper"] > div {
                padding: 10px !important;
            }
            div[data-testid="stVerticalBlockBorderWrapper"] {
                margin-bottom: -5px !important;
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
    
    # Contadores
    hoje = obter_hora_local().date()
    # Atendimentos de hoje
    atendimentos_hoje = db.query(Atendimento).filter(Atendimento.data_criacao >= hoje.strftime("%Y-%m-%d")).all()
    qtd_andamento = sum(1 for a in atendimentos_hoje if a.status == "Em andamento")
    qtd_concluido = sum(1 for a in atendimentos_hoje if a.status == "Finalizado")
    
    clientes = db.query(Cliente).all()
    servicos = db.query(Servico).all()
    
    # As tabs agora contém a flag
    tab1, tab2, tab3, tab4 = st.tabs(["Novo", f"Pátio ({qtd_andamento})", f"Histórico ({qtd_concluido})", "Resumo"])
    
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
            
            st.markdown(f"<label style='font-size:13px; font-weight:500;'>{gold_icon('service')} Serviço Principal</label>", unsafe_allow_html=True)
            servico_opcoes = {s.nome: s for s in servicos}
            item_selecionado = st.selectbox("Serviço Principal", list(servico_opcoes.keys()) if servico_opcoes else ["Nenhum serviço"], label_visibility="collapsed")
            
            valor_sugerido = 0.0
            if item_selecionado and item_selecionado != "Nenhum serviço":
                valor_sugerido = servico_opcoes[item_selecionado].preco_padrao
                
            valor_final = st.number_input("Valor Cobrado (R$)", value=valor_sugerido, min_value=0.0)
            
            # Adicional multiselect
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
                        codigo=codigo_seq, cliente_id=cliente_ref.id, status="Em andamento",
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
                    st.markdown(f"<h4 style='margin:0;'>{cli_nome} <span style='font-size:11px; font-weight:normal; color:var(--text-sec);'>({at.codigo})</span></h4>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:0; font-size:14px;'>*{carro} | Placa: {placa}*</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:4px 0 10px 0; font-size:13px;'>{gold_icon('clock')} Início: {dt_criacao.strftime('%H:%M')} (⏳ **{tempo_decorrido}**) &nbsp;|&nbsp; <b>Total: R$ {at.valor_total:.2f}</b></p>", unsafe_allow_html=True)
                    
                    # 3 Botões Inline: Editar, Excluir, Concluir
                    c_edit, c_del, c_fin = st.columns([1, 1, 1.5])
                    with c_edit:
                        if st.button("Editar", key=f"btn_ed_{at.id}", use_container_width=True): dialog_editar_os(at.id)
                    with c_del:
                        if st.button("Excluir", key=f"btn_dl_{at.id}", use_container_width=True): dialog_excluir_os(at.id)
                    with c_fin:
                        if st.button("Concluir", key=f"btn_fn_{at.id}", type="primary", use_container_width=True): dialog_checkout(at.id)
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
                    st.markdown(f"<h4 style='margin:0;'>{cli.nome if cli else 'Desconhecido'} <span style='font-size:11px; font-weight:normal; color:var(--text-sec);'>({at.codigo})</span></h4>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:4px 0; font-size:13px;'>{gold_icon('check')} <i>Finalizado: {datetime.fromisoformat(at.data_conclusao).strftime('%d/%m %H:%M') if at.data_conclusao else '-'}</i></p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:0; font-size:14px;'><b>Pagamento:</b> {at.forma_pagamento} - <b>R$ {at.valor_total:.2f}</b></p>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Excluir", key=f"hist_del_{at.id}"):
                        dialog_excluir_os(at.id)
        else:
            st.info("Nenhum concluído hoje.")

    # ==========================================
    # ABA 4: RESUMO (GRÁFICOS)
    # ==========================================
    with tab4:
        st.markdown(f"### {gold_icon('chart')} Resumo de Hoje", unsafe_allow_html=True)
        hoje_str = hoje.strftime("%Y-%m-%d")
        total_dia = db.query(Atendimento).filter(Atendimento.data_criacao >= hoje_str, Atendimento.status == "Finalizado").all()
        
        valor_total = sum(a.valor_total for a in total_dia)
        ticket_medio = (valor_total / len(total_dia)) if total_dia else 0
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div class='premium-card' style='text-align:center;'><span style='font-size:14px;'>Faturamento</span><br><b style='font-size:20px; color:var(--success);'>R$ " + f"{valor_total:,.2f}" + "</b></div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div class='premium-card' style='text-align:center;'><span style='font-size:14px;'>Ticket Médio</span><br><b style='font-size:20px; color:var(--accent);'>R$ " + f"{ticket_medio:,.2f}" + "</b></div>", unsafe_allow_html=True)
            
        st.markdown("---")
        
        # Preparar dados para Gráfico de Horas Quentes
        st.markdown("#### 🔥 Horas Quentes")
        horas_count = {}
        for a in total_dia:
            if a.data_conclusao:
                h = datetime.fromisoformat(a.data_conclusao).hour
                horas_count[f"{h}h"] = horas_count.get(f"{h}h", 0) + 1
                
        if horas_count:
            df_horas = pd.DataFrame(list(horas_count.items()), columns=["Hora", "Concluídos"]).set_index("Hora")
            st.bar_chart(df_horas)
        else:
            st.write("Sem dados de horas.")
            
        # Preparar dados para Gráfico de Serviços Executados
        st.markdown("#### 🛠️ Serviços Executados")
        servicos_count = {}
        if total_dia:
            # Pega IDs de todos atendimentos de hoje
            ids_hoje = [a.id for a in total_dia]
            # Busca itens de serviço desses atendimentos
            itens_hoje = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id.in_(ids_hoje), ItemAtendimento.tipo == "Serviço").all()
            for i in itens_hoje:
                s = db.query(Servico).filter(Servico.id == i.referencia_id).first()
                if s:
                    servicos_count[s.nome] = servicos_count.get(s.nome, 0) + 1
                    
        if servicos_count:
            df_serv = pd.DataFrame(list(servicos_count.items()), columns=["Serviço", "Qtd"]).set_index("Serviço")
            st.bar_chart(df_serv, color="#C5A059")
        else:
            st.write("Sem dados de serviços.")
