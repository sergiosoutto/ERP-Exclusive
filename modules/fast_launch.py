import streamlit as st
from db_config import get_db, Cliente, Servico, Produto, Atendimento, ItemAtendimento
from datetime import datetime

# Tratamento para st.dialog independente da versão exata 1.34/1.35+
dialog_decorator = st.dialog if hasattr(st, "dialog") else st.experimental_dialog

@dialog_decorator("👤 Cadastrar Novo Cliente")
def dialog_novo_cliente():
    db = next(get_db())
    # Gerar código automático e sequencial
    qtd = db.query(Cliente).count()
    codigo_seq = f"CLI-{qtd+1:04d}"
    
    st.info(f"Código do Cliente: **{codigo_seq}**")
    novo_nome = st.text_input("Nome do Cliente")
    novo_tel = st.text_input("Telefone")
    nova_placa = st.text_input("Placa do Veículo")
    novo_modelo = st.text_input("Modelo do Veículo") # Novo campo solicitado!
    if st.button("Salvar Cliente", type="primary", use_container_width=True):
        if novo_nome:
            novo_cliente = Cliente(
                codigo=codigo_seq, 
                nome=novo_nome, 
                telefone=novo_tel, 
                placa_veiculo=nova_placa,
                modelo_veiculo=novo_modelo
            )
            db.add(novo_cliente)
            db.commit()
            st.success(f"Cliente {codigo_seq} cadastrado com sucesso!")
            st.rerun()

@dialog_decorator("⚠️ Cancelar Atendimento")
def dialog_cancelar_atendimento(at_id):
    st.warning("Para cancelar este serviço, é necessária a senha do gerente.")
    senha = st.text_input("Senha do Gerente", type="password", key=f"senha_canc_{at_id}")
    if st.button("Confirmar Cancelamento", type="primary", use_container_width=True):
        if senha == "admin123":
            db = next(get_db())
            at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
            if at:
                at.status = "Cancelado"
                db.commit()
                st.success("Atendimento cancelado com sucesso!")
                st.rerun()
        else:
            st.error("Senha incorreta!")

@dialog_decorator("✏️ Editar Atendimento")
def dialog_editar_atendimento(at_id):
    db = next(get_db())
    at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
    if not at:
        return
        
    st.write(f"Editando OS: **{at.codigo}**")
    
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
        if col2.button("Remover", key=f"rem_{i.id}", use_container_width=True):
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
    
    if st.button("Adicionar Item ao Atendimento Existente", use_container_width=True):
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

