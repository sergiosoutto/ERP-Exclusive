
def formatar_moeda(valor):
    try:
        return f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return '0,00'

import streamlit as st
from datetime import datetime
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
    
    st.markdown("<div style='font-size:12px; font-weight:bold; margin-top:10px;'>Pesos por Dia da Semana (%)</div>", unsafe_allow_html=True)
    c_seg, c_ter, c_qua = st.columns(3)
    p_seg = c_seg.number_input("Segunda", value=15.0, min_value=0.0)
    p_ter = c_ter.number_input("Terça", value=15.0, min_value=0.0)
    p_qua = c_qua.number_input("Quarta", value=15.0, min_value=0.0)
    
    c_qui, c_sex, c_sab = st.columns(3)
    p_qui = c_qui.number_input("Quinta", value=15.0, min_value=0.0)
    p_sex = c_sex.number_input("Sexta", value=15.0, min_value=0.0)
    p_sab = c_sab.number_input("Sábado", value=25.0, min_value=0.0)
    
    if st.button("Salvar Meta", type="primary", use_container_width=True):
        db.add(MetaApp(
            descricao=desc, valor=val, data_inicial=d1, data_final=d2,
            peso_seg=p_seg, peso_ter=p_ter, peso_qua=p_qua, 
            peso_qui=p_qui, peso_sex=p_sex, peso_sab=p_sab
        ))
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


MENUS_DISPONIVEIS = ["Fluxo do Dia", "CRM", "Estoque", "Financeiro", "Gestão de Pessoal", "Cadastros"]

@dialog_decorator("Novo Usuário")
def dialog_novo_usuario():
    db = next(get_db())
    username = st.text_input("Username")
    password = st.text_input("Senha", type="password")
    
    st.markdown("**Permissões de Menus:**")
    permissoes_selecionadas = []
    for menu in MENUS_DISPONIVEIS:
        if st.checkbox(menu, value=True, key=f"novo_menu_{menu}"):
            permissoes_selecionadas.append(menu)
            
    st.markdown("**Ações:**")
    pode_excluir = st.checkbox("Pode excluir registros", value=False, key="novo_pode_excluir")
    
    if st.button("Criar Usuário", type="primary", use_container_width=True):
        if username and password:
            perm_str = ",".join(permissoes_selecionadas)
            usr = Usuario(
                username=username, 
                password_hash=hashlib.sha256(password.encode()).hexdigest(), 
                role="basico", 
                permissoes=perm_str,
                pode_excluir=pode_excluir
            )
            db.add(usr)
            db.commit()
            from db_config import registrar_log
            registrar_log(f"Criou o usuário '{username}'")
            st.rerun()

@dialog_decorator("Editar Usuário")
def dialog_editar_usuario(u_id):
    db = next(get_db())
    u = db.query(Usuario).filter(Usuario.id == u_id).first()
    if not u: return
    
    st.write(f"Editando: **{u.username}**")
    nova_senha = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password")
    
    if u.username == 'admin':
        st.info("O admin possui acesso total. Você só pode alterar a senha.")
        if st.button("Salvar Admin", type="primary", use_container_width=True):
            if nova_senha:
                u.password_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
                db.commit()
                from db_config import registrar_log
                registrar_log(f"Alterou a senha do Admin")
            st.rerun()
        return
        
    perms_atuais = u.permissoes.split(",") if u.permissoes else []
    if u.permissoes == "todas": perms_atuais = MENUS_DISPONIVEIS
    
    st.markdown("**Permissões de Menus:**")
    permissoes_selecionadas = []
    for menu in MENUS_DISPONIVEIS:
        val_inicial = (menu in perms_atuais)
        if st.checkbox(menu, value=val_inicial, key=f"edit_menu_{menu}_{u_id}"):
            permissoes_selecionadas.append(menu)
            
    st.markdown("**Ações:**")
    pode_excluir = st.checkbox("Pode excluir registros", value=getattr(u, "pode_excluir", False), key=f"edit_pode_excluir_{u_id}")
    
    if st.button("Salvar Alterações", type="primary", use_container_width=True):
        if nova_senha:
            u.password_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
        u.permissoes = ",".join(permissoes_selecionadas)
        u.pode_excluir = pode_excluir
        db.commit()
        from db_config import registrar_log
        registrar_log(f"Editou permissões do usuário '{u.username}'")
        st.rerun()



