import streamlit as st
from db_config import get_db, Cliente, Servico, Produto, Atendimento, ItemAtendimento
from datetime import datetime, timedelta, timezone

# Tratamento para st.dialog independente da versão exata 1.34/1.35+
dialog_decorator = st.dialog if hasattr(st, "dialog") else st.experimental_dialog

# Helper para retornar hora no fuso horário do usuário (UTC-3 - Brasília)
def obter_hora_local():
    fuso_brasil = timezone(timedelta(hours=-3))
    return datetime.now(fuso_brasil)

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
        return f"(61) 9{digitos[:4]}-{digitos[4:]}"
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
        "clock": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:4px;"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>'
    }
    return icons.get(icon_name, "")

@dialog_decorator("👤 Cadastrar Novo Cliente")
def dialog_novo_cliente():
    db = next(get_db())
    # Gerar código automático e sequencial
    qtd = db.query(Cliente).count()
    codigo_seq = f"CLI-{qtd+1:04d}"
    
    st.info(f"Código do Cliente: **{codigo_seq}**")
    novo_nome = st.text_input("Nome do Cliente")
    
    # Campo de telefone dividido para travar o DDD 61 e permitir tabulação direta
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

@dialog_decorator("⚠️ Cancelar Atendimento")
def dialog_cancelar_atendimento(at_id):
    st.warning("Para cancelar este serviço, é necessária a senha do gerente.")
    senha = st.text_input("Senha do Gerente", type="password", key=f"senha_canc_{at_id}")
    if st.button("Confirmar Cancelamento", type="primary", use_container_width=True):
        if senha == "admin": # Alterado para "admin"
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
    
    # Exige senha do gerente para QUALQUER alteração/remoção
    senha_gerente = st.text_input("Senha do Gerente para Alterações", type="password", key=f"edit_senha_{at_id}")
    gerente_autorizado = (senha_gerente == "admin") # Alterado para "admin"
    
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

@dialog_decorator("✅ Concluir Atendimento")
def dialog_concluir_atendimento(at_id):
    db = next(get_db())
    at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
    if not at:
        return
        
    st.write(f"Deseja realmente concluir a **{at.codigo}**?")
    obs = st.text_area("Observações (Opcional)", placeholder="Digite alguma observação sobre a entrega...")
    
    if st.button("Confirmar Conclusão", type="primary", use_container_width=True):
        at.status = "Finalizado"
        at.data_conclusao = obter_hora_local().isoformat()
        at.observacoes = obs
        db.commit()
        
        # Salva a mensagem no estado da sessão para persistir e não sumir rápido
        st.session_state['success_msg'] = f"Atendimento {at.codigo} concluído com sucesso!"
        st.rerun()

