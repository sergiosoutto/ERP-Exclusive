import re

with open('modules/cadastros.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace dialog_novo_usuario and add dialog_editar_usuario
new_user_dialogs = """
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
    pode_excluir = st.checkbox("Pode excluir registros", value=u.pode_excluir, key=f"edit_pode_excluir_{u_id}")
    
    if st.button("Salvar Alterações", type="primary", use_container_width=True):
        if nova_senha:
            u.password_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
        u.permissoes = ",".join(permissoes_selecionadas)
        u.pode_excluir = pode_excluir
        db.commit()
        from db_config import registrar_log
        registrar_log(f"Editou permissões do usuário '{u.username}'")
        st.rerun()
"""

# Replace the old dialog
old_dialog = """@dialog_decorator("Novo Usuário")
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
            st.rerun()"""

if "def dialog_editar_usuario" not in content:
    content = content.replace(old_dialog, new_user_dialogs)
    if "MENUS_DISPONIVEIS" not in content: # just in case old_dialog was slightly different
        # Let's use regex
        content = re.sub(r'@dialog_decorator\("Novo Usuário"\).*?st\.rerun\(\)', new_user_dialogs, content, flags=re.DOTALL)

# Now inject the Log Tab in render_cadastros
# We need to change tabs to 8 tabs instead of 7
tabs_def = 't_cat, t_banco, t_metas, t_prod, t_serv, t_pag, t_usr = st.tabs(["Categorias", "Bancos", "Metas", "Produtos", "Serviços", "Pagamentos", "Usuários"])'
new_tabs_def = 't_cat, t_banco, t_metas, t_prod, t_serv, t_pag, t_usr, t_log = st.tabs(["Categorias", "Bancos", "Metas", "Produtos", "Serviços", "Pagamentos", "Usuários", "Histórico / Logs"])'
content = content.replace(tabs_def, new_tabs_def)

# Find the end of TAB 7: USUARIOS and replace its UI
tab_users_old = """    # --- TAB 7: USUÁRIOS ---
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
                            st.rerun()"""

tab_users_new = """    # --- TAB 7: USUÁRIOS ---
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
                    st.write(f"**Pode Excluir:** {'Sim' if u.pode_excluir or u.role == 'admin' else 'Não'}")
                    
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
"""
if "# --- TAB 8: LOGS ---" not in content:
    content = content.replace(tab_users_old, tab_users_new)

with open('modules/cadastros.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated cadastros.py for users and logs")