# ==========================================
# Dialogs de Colaboradores, Produtos e Serviços
# ==========================================
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
    
    st.markdown(f"**Custo Total Estimado:** R$ {formatar_moeda(custo_total)}")
    st.markdown(f"**Margem de Lucro Projetada:** {margem:.1f}% (R$ {formatar_moeda(lucro)})")
    
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
    
    t_cat, t_banco, t_servico, t_pag, t_usr, t_meta = st.tabs([
        "Categorias", 
        "Bancos",
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
                    if st.session_state.get("pode_excluir", False) and st.button(f"Excluir {cat.nome}", key=f"excluir_cat_{cat.id}"):
                        db.delete(cat)
                        db.commit()
                        st.rerun()
                        
                    subs = db.query(SubcategoriaFinanceira).filter(SubcategoriaFinanceira.categoria_id == cat.id).all()
                    if subs:
                        for s in subs:
                            col_s1, col_s2 = st.columns([3, 1])
                            with col_s1: st.write(f"- {s.nome}")
                            with col_s2:
                                if st.session_state.get("pode_excluir", False) and st.button("Excluir", key=f"excluir_sub_{s.id}"):
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
                    f"<h3 style='color: {'var(--success)' if c.saldo_atual >= 0 else 'var(--danger)'}; margin-top: 5px; font-weight: 500;'>R$ {formatar_moeda(c.saldo_atual)}</h3>"
                    f"</div>"
                )
                st.markdown(html_card, unsafe_allow_html=True)
                if st.button("Editar / Excluir", key=f"edit_banco_{c.id}"): dialog_gerenciar_conta(c.id)

    with t_servico:
        col_s1, col_s2 = st.columns([4, 1])
        with col_s1: st.markdown(f"### {gold_icon('check2-circle')} Serviços de Estética", unsafe_allow_html=True)
        with col_s2:
            if st.button("+ Novo Serviço", use_container_width=True, type="primary"): dialog_novo_servico()
                
        st.markdown("---")
        servicos = db.query(Servico).all()
        if servicos:
            for s in servicos:
                with st.expander(f"{s.nome} - Venda: R$ {formatar_moeda(s.preco_padrao)} | Margem: {s.margem_lucro:.1f}%"):
                    s1, s2 = st.columns([3, 1])
                    with s1:
                        st.write(f"**Custo Total (Fixos + Insumos):** R$ {formatar_moeda(s.custo_total)}")
                        insumos = db.query(ServicoInsumo).filter(ServicoInsumo.servico_id == s.id).all()
                        if insumos:
                            st.write("**Insumos Consumidos por aplicação:**")
                            for ins in insumos:
                                p = db.query(Produto).filter(Produto.id == ins.produto_id).first()
                                st.write(f"- {p.nome}: {ins.quantidade_utilizada} {p.unidade_medida}")
                    with s2:
                        if st.session_state.get("pode_excluir", False) and st.button("Excluir", key=f"del_serv_{s.id}", type="primary"):
                            db.query(ServicoInsumo).filter(ServicoInsumo.servico_id == s.id).delete()
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
                        if st.session_state.get("pode_excluir", False) and st.button("Excluir", key=f"del_fp_{f.id}", type="primary"):
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
                    perms = "Todas" if u.permissoes == "todas" or u.role == "admin" else u.permissoes
                    st.write(f"**Permissões:** {perms}")
                    st.write(f"**Pode Excluir:** {'Sim' if getattr(u, 'pode_excluir', False) or u.role == 'admin' else 'Não'}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Editar Usuário", key=f"edit_usr_{u.id}", use_container_width=True):
                            dialog_editar_usuario(u.id)
                    with c2:
                        if u.username == 'admin':
                            st.info("Admin não pode ser excluído.")
                        else:
                            if st.button("Excluir", key=f"del_usr_{u.id}", type="primary", use_container_width=True):
                                from db_config import registrar_log
                                registrar_log(f"Excluiu o usuário '{u.username}'")
                                db.delete(u)
                                db.commit()
                                st.rerun()

    # --- TAB 8: LOGS ---
    with t_log:
        st.markdown(f"### {gold_icon('clock')} Registro de Atividades (Log)", unsafe_allow_html=True)
        from db_config import LogAuditoria
        
        col_l1, col_l2, col_l3 = st.columns(3)
        with col_l1:
            data_filtro = st.date_input("Data do Registro")
        with col_l2:
            usuarios_logs = db.query(LogAuditoria.usuario).distinct().all()
            user_opts = ["Todos"] + [x[0] for x in usuarios_logs if x[0]]
            user_filtro = st.selectbox("Filtrar por Usuário", user_opts)
        with col_l3:
            busca_acao = st.text_input("Buscar na Ação")
            
        logs_query = db.query(LogAuditoria).filter(LogAuditoria.data_hora.like(f"{data_filtro.strftime('%Y-%m-%d')}%"))
        if user_filtro != "Todos":
            logs_query = logs_query.filter(LogAuditoria.usuario == user_filtro)
        if busca_acao:
            logs_query = logs_query.filter(LogAuditoria.acao.ilike(f"%{busca_acao}%"))
            
        logs = logs_query.order_by(LogAuditoria.id.desc()).all()
        
        st.markdown("---")
        if logs:
            for log in logs:
                dt_obj = datetime.fromisoformat(log.data_hora)
                st.markdown(f"<div style='font-size:12px; margin-bottom:10px; border-bottom:1px solid #eee; padding-bottom:5px;'>"
                            f"<span style='color:#888; font-weight:600;'>{dt_obj.strftime('%d/%m/%Y %H:%M:%S')}</span> &nbsp;|&nbsp; "
                            f"<span style='color:#333; font-weight:700;'>@{log.usuario}</span> &nbsp;|&nbsp; "
                            f"<span style='color:var(--text-main);'>{log.acao}</span>"
                            f"</div>", unsafe_allow_html=True)
        else:
            st.info("Nenhum registro encontrado para os filtros selecionados.")


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
                with st.expander(f"{m.descricao} (R$ {formatar_moeda(m.valor)})"):
                    st.write(f"**Período:** {m.data_inicial.strftime('%d/%m/%Y')} a {m.data_final.strftime('%d/%m/%Y')}")
                    if st.session_state.get("pode_excluir", False) and st.button("Excluir", key=f"del_meta_{m.id}", type="primary"):
                        db.delete(m)
                        db.commit()
                        st.rerun()
        else:
            st.info("Nenhuma meta cadastrada.")
