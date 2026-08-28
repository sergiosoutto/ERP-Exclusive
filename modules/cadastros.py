import streamlit as st
import pandas as pd
from db_config import get_db, CategoriaFinanceira, SubcategoriaFinanceira, ContaBancaria, Colaborador, Produto, Servico, FormaPagamento, Usuario, ServicoInsumo, MetaApp
from modules.fast_launch import gold_icon, dialog_decorator
import hashlib

# ==========================================
# Dialogs de Bancos e Categorias
# ==========================================
@dialog_decorator("Nova Meta")
def dialog_nova_meta():
    db = next(get_db())
    desc = st.text_input("Descrição (Ex: Agosto/2026)")
    val = st.number_input("Valor Total (R$)", min_value=0.0)
    c1, c2 = st.columns(2)
    with c1: d1 = st.date_input("Data Inicial")
    with c2: d2 = st.date_input("Data Final")
    if st.button("Salvar Meta", type="primary", use_container_width=True):
        db.add(MetaApp(descricao=desc, valor=val, data_inicial=d1, data_final=d2))
        db.commit()
        st.rerun()

@dialog_decorator("Nova Transferência Interna")
def dialog_transferencia():
    db = next(get_db())
    contas = db.query(ContaBancaria).all()
    contas_nomes = [c.nome for c in contas]
    
    origem = st.selectbox("Conta de Origem (-)", contas_nomes, key="transf_origem")
    destino = st.selectbox("Conta Destino (+)", contas_nomes, key="transf_destino")
    valor = st.number_input("Valor da Transferência (R$)", min_value=0.01, format="%.2f")
    
    if st.button("Realizar Transferência", type="primary", use_container_width=True):
        if origem and destino and origem != destino:
            c_origem = db.query(ContaBancaria).filter(ContaBancaria.nome == origem).first()
            c_destino = db.query(ContaBancaria).filter(ContaBancaria.nome == destino).first()
            if c_origem.saldo_atual >= valor:
                c_origem.saldo_atual -= valor
                c_destino.saldo_atual += valor
                db.commit()
                st.toast("Transferência realizada com sucesso!", icon="✅")
            else:
                st.error("Saldo insuficiente na conta de origem.")
        else:
            st.error("Selecione contas diferentes e válidas.")

@dialog_decorator("Gerenciar Conta")
def dialog_gerenciar_conta(conta_id):
    db = next(get_db())
    c = db.query(ContaBancaria).filter(ContaBancaria.id == conta_id).first()
    if not c: return
    
    novo_nome = st.text_input("Nome da Conta", c.nome)
    novo_saldo = st.number_input("Saldo Atual (Ajuste Manual)", value=c.saldo_atual, format="%.2f")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Atualizar Conta", type="primary", use_container_width=True):
            c.nome = novo_nome
            c.saldo_atual = novo_saldo
            db.commit()
            st.toast("Conta atualizada!", icon="✅")
    with col2:
        if st.button("Excluir Conta", use_container_width=True):
            db.delete(c)
            db.commit()
            st.toast("Conta excluída!", icon="✅")

@dialog_decorator("Nova Conta Bancária")
def dialog_nova_conta():
    db = next(get_db())
    nome = st.text_input("Nome da Conta", placeholder="Ex: Conta BB, Caixa Físico...")
    saldo = st.number_input("Saldo Inicial (R$)", value=0.0, format="%.2f")
    if st.button("Criar Conta", type="primary", use_container_width=True):
        if nome:
            nc = ContaBancaria(nome=nome, saldo_atual=saldo)
            db.add(nc)
            db.commit()
            st.toast("Conta criada!", icon="✅")

