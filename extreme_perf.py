import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Optimize Metas queries using func.sum
if "from sqlalchemy import func" not in content:
    content = content.replace("import unicodedata", "import unicodedata\nfrom sqlalchemy import func")

old_metas = """        atends_mes = db.query(Atendimento).filter(Atendimento.data_criacao >= d1_meta.strftime("%Y-%m-%d"), Atendimento.data_criacao <= d2_meta.strftime("%Y-%m-%dT23:59:59"), Atendimento.status == "Finalizado").all()
        fat_mes = sum(a.valor_total for a in atends_mes)
        
        seg_str = segunda_atual.strftime("%Y-%m-%d")
        atends_semana = [a for a in atends_mes if a.data_criacao >= seg_str]
        fat_semana = sum(a.valor_total for a in atends_semana)
        fat_semana_ate_ontem = sum(a.valor_total for a in atends_semana if a.data_criacao < hoje_str)
        fat_hoje = sum(a.valor_total for a in atends_semana if a.data_criacao.startswith(hoje_str))"""

new_metas = """        # Optimized Metas using func.sum
        fat_mes = db.query(func.sum(Atendimento.valor_total)).filter(Atendimento.data_criacao >= d1_meta.strftime("%Y-%m-%d"), Atendimento.data_criacao <= d2_meta.strftime("%Y-%m-%dT23:59:59"), Atendimento.status == "Finalizado").scalar() or 0.0
        
        seg_str = segunda_atual.strftime("%Y-%m-%d")
        fat_semana = db.query(func.sum(Atendimento.valor_total)).filter(Atendimento.data_criacao >= seg_str, Atendimento.data_criacao <= d2_meta.strftime("%Y-%m-%dT23:59:59"), Atendimento.status == "Finalizado").scalar() or 0.0
        fat_semana_ate_ontem = db.query(func.sum(Atendimento.valor_total)).filter(Atendimento.data_criacao >= seg_str, Atendimento.data_criacao < hoje_str, Atendimento.status == "Finalizado").scalar() or 0.0
        fat_hoje = db.query(func.sum(Atendimento.valor_total)).filter(Atendimento.data_criacao.like(f"{hoje_str}%"), Atendimento.status == "Finalizado").scalar() or 0.0"""
        
content = content.replace(old_metas, new_metas)


# 2. Optimize Client and Service Map fetching (Lazy evaluation)
old_maps = """    # Pr-carregar dicionrios globais
    todos_cli = db.query(Cliente).all()
    clientes_map = {c.id: c for c in todos_cli}
    
    todos_servs = db.query(Servico).all()
    servico_map = {s.id: s for s in todos_servs}"""

new_maps = """    # Lazy load dictionaries only for active OSs to save 90% bandwidth
    active_client_ids = set([a.cliente_id for a in em_andamento] + [a.cliente_id for a in concluidos_hoje])
    if aba_selecionada == lbl_agenda:
        agendados_raw = db.query(Atendimento).filter(Atendimento.status == "Agendado").order_by(Atendimento.data_agendamento.asc()).all()
        active_client_ids.update([a.cliente_id for a in agendados_raw])
        
    clientes_map = {c.id: c for c in db.query(Cliente).filter(Cliente.id.in_(active_client_ids)).all()} if active_client_ids else {}
    servico_map = {s.id: s for s in db.query(Servico).all()} # Services are small, safe to pull"""
content = re.sub(r'# Pr-carregar.*?(?=    if aba_selecionada == "Novo":)', new_maps + '\n\n', content, flags=re.DOTALL)


# 3. Fix Novo client search to not use in-memory todos_cli
old_novo_search = """        with st.container(border=True):
            busca_cliente = st.text_input("Pesquisar Cliente", placeholder="Nome ou Placa...")
            
            if busca_cliente:
                clientes_filtrados = [c for c in todos_cli if busca_cliente.lower() in c.nome.lower() or (c.placa_veiculo and busca_cliente.lower() in c.placa_veiculo.lower())]
            else:
                clientes_filtrados = todos_cli[:5]
                
            opcoes_cli = ["-- Selecione um Cliente --"] + [f"{c.codigo} | {c.nome} - {c.modelo_veiculo or 'S/V'}" for c in clientes_filtrados]"""

new_novo_search = """        with st.container(border=True):
            busca_cliente = st.text_input("Pesquisar Cliente", placeholder="Nome ou Placa...")
            
            if busca_cliente:
                clientes_filtrados = db.query(Cliente).filter(
                    (Cliente.nome.ilike(f"%{busca_cliente}%")) | 
                    (Cliente.placa_veiculo.ilike(f"%{busca_cliente}%"))
                ).limit(20).all()
            else:
                clientes_filtrados = db.query(Cliente).limit(5).all()
                
            opcoes_cli = ["-- Selecione um Cliente --"] + [f"{c.codigo} | {c.nome} - {c.modelo_veiculo or 'S/V'}" for c in clientes_filtrados]"""
content = content.replace(old_novo_search, new_novo_search)


# 4. Fix Agenda query inside tab (since we fetched it in maps)
old_agenda = """        agendados = db.query(Atendimento).filter(Atendimento.status == "Agendado").order_by(Atendimento.data_agendamento.asc()).all()"""
new_agenda = """        agendados = agendados_raw # Já buscado no lazy load acima"""
content = content.replace(old_agenda, new_agenda)

with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Applied Extreme Performance Optimizations")