def render_fast_launch():
    # Mensagem de confirmação persistente
    if 'success_msg' not in st.session_state:
        st.session_state['success_msg'] = None
        
    if st.session_state['success_msg']:
        st.success(st.session_state['success_msg'])
        # Deixa o botão de fechar para o usuário decidir quando limpar, ou limpa no próximo clique
        if st.button("Limpar aviso"):
            st.session_state['success_msg'] = None
            st.rerun()

    col_t, col_s = st.columns([2, 1], vertical_alignment="center")
    with col_t:
        st.markdown("<h2 style='margin:0; padding:0; font-size: 24px;'>⚡ Fluxo do dia</h2>", unsafe_allow_html=True)
    with col_s:
        st.markdown("<div style='background-color: var(--success); color: white; padding: 6px 10px; border-radius: 20px; text-align: center; font-weight: bold; font-size: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>🟢 CAIXA ABERTO</div>", unsafe_allow_html=True)
    
    # Inicializando estados
    if 'pdv_cart' not in st.session_state:
        st.session_state['pdv_cart'] = []
    if 'selected_payment' not in st.session_state:
        st.session_state['selected_payment'] = 'Pix'
    
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
            st.markdown(f"### {gold_icon('user')} Novo Atendimento") # Título renomeado e com ícone elegante
            
            # Passo 1: Selecionar Cliente
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
            
            st.markdown(f"<label style='font-size:14px; font-weight:500; color:var(--text-main);'>{gold_icon('user')} Selecionar Cliente</label>", unsafe_allow_html=True)
            col_c1, col_c2 = st.columns([2.5, 1], vertical_alignment="bottom")
            cliente_selecionado = col_c1.selectbox("Selecione o Cliente", cliente_opcoes, index=0, label_visibility="collapsed")
            
            # Botão para abrir o popup de novo cliente
            if col_c2.button("➕ Novo Cliente", use_container_width=True):
                dialog_novo_cliente()
                
            st.markdown("---")

            # Passo 2: O que está lançando (Permite vender Serviço ou Produto individual)
            tipo_venda = st.radio("O que está vendendo?", ["Serviço", "Produto"], horizontal=True)
            
            if tipo_venda == "Serviço":
                st.markdown(f"<label style='font-size:14px; font-weight:500; color:var(--text-main);'>{gold_icon('service')} Selecionar Serviço Principal</label>", unsafe_allow_html=True)
                servico_opcoes = [s.nome for s in servicos]
                item_selecionado = st.selectbox("Serviço Principal", servico_opcoes if servico_opcoes else ["Nenhum serviço cadastrado"], label_visibility="collapsed")
                
                valor_sugerido = 0.0
                if item_selecionado and item_selecionado != "Nenhum serviço cadastrado":
                    serv = next((s for s in servicos if s.nome == item_selecionado), None)
                    valor_sugerido = serv.preco_padrao if serv else 0.0
            else:
                st.markdown(f"<label style='font-size:14px; font-weight:500; color:var(--text-main);'>{gold_icon('box')} Selecionar Produto</label>", unsafe_allow_html=True)
                produto_opcoes = [p.nome for p in produtos]
                item_selecionado = st.selectbox("Produto Principal", produto_opcoes if produto_opcoes else ["Nenhum produto cadastrado"], label_visibility="collapsed")
                
                valor_sugerido = 0.0
                if item_selecionado and item_selecionado != "Nenhum produto cadastrado":
                    prod = next((p for p in produtos if p.nome == item_selecionado), None)
                    valor_sugerido = prod.preco_venda if prod else 0.0
            
            col_preco, col_space = st.columns([1.5, 2], vertical_alignment="bottom")
            valor_final = col_preco.number_input("Valor (R$)", value=valor_sugerido, min_value=0.0)
            
            st.markdown("---")
            
            # Passo 3: Forma de Pagamento em Botões/Quadrados elegantes lado a lado
            st.markdown(f"<label style='font-size:14px; font-weight:500; color:var(--text-main);'>{gold_icon('payment')} Selecionar Forma de Pagamento</label>", unsafe_allow_html=True)
            col_p1, col_p2, col_p3 = st.columns(3)
            
            with col_p1:
                is_sel = st.session_state['selected_payment'] == 'Débito'
                if st.button("💳\nDébito", type="primary" if is_sel else "secondary", use_container_width=True, key="pay_deb"):
                    st.session_state['selected_payment'] = 'Débito'
                    st.rerun()
            with col_p2:
                is_sel = st.session_state['selected_payment'] == 'Pix'
                if st.button("📱\nPix", type="primary" if is_sel else "secondary", use_container_width=True, key="pay_pix"):
                    st.session_state['selected_payment'] = 'Pix'
                    st.rerun()
            with col_p3:
                is_sel = st.session_state['selected_payment'] == 'Crédito'
                if st.button("💵\nCrédito", type="primary" if is_sel else "secondary", use_container_width=True, key="pay_cred"):
                    st.session_state['selected_payment'] = 'Crédito'
                    st.rerun()
            
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
                        forma_pagamento=st.session_state['selected_payment'],
                        data_criacao=obter_hora_local().isoformat() # Fuso Brasília
                    )
                    db.add(novo_atendimento)
                    db.flush()
                    
                    # Adicionar o item (pode ser serviço ou produto)
                    ref_id = 0
                    if tipo_venda == "Serviço":
                        item_ref = db.query(Servico).filter(Servico.nome == item_selecionado).first()
                        ref_id = item_ref.id if item_ref else 0
                    else:
                        item_ref = db.query(Produto).filter(Produto.nome == item_selecionado).first()
                        ref_id = item_ref.id if item_ref else 0
                        
                    if ref_id > 0:
                        novo_item = ItemAtendimento(
                            atendimento_id=novo_atendimento.id,
                            tipo=tipo_venda,
                            referencia_id=ref_id,
                            valor_cobrado=valor_final
                        )
                        db.add(novo_item)
                    
                    db.commit()
                    st.session_state['success_msg'] = f"Venda/Atendimento {codigo_seq} lançado com sucesso no pátio!"
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
                    
                    st.markdown(f"<div style='margin-bottom: 2px; font-size: 15px; font-weight: bold; color: var(--text-main);'>🚘 [{at.codigo}] {cliente_nome}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='margin-bottom: 2px; font-size: 12px; color: var(--text-sec);'><b>Veículo:</b> {cliente_veiculo}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='margin-bottom: 2px; font-size: 12px; color: var(--text-sec);'>{gold_icon('clock')} <b>Entrada:</b> {hora_entrada} <span style='color: var(--warning); font-weight: bold;'>({tempo_decorrido})</span></div>", unsafe_allow_html=True)
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
                    if col_btn1.button("Concluir", key=f"concluir_{at.id}", use_container_width=True):
                        dialog_concluir_atendimento(at.id)
                        
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
        
        # Ordenação de cima para baixo pelo último serviço concluído (ID Decrescente)
        query_finalizados = db.query(Atendimento).filter(Atendimento.status == filtro_status).order_by(Atendimento.id.desc())
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
            
            cliente_nome = cliente_at.nome if cliente_at else 'Desconhecido'
            cliente_veiculo = f"{cliente_at.modelo_veiculo} - {cliente_at.placa_veiculo}" if (cliente_at and cliente_at.modelo_veiculo) else (cliente_at.placa_veiculo if cliente_at else '')
            
            with st.container(border=True):
                # Altura menor e design super compacto para histórico
                status_cor = "color: var(--success);" if at.status == "Finalizado" else "color: var(--danger);"
                st.markdown(f"<div style='margin-bottom: 2px; font-size: 14px; font-weight: bold; {status_cor}'>● {at.status}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='margin-bottom: 2px; font-size: 15px; font-weight: bold; color: var(--text-main);'>🚘 [{at.codigo}] {cliente_nome}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='margin-bottom: 2px; font-size: 12px; color: var(--text-sec);'><b>Veículo:</b> {cliente_veiculo} | <b>Total:</b> R$ {at.valor_total:.2f} | <b>Pgto:</b> {at.forma_pagamento}</div>", unsafe_allow_html=True)
                
                if at.status == "Finalizado":
                    st.markdown(f"<div style='margin-bottom: 2px; font-size: 12px; color: var(--text-sec);'>{gold_icon('clock')} <b>Entrada:</b> {hora_entrada} | <b>Saída:</b> {hora_saida} <i>(Duração: {duracao_str})</i></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='margin-bottom: 2px; font-size: 12px; color: var(--text-sec);'>{gold_icon('calendar')} <b>Data:</b> {hora_entrada}</div>", unsafe_allow_html=True)
                    
                if at.observacoes:
                    st.markdown(f"<div style='font-size: 11px; color: #86868B; font-style: italic; background-color: #F5F5F7; padding: 4px 8px; border-radius: 4px; margin-top: 4px;'>Obs: {at.observacoes}</div>", unsafe_allow_html=True)