@dialog_decorator("Nova Categoria")
def dialog_nova_categoria():
    db = next(get_db())
    tipo = st.radio("Tipo", ["Receita", "Despesa"], horizontal=True)
    nome = st.text_input("Nome da Categoria")
    
    contas = db.query(ContaBancaria).all()
    contas_nomes = ["Nenhum (Opcional)"] + [c.nome for c in contas]
    banco_sel = st.selectbox("Banco Padrão para Baixa", contas_nomes)
    
    if st.button("Salvar Categoria", type="primary", use_container_width=True):
        if nome:
            banco_id = None
            if banco_sel != "Nenhum (Opcional)":
                banco = db.query(ContaBancaria).filter(ContaBancaria.nome == banco_sel).first()
                if banco:
                    banco_id = banco.id
            nova_cat = CategoriaFinanceira(nome=nome, tipo=tipo, banco_padrao_id=banco_id)
            db.add(nova_cat)
            try:
                db.commit()
                st.toast("Categoria criada com sucesso!", icon="✅")
            except Exception:
                db.rollback()
                st.error("Erro: Já existe uma categoria com este nome.")
        else:
            st.error("O nome da categoria é obrigatório.")

@dialog_decorator("Nova Subcategoria")
def dialog_nova_subcategoria():
    db = next(get_db())
    categorias = db.query(CategoriaFinanceira).all()
    cat_nomes = [c.nome for c in categorias]
    cat_sel = st.selectbox("Categoria Pai", options=cat_nomes if cat_nomes else ["Nenhuma"])
    nome = st.text_input("Nome da Subcategoria")
    
    contas = db.query(ContaBancaria).all()
    contas_nomes = ["Nenhum"] + [c.nome for c in contas]
    banco_padrao = st.selectbox("Banco Padrão para Baixa (Opcional)", contas_nomes)
    
    if st.button("Salvar Subcategoria", type="primary", use_container_width=True):
        if nome and cat_sel != "Nenhuma":
            cat = db.query(CategoriaFinanceira).filter(CategoriaFinanceira.nome == cat_sel).first()
            if cat:
                bp_id = None
                if banco_padrao != "Nenhum":
                    banco = db.query(ContaBancaria).filter(ContaBancaria.nome == banco_padrao).first()
                    if banco: bp_id = banco.id
                    
                n_sub = SubcategoriaFinanceira(nome=nome, categoria_id=cat.id, banco_padrao_id=bp_id)
                db.add(n_sub)
                db.commit()
                st.toast("Subcategoria criada!", icon="✅")

# ==========================================
# Dialogs Formas de Pagamento e Usuários
# ==========================================
@dialog_decorator("Nova Forma de Pagamento")
def dialog_nova_forma_pagamento():
    db = next(get_db())
    nome = st.text_input("Nome da Forma de Pagamento")
    c1, c2 = st.columns(2)
    with c1:
        tx_vista = st.number_input("Taxa à Vista (%)", min_value=0.0, format="%.2f")
    with c2:
        tx_parcela = st.number_input("Taxa por Parcela (%)", min_value=0.0, format="%.2f")
    
    if st.button("Salvar", type="primary", use_container_width=True):
        if nome:
            fp = FormaPagamento(nome=nome, taxa_juros_vista=tx_vista, taxa_juros_parcela=tx_parcela)
            db.add(fp)
            db.commit()
            st.rerun()

@dialog_decorator("Novo Usuário")
def dialog_novo_usuario():
    db = next(get_db())
    username = st.text_input("Username")
    password = st.text_input("Senha", type="password")
    role = st.selectbox("Nível de Acesso", ["admin", "basico"])
    
    if st.button("Criar Usuário", type="primary", use_container_width=True):
        if username and password:
            usr = Usuario(username=username, password_hash=hashlib.sha256(password.encode()).hexdigest(), role=role)
            db.add(usr)
            db.commit()
            st.rerun()


# ==========================================
# Dialogs de Colaboradores, Produtos e Serviços
# ==========================================
@dialog_decorator("Novo Colaborador")
def dialog_novo_colaborador():
    db = next(get_db())
    nome = st.text_input("Nome do Colaborador")
    cargo = st.text_input("Cargo")
    telefone = st.text_input("Telefone")
    
    if st.button("Salvar Colaborador", type="primary", use_container_width=True):
        if nome:
            nc = Colaborador(nome=nome, cargo=cargo, telefone=telefone)
            db.add(nc)
            db.commit()
            st.toast("Colaborador criado!", icon="✅")
            st.rerun()

