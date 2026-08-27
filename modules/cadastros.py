import streamlit as st
import pandas as pd
from db_config import get_db, CategoriaFinanceira, SubcategoriaFinanceira, ContaBancaria, Colaborador, Produto, Servico
from modules.fast_launch import gold_icon, dialog_decorator

# ==========================================
# Dialogs de Bancos e Categorias
# ==========================================
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

@dialog_decorator("Novo Produto")
def dialog_novo_produto():
    db = next(get_db())
    nome = st.text_input("Nome do Produto")
    unidade = st.text_input("Unidade de Medida (ex: un, ml, g)")
    preco = st.number_input("Preço de Venda (R$)", min_value=0.0, format="%.2f")
    estoque = st.number_input("Qtd em Estoque", min_value=0.0, format="%.2f")
    
    if st.button("Salvar Produto", type="primary", use_container_width=True):
        if nome:
            np = Produto(nome=nome, unidade_medida=unidade, preco_venda=preco, quantidade_estoque=estoque)
            db.add(np)
            db.commit()
            st.toast("Produto criado!", icon="✅")
            st.rerun()

@dialog_decorator("Novo Serviço")
def dialog_novo_servico():
    db = next(get_db())
    nome = st.text_input("Nome do Serviço")
    preco = st.number_input("Preço Padrão (R$)", min_value=0.0, format="%.2f")
    
    if st.button("Salvar Serviço", type="primary", use_container_width=True):
        if nome:
            ns = Servico(nome=nome, preco_padrao=preco)
            db.add(ns)
            db.commit()
            st.toast("Serviço criado!", icon="✅")
            st.rerun()


# ==========================================
# Renderização Principal
# ==========================================
def render_cadastros():
    st.markdown(f"<h2 style='margin-top:0;'>{gold_icon('database-add')} Central de Cadastros</h2>", unsafe_allow_html=True)
    st.markdown("Gerencie as informações base que alimentam todo o sistema ERP.")
    
    db = next(get_db())
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Categorias e sub categorias", 
        "Bancos",
        "Colaboradores",
        "Produtos",
        "Serviços"
    ])
    
    # --- TAB 1: CATEGORIAS ---
    with tab1:
        st.markdown(f"### {gold_icon('tags')} Categorias Financeiras", unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("+ Nova Categoria", use_container_width=True):
                dialog_nova_categoria()
        with col_c2:
            if st.button("+ Nova Subcategoria", use_container_width=True):
                dialog_nova_subcategoria()
                
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
                            with col_s1:
                                st.write(f"- {s.nome}")
                            with col_s2:
                                if st.button("Excluir", key=f"excluir_sub_{s.id}", help="Excluir subcategoria"):
                                    db.delete(s)
                                    db.commit()
                                    st.rerun()
                    else:
                        st.write("Sem subcategorias.")
                        
    # --- TAB 2: BANCOS ---
    with tab2:
        st.markdown(f"### {gold_icon('bank')} Contas Bancárias", unsafe_allow_html=True)
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("Transferência Interna", use_container_width=True, type="primary"):
                dialog_transferencia()
        with col_b2:
            if st.button("+ Criar Conta", use_container_width=True):
                dialog_nova_conta()
                
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
                if st.button("Editar / Excluir", key=f"edit_banco_{c.id}"):
                    dialog_gerenciar_conta(c.id)

    # --- TAB 3: COLABORADORES ---
    with tab3:
        col_t1, col_t2 = st.columns([4, 1])
        with col_t1:
            st.markdown(f"### {gold_icon('people')} Colaboradores", unsafe_allow_html=True)
        with col_t2:
            if st.button("+ Novo Colaborador", use_container_width=True, type="primary"):
                dialog_novo_colaborador()
                
        st.markdown("---")
        colabs = db.query(Colaborador).all()
        if colabs:
            for c in colabs:
                with st.expander(f"{c.nome} - {c.cargo or 'Sem cargo'}"):
                    c1, c2, c3 = st.columns([2,2,1])
                    with c1:
                        st.write(f"**Telefone:** {c.telefone or 'N/I'}")
                    with c2:
                        st.write(f"**Status:** {'Ativo' if c.ativo else 'Inativo'}")
                    with c3:
                        if st.button("Excluir", key=f"del_colab_{c.id}", type="primary"):
                            db.delete(c)
                            db.commit()
                            st.rerun()
        else:
            st.info("Nenhum colaborador cadastrado.")

    # --- TAB 4: PRODUTOS ---
    with tab4:
        col_p1, col_p2 = st.columns([4, 1])
        with col_p1:
            st.markdown(f"### {gold_icon('box-seam')} Produtos", unsafe_allow_html=True)
        with col_p2:
            if st.button("+ Novo Produto", use_container_width=True, type="primary"):
                dialog_novo_produto()
                
        st.markdown("---")
        produtos = db.query(Produto).all()
        if produtos:
            for p in produtos:
                with st.expander(f"{p.nome}"):
                    p1, p2, p3, p4 = st.columns([1,1,1,1])
                    with p1:
                        st.write(f"**Preço:** R$ {p.preco_venda:,.2f}")
                    with p2:
                        st.write(f"**Estoque:** {p.quantidade_estoque} {p.unidade_medida}")
                    with p3:
                        st.write(f"**Monofásico:** {'Sim' if p.produto_monofasico else 'Não'}")
                    with p4:
                        if st.button("Excluir", key=f"del_prod_{p.id}", type="primary"):
                            db.delete(p)
                            db.commit()
                            st.rerun()
        else:
            st.info("Nenhum produto cadastrado.")

    # --- TAB 5: SERVIÇOS ---
    with tab5:
        col_s1, col_s2 = st.columns([4, 1])
        with col_s1:
            st.markdown(f"### {gold_icon('check2-circle')} Serviços", unsafe_allow_html=True)
        with col_s2:
            if st.button("+ Novo Serviço", use_container_width=True, type="primary"):
                dialog_novo_servico()
                
        st.markdown("---")
        servicos = db.query(Servico).all()
        if servicos:
            for s in servicos:
                with st.expander(f"{s.nome}"):
                    s1, s2 = st.columns([3, 1])
                    with s1:
                        st.write(f"**Preço Padrão:** R$ {s.preco_padrao:,.2f}")
                    with s2:
                        if st.button("Excluir", key=f"del_serv_{s.id}", type="primary"):
                            db.delete(s)
                            db.commit()
                            st.rerun()
        else:
            st.info("Nenhum serviço cadastrado.")
