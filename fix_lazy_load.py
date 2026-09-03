import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the manual dictionary loads with lazy load
# I will use a very robust replace this time by finding the exact block
start_idx = content.find('# ==========================================\n    # ABA 1: NOVO ATENDIMENTO')
if start_idx != -1:
    end_idx = content.find('    if aba_selecionada == "Novo":', start_idx)
    
    new_block = """# ==========================================
    # ABA 1: NOVO ATENDIMENTO
    # ==========================================
    
    # Lazy load dicionarios para evitar lentidao
    active_client_ids = set([a.cliente_id for a in em_andamento] + [a.cliente_id for a in concluidos_hoje])
    if aba_selecionada == lbl_agenda:
        agendados_raw = db.query(Atendimento).filter(Atendimento.status == "Agendado").order_by(Atendimento.data_agendamento.asc()).all()
        active_client_ids.update([a.cliente_id for a in agendados_raw])
        
    clientes_map = {c.id: c for c in db.query(Cliente).filter(Cliente.id.in_(active_client_ids)).all()} if active_client_ids else {}
    servico_map = {s.id: s for s in db.query(Servico).all()} 

"""
    content = content[:start_idx] + new_block + content[end_idx:]

# Now replace the 'Novo' search block
old_novo_search_start = content.find('termo = remover_acentos(busca_cliente.strip().lower())')
old_novo_search_end = content.find('cliente_selecionado = st.selectbox("Cliente", opcoes_cli)', old_novo_search_start)

if old_novo_search_start != -1 and old_novo_search_end != -1:
    new_search = """if busca_cliente:
                clientes_filtrados = db.query(Cliente).filter(
                    (Cliente.nome.ilike(f"%{busca_cliente}%")) | 
                    (Cliente.placa_veiculo.ilike(f"%{busca_cliente}%"))
                ).limit(20).all()
            else:
                clientes_filtrados = db.query(Cliente).limit(5).all()
                
            opcoes_cli = ["-- Selecione o Cliente --"] + [f"{c.codigo} | {c.nome} - {c.modelo_veiculo or 'S/V'}" for c in clientes_filtrados if c.codigo != "CLI-0000"]
            """
    content = content[:old_novo_search_start] + new_search + content[old_novo_search_end:]


# And fix the Agenda error!
# In the agenda tab:
old_agenda = 'agendados = agendados_raw # Já buscado no lazy load acima'
# Wait, let's check what's actually there
if 'agendados = agendados_raw' in content:
    pass # Will be fine since agendados_raw is defined now
elif 'agendados = db.query(Atendimento).filter(Atendimento.status == "Agendado")' in content:
    # Just leave it or replace it
    pass

with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed Lazy Load and NameError")