@dialog_decorator("Novo Insumo (Produto)")
def dialog_novo_produto():
    db = next(get_db())
    nome = st.text_input("Nome do Insumo")
    unidade = st.text_input("Unidade de Medida (ex: un, ml, g)")
    custo = st.number_input("Custo por Unidade (R$)", min_value=0.0, format="%.4f")
    estoque = st.number_input("Qtd em Estoque", min_value=0.0, format="%.2f")
    
    if st.button("Salvar Insumo", type="primary", use_container_width=True):
        if nome:
            np = Produto(nome=nome, unidade_medida=unidade, custo_unidade=custo, quantidade_estoque=estoque)
            db.add(np)
            db.commit()
            st.toast("Insumo criado!", icon="✅")
            st.rerun()

@dialog_decorator("Novo Serviço")
def dialog_novo_servico():
    db = next(get_db())
    st.markdown("### Configuração do Serviço")
    nome = st.text_input("Nome do Serviço")
    preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.0, format="%.2f")
    
    st.markdown("---")
    st.markdown("#### Custos Operacionais")
    c1, c2, c3 = st.columns(3)
    with c1: custo_agua = st.number_input("Proporcional Água (R$)", min_value=0.0, format="%.2f")
    with c2: custo_luz = st.number_input("Proporcional Luz (R$)", min_value=0.0, format="%.2f")
    with c3: custo_fixo = st.number_input("Custo Fixo Extra (R$)", min_value=0.0, format="%.2f")
    
    st.markdown("---")
    st.markdown("#### Insumos Utilizados")
    produtos_db = db.query(Produto).all()
    produtos_dict = {p.id: p for p in produtos_db}
    produtos_nomes = {p.nome: p.id for p in produtos_db}
    
    selecionados = st.multiselect("Selecione os insumos", list(produtos_nomes.keys()))
    
    insumos_qtd = {}
    custo_insumos = 0.0
    
    if selecionados:
        for sel in selecionados:
            p_id = produtos_nomes[sel]
            p_obj = produtos_dict[p_id]
            qtd = st.number_input(f"Qtd. de {sel} ({p_obj.unidade_medida})", min_value=0.0, format="%.4f", key=f"insumo_{p_id}")
            insumos_qtd[p_id] = qtd
            custo_insumos += qtd * p_obj.custo_unidade
            
    custo_total = custo_agua + custo_luz + custo_fixo + custo_insumos
    lucro = preco_venda - custo_total
    margem = (lucro / preco_venda * 100) if preco_venda > 0 else 0.0
    
    st.markdown(f"**Custo Total Estimado:** R$ {custo_total:,.2f}")
    st.markdown(f"**Margem de Lucro Projetada:** {margem:.1f}% (R$ {lucro:,.2f})")
    
    if st.button("Salvar Serviço Completo", type="primary", use_container_width=True):
        if nome:
            ns = Servico(
                nome=nome, preco_padrao=preco_venda, 
                custo_agua=custo_agua, custo_luz=custo_luz, 
                custo_fixo=custo_fixo, custo_total=custo_total, 
                margem_lucro=margem
            )
            db.add(ns)
            db.commit() # Commit to get ID
            
            for p_id, qtd in insumos_qtd.items():
                if qtd > 0:
                    si = ServicoInsumo(servico_id=ns.id, produto_id=p_id, quantidade_utilizada=qtd)
                    db.add(si)
            db.commit()
            
            st.toast("Serviço configurado!", icon="✅")
            st.rerun()