def render_fast_launch():
    col_t, col_s = st.columns([2, 1], vertical_alignment="center")
    with col_t:
        st.markdown("<h2 style='margin:0; padding:0; font-size: 24px;'>⚡ Fluxo do dia</h2>", unsafe_allow_html=True)
    with col_s:
        st.markdown("<div style='background-color: var(--success); color: white; padding: 6px 10px; border-radius: 20px; text-align: center; font-weight: bold; font-size: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>🟢 CAIXA ABERTO</div>", unsafe_allow_html=True)
    
    # Inicializando estados
    if 'pdv_cart' not in st.session_state:
        st.session_state['pdv_cart'] = []
    
    # Obter sessão do DB
    db = next(get_db())

    # Carregar dados
    clientes = db.query(Cliente).all()
    servicos = db.query(Servico).all()
    produtos = db.query(Produto).all()
    
    # Estrutura de Abas
    tab1, tab2, tab3 = st.tabs(["Lançamento", "Em andamento", "Finalizado"])
    
    # ==========================================
    # ABA 1: Lançamento
    # ==========================================
    with tab1:
        with st.container(border=True):
            st.markdown("### 🚀 Lançamento Rápido")
            
            # Passo 1: Selecionar Cliente (sem permitir avulso/CLI-0000 se houver, filtramos CLI-0000 da lista)
            # Contar atendimentos finalizados para cada cliente (programa de fidelidade Diamante > 10 serviços)
            cliente_atendimentos = {}
            for c in clientes:
                count = db.query(Atendimento).filter(
                    Atendimento.cliente_id == c.id, 
                    Atendimento.status == "Finalizado"
                ).count()
                cliente_atendimentos[c.id] = count
                
            cliente_opcoes = ["-- Selecione o Cliente (Digite nome, placa ou modelo) --"]
            for c in clientes:
                if c.codigo == "CLI-0000":
                    continue # Não permite cliente avulso
                    
                tag_fidelidade = ""
                if cliente_atendimentos.get(c.id, 0) > 10:
                    tag_fidelidade = " 💎 [Diamante]"
                    
                cliente_opcoes.append(
                    f"{c.codigo} | {c.nome}{tag_fidelidade} - {c.modelo_veiculo or 'Sem Modelo'} ({c.placa_veiculo or 'Sem Placa'})"
                )
            
            col_c1, col_c2 = st.columns([2.5, 1], vertical_alignment="bottom")
            cliente_selecionado = col_c1.selectbox("👤 Selecionar Cliente", cliente_opcoes, index=0)
            
            # Botão para abrir o popup de novo cliente
            if col_c2.button("➕ Novo Cliente", use_container_width=True):
                dialog_novo_cliente()
                
            # Passo 2: Selecionar Serviço e Preço
            st.markdown("---")
            col_serv, col_preco = st.columns([2.5, 1], vertical_alignment="bottom")
            
            servico_opcoes = [s.nome for s in servicos]
            servico_selecionado = col_serv.selectbox("🛠️ Selecionar Serviço Principal", servico_opcoes if servico_opcoes else ["Nenhum serviço cadastrado"])
            
            valor_sugerido = 0.0
            if servico_selecionado and servico_selecionado != "Nenhum serviço cadastrado":
                serv = next((s for s in servicos if s.nome == servico_selecionado), None)
                valor_sugerido = serv.preco_padrao if serv else 0.0
                
            valor_final = col_preco.number_input("Valor (R$)", value=valor_sugerido, min_value=0.0)
            
            # Passo 3: Pagamento
            forma_pagamento = st.selectbox("💳 Forma de Pagamento", ["Dinheiro", "Pix", "Débito", "Crédito"])
            
            st.markdown("---")
            
            # Botão de Lançamento Direto (Um clique!)
            if st.button("🚀 INICIAR LAVAGEM (Enviar ao Pátio)", type="primary", use_container_width=True):
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
                        desconto_total=0.0,
                        valor_total=valor_final,
                        forma_pagamento=forma_pagamento,
                        data_criacao=datetime.now().isoformat()
                    )
                    db.add(novo_atendimento)
                    db.flush()
                    
                    # Adicionar o item do serviço
                    serv_ref = db.query(Servico).filter(Servico.nome == servico_selecionado).first()
                    if serv_ref:
                        novo_item = ItemAtendimento(
                            atendimento_id=novo_atendimento.id,
                            tipo="Serviço",
                            referencia_id=serv_ref.id,
                            valor_cobrado=valor_final
                        )
                        db.add(novo_item)
                    
                    db.commit()
                    st.success(f"Lavagem {codigo_seq} iniciada com sucesso! Movida para o Pátio.")
                    st.rerun()
                else:
                    st.error("Por favor, selecione um cliente cadastrado ou clique em ➕ Novo Cliente para cadastrar um novo.")
                    
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
                    
                    # Senha do Gerente se desconto > 5%
                    gerente_aprovado = True
                    if desconto > 5.0:
                        st.warning("⚠️ Desconto maior que 5% exige autorização do gerente.")
                        senha = st.text_input("Senha do Gerente", type="password", key="cart_senha_gerente")
                        if senha != "admin123":
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
                                data_criacao=datetime.now().isoformat()
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
                            st.success(f"Atendimento {codigo_seq} lançado com sucesso! Movido para a aba 'Em andamento'.")
                            st.rerun()
                    
                    if st.button("Limpar Carrinho", key="cart_clear_btn"):
                        st.session_state['pdv_cart'] = []
                        st.rerun()

    # ==========================================
    # ABA 2: Em Andamento
    # ==========================================
    with tab2:
        st.markdown("### Pátio (Em Andamento)")
        atendimentos_abertos = db.query(Atendimento).filter(Atendimento.status == "Em andamento").all()
        
        if not atendimentos_abertos:
            st.info("Nenhum veículo em andamento no momento.")
            
        for at in atendimentos_abertos:
            cliente_at = db.query(Cliente).filter(Cliente.id == at.cliente_id).first()
            itens_at = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id == at.id).all()
            
            # Calcular horário de entrada e tempo decorrido
            try:
                entrada_dt = datetime.fromisoformat(at.data_criacao)
                decorrido = datetime.now() - entrada_dt
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
                # Proporções otimizadas para tablet: col1 (informações) e col2 (botões sem quebra de linha)
                col1, col2 = st.columns([1.1, 1.4], vertical_alignment="center")
                with col1:
                    # Menor altura das linhas usando margens compactas e texto otimizado
                    cliente_nome = cliente_at.nome if cliente_at else 'Desconhecido'
                    cliente_veiculo = f"{cliente_at.modelo_veiculo} - {cliente_at.placa_veiculo}" if (cliente_at and cliente_at.modelo_veiculo) else (cliente_at.placa_veiculo if cliente_at else '')
                    
                    st.markdown(f"<div style='margin-bottom: 2px; font-size: 15px; font-weight: bold; color: var(--text-main);'>🚘 [{at.codigo}] {cliente_nome}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='margin-bottom: 2px; font-size: 12px; color: var(--text-sec);'><b>Veículo:</b> {cliente_veiculo}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='margin-bottom: 2px; font-size: 12px; color: var(--text-sec);'><b>Entrada:</b> {hora_entrada} <span style='color: var(--warning); font-weight: bold;'>({tempo_decorrido})</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='margin-bottom: 2px; font-size: 12px; color: var(--text-sec);'><b>Total:</b> R$ {at.valor_total:.2f} | <b>Pgto:</b> {at.forma_pagamento}</div>", unsafe_allow_html=True)
                    
                    detalhes = []
                    for i in itens_at:
                        if i.tipo == "Serviço":
                            s = db.query(Servico).filter(Servico.id == i.referencia_id).first()
                            detalhes.append(f"🛠️ {s.nome if s else 'Serviço'}")
                        else:
                            p = db.query(Produto).filter(Produto.id == i.referencia_id).first()
                            detalhes.append(f"📦 {p.nome if p else 'Produto'}")
                    st.markdown(f"<div style='font-size: 12px; color: var(--text-sec);'>{' | '.join(detalhes)}</div>", unsafe_allow_html=True)
                    
                with col2:
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    # Botões sem emojis e em formato compacto para alinhar e nunca quebrar linha no tablet
                    if col_btn1.button("Concluir", key=f"concluir_{at.id}", use_container_width=True):
                        at.status = "Finalizado"
                        at.data_conclusao = datetime.now().isoformat()
                        db.commit()
                        st.success("Atendimento finalizado!")
                        st.rerun()
                        
                    if col_btn2.button("Editar", key=f"editar_{at.id}", use_container_width=True):
                        dialog_editar_atendimento(at.id)
                        
                    if col_btn3.button("Excluir", key=f"excluir_{at.id}", use_container_width=True):
                        dialog_cancelar_atendimento(at.id)

    # ==========================================
    # ABA 3: Finalizado
    # ==========================================
    with tab3:
        st.markdown("### Histórico de Atendimentos")
        
        # Filtros
        with st.container(border=True):
            col_f1, col_f2 = st.columns(2)
            filtro_cliente = col_f1.selectbox("Filtrar por Cliente", ["Todos"] + [c.nome for c in clientes if c.codigo != "CLI-0000"])
            filtro_status = col_f2.selectbox("Status", ["Finalizado", "Cancelado"])
        
        query_finalizados = db.query(Atendimento).filter(Atendimento.status == filtro_status)
        if filtro_cliente != "Todos":
            c_ref = db.query(Cliente).filter(Cliente.nome == filtro_cliente).first()
            if c_ref:
                query_finalizados = query_finalizados.filter(Atendimento.cliente_id == c_ref.id)
            
        atendimentos_finalizados = query_finalizados.all()
        
        if not atendimentos_finalizados:
            st.info(f"Nenhum atendimento {filtro_status.lower()} encontrado.")
            
        for at in atendimentos_finalizados:
            cliente_at = db.query(Cliente).filter(Cliente.id == at.cliente_id).first()
            
            # Calcular entrada, saída e duração para os concluídos
            try:
                entrada_dt = datetime.fromisoformat(at.data_criacao)
                hora_entrada = entrada_dt.strftime("%d/%m %H:%M")
                if at.data_conclusao:
                    conclusao_dt = datetime.fromisoformat(at.data_conclusao)
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
            
            with st.container(border=True):
                status_text = "🟢 Finalizado" if at.status == "Finalizado" else "🔴 Cancelado"
                st.markdown(f"**{status_text}**")
                st.markdown(f"#### {at.codigo} | {cliente_at.nome if cliente_at else 'Desconhecido'} - R$ {at.valor_total:.2f}")
                if at.status == "Finalizado":
                    st.markdown(f"**Entrada:** {hora_entrada} | **Saída:** {hora_saida} *(Duração: {duracao_str})*")
                else:
                    st.markdown(f"**Data:** {hora_entrada} | **Pagamento:** {at.forma_pagamento}")