# ==========================================
# Renderização Principal
# ==========================================
def render_cadastros():
    st.markdown(f"<h2 style='margin-top:0;'>{gold_icon('database-add')} Central de Cadastros</h2>", unsafe_allow_html=True)
    st.markdown("Gerencie as configurações financeiras, operacionais e de equipe.")
    
    db = next(get_db())
    
    t_cat, t_banco, t_colab, t_insumo, t_servico, t_pag, t_usr, t_meta = st.tabs([
        "Categorias", 
        "Bancos",
        "Colaboradores",
        "Insumos",
        "Serviços",
        "Formas de Pgto",
        "Usuários",
        "Metas"
    ])
    
    # --- TAB 1: CATEGORIAS ---
    with t_cat:
        st.markdown(f"### {gold_icon('tags')} Categorias Financeiras", unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("+ Nova Categoria", use_container_width=True): dialog_nova_categoria()
        with col_c2:
            if st.button("+ Nova Subcategoria", use_container_width=True): dialog_nova_subcategoria()
                
        st.markdown("---")
        categorias = db.query(CategoriaFinanceira).all()
        if categorias:
            for cat in categorias:
                with st.expander(f"{cat.nome} ({cat.tipo})"):
                    if st.button(f"Excluir {cat.nome}", key=f"excluir_cat_{cat.id}"):
                        db.delete(cat)
                        db.commit()
                        st.rerun()
                        
                    subs = db.query(SubcategoriaFinanceira).filter(SubcategoriaFinanceira.categoria_id == cat.id).all()
                    if subs:
                        for s in subs:
                            col_s1, col_s2 = st.columns([3, 1])
                            with col_s1: st.write(f"- {s.nome}")
                            with col_s2:
                                if st.button("Excluir", key=f"excluir_sub_{s.id}"):
                                    db.delete(s)
                                    db.commit()
                                    st.rerun()
                    else:
                        st.write("Sem subcategorias.")
                        
    # --- TAB 2: BANCOS ---
    with t_banco:
        st.markdown(f"### {gold_icon('bank')} Contas Bancárias", unsafe_allow_html=True)
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("Transferência Interna", use_container_width=True, type="primary"): dialog_transferencia()
        with col_b2:
            if st.button("+ Criar Conta", use_container_width=True): dialog_nova_conta()
                
        st.markdown("---")
        contas = db.query(ContaBancaria).all()
        cols = st.columns(3)
        for i, c in enumerate(contas):
            with cols[i % 3]:
                html_card = (
                    f"<div class='premium-card'>"
                    f"<div style='display:flex; justify-content: space-between;'>"
                    f"<h4 style='margin:0;'>{c.nome}</h4>"
                    f"{gold_icon('bank')}"
                    f"</div>"
                    f"<h3 style='color: {'var(--success)' if c.saldo_atual >= 0 else 'var(--danger)'}; margin-top: 5px; font-weight: 500;'>R$ {c.saldo_atual:,.2f}</h3>"
                    f"</div>"
                )
                st.markdown(html_card, unsafe_allow_html=True)
                if st.button("Editar / Excluir", key=f"edit_banco_{c.id}"): dialog_gerenciar_conta(c.id)

    # --- TAB 3: COLABORADORES ---
    with t_colab:
        col_t1, col_t2 = st.columns([4, 1])
        with col_t1: st.markdown(f"### {gold_icon('people')} Colaboradores", unsafe_allow_html=True)
        with col_t2:
            if st.button("+ Novo Colaborador", use_container_width=True, type="primary"): dialog_novo_colaborador()
                
        st.markdown("---")
        colabs = db.query(Colaborador).all()
        if colabs:
            for c in colabs:
                with st.expander(f"{c.nome} - {c.cargo or 'Sem cargo'}"):
                    c1, c2, c3 = st.columns([2,2,1])
                    with c1: st.write(f"**Telefone:** {c.telefone or 'N/I'}")
                    with c2: st.write(f"**Status:** {'Ativo' if c.ativo else 'Inativo'}")
                    with c3:
                        if st.button("Excluir", key=f"del_colab_{c.id}", type="primary"):
                            db.delete(c)
                            db.commit()
                            st.rerun()

    # --- TAB 4: INSUMOS ---
    with t_insumo:
        col_p1, col_p2 = st.columns([4, 1])
        with col_p1: st.markdown(f"### {gold_icon('box-seam')} Insumos (Estoque)", unsafe_allow_html=True)
        with col_p2:
            if st.button("+ Novo Insumo", use_container_width=True, type="primary"): dialog_novo_produto()
                
        st.markdown("---")
        produtos = db.query(Produto).all()
        if produtos:
            for p in produtos:
                with st.expander(f"{p.nome}"):
                    p1, p2, p4 = st.columns([1,1,1])
                    with p1: st.write(f"**Custo Unitário:** R$ {p.custo_unidade:,.4f}")
                    with p2: st.write(f"**Estoque:** {p.quantidade_estoque} {p.unidade_medida}")
                    with p4:
                        if st.button("Excluir", key=f"del_prod_{p.id}", type="primary"):
                            db.delete(p)
                            db.commit()
                            st.rerun()

    # --- TAB 5: SERVIÇOS ---
    with t_servico:
        col_s1, col_s2 = st.columns([4, 1])
        with col_s1: st.markdown(f"### {gold_icon('check2-circle')} Serviços de Estética", unsafe_allow_html=True)
        with col_s2:
            if st.button("+ Novo Serviço", use_container_width=True, type="primary"): dialog_novo_servico()
                
        st.markdown("---")
        servicos = db.query(Servico).all()
        if servicos:
            for s in servicos:
                with st.expander(f"{s.nome} - Venda: R$ {s.preco_padrao:,.2f} | Margem: {s.margem_lucro:.1f}%"):
                    s1, s2 = st.columns([3, 1])
                    with s1:
                        st.write(f"**Custo Total (Fixos + Insumos):** R$ {s.custo_total:,.2f}")
                        insumos = db.query(ServicoInsumo).filter(ServicoInsumo.servico_id == s.id).all()
                        if insumos:
                            st.write("**Insumos Consumidos por aplicação:**")
                            for ins in insumos:
                                p = db.query(Produto).filter(Produto.id == ins.produto_id).first()
                                st.write(f"- {p.nome}: {ins.quantidade_utilizada} {p.unidade_medida}")
                    with s2:
                        if st.button("Excluir", key=f"del_serv_{s.id}", type="primary"):
                            db.delete(s)
                            db.commit()
                            st.rerun()

    # --- TAB 6: FORMAS DE PAGAMENTO ---
    with t_pag:
        col_f1, col_f2 = st.columns([4, 1])
        with col_f1: st.markdown(f"### {gold_icon('credit-card')} Formas de Pagamento", unsafe_allow_html=True)
        with col_f2:
            if st.button("+ Nova Forma", use_container_width=True, type="primary"): dialog_nova_forma_pagamento()
                
        st.markdown("---")
        fps = db.query(FormaPagamento).all()
        if fps:
            for f in fps:
                with st.expander(f"{f.nome}"):
                    c1, c2, c3 = st.columns([1,1,1])
                    with c1: st.write(f"**Tx à Vista:** {f.taxa_juros_vista}%")
                    with c2: st.write(f"**Tx Parcelado:** {f.taxa_juros_parcela}%")
                    with c3:
                        if st.button("Excluir", key=f"del_fp_{f.id}", type="primary"):
                            db.delete(f)
                            db.commit()
                            st.rerun()

    # --- TAB 7: USUÁRIOS ---
    with t_usr:
        col_u1, col_u2 = st.columns([4, 1])
        with col_u1: st.markdown(f"### {gold_icon('person-badge')} Gestão de Acessos", unsafe_allow_html=True)
        with col_u2:
            if st.button("+ Novo Usuário", use_container_width=True, type="primary"): dialog_novo_usuario()
                
        st.markdown("---")
        usrs = db.query(Usuario).all()
        if usrs:
            for u in usrs:
                with st.expander(f"@{u.username} ({u.role})"):
                    if u.username == 'admin':
                        st.info("O usuário admin padrão não pode ser excluído.")
                    else:
                        if st.button("Excluir", key=f"del_usr_{u.id}", type="primary"):
                            db.delete(u)
                            db.commit()
                            st.rerun()

    # --- TAB 8: METAS ---
    with t_meta:
        col_m1, col_m2 = st.columns([4, 1])
        with col_m1: st.markdown(f"### {gold_icon('graph-up')} Gestão de Metas", unsafe_allow_html=True)
        with col_m2:
            if st.button("+ Nova Meta", use_container_width=True, type="primary"): dialog_nova_meta()
                
        st.markdown("---")
        metas = db.query(MetaApp).order_by(MetaApp.data_inicial.desc()).all()
        if metas:
            for m in metas:
                with st.expander(f"{m.descricao} (R$ {m.valor:,.2f})"):
                    st.write(f"**Período:** {m.data_inicial.strftime('%d/%m/%Y')} a {m.data_final.strftime('%d/%m/%Y')}")
                    if st.button("Excluir", key=f"del_meta_{m.id}", type="primary"):
                        db.delete(m)
                        db.commit()
                        st.rerun()
        else:
            st.info("Nenhuma meta cadastrada.")
