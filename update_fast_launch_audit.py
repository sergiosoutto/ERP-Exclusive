import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Inject registrar_log where needed
if "from db_config import get_db" in content and "registrar_log" not in content.split("def dialog_novo_cliente")[0]:
    content = content.replace(
        "from db_config import engine, get_db, Cliente,",
        "from db_config import engine, get_db, Cliente, registrar_log,"
    )

# A. Novo Cliente
content = content.replace(
    'st.session_state["success_msg"] = "Cliente cadastrado com sucesso!"',
    'registrar_log(f"Cadastrou o cliente: {novo_nome}")\n            st.session_state["success_msg"] = "Cliente cadastrado com sucesso!"'
)

# B. Excluir OS
content = content.replace(
    'db.delete(at)\n        db.commit()',
    'registrar_log(f"Excluiu a OS: {at.codigo}")\n        db.delete(at)\n        db.commit()'
)

# C. Checkout Direct / Concluir OS (Checkout happens in dialog_checkout but we don't have that in fast_launch anymore! 
# Wait, dialog_checkout is still in fast_launch.py!)
# Let's check if dialog_checkout is there. Yes, I saw it earlier.
content = content.replace(
    'at.status = "Finalizado"',
    'registrar_log(f"Finalizou a OS: {at.codigo}")\n        at.status = "Finalizado"'
)

# D. Lançar nova OS
content = content.replace(
    'st.session_state[\'success_msg\'] = f"OS {codigo_seq} enviada ao Pátio!"',
    'registrar_log(f"Lançou a {codigo_seq} para {cliente_ref.nome}")\n                    st.session_state[\'success_msg\'] = f"OS {codigo_seq} enviada ao Pátio!"'
)

# 2. Fix Agendar OS to include time in "Novo" tab
old_agend = """            c_ag1, c_ag2 = st.columns([1, 2])
            with c_ag1:
                is_agendamento = st.checkbox("Agendar OS?", value=False)
            with c_ag2:
                data_agendamento = None
                if is_agendamento:
                    data_agendamento = st.date_input("Data do Serviço")"""

new_agend = """            c_ag1, c_ag2, c_ag3 = st.columns([1, 1.5, 1.5])
            with c_ag1:
                is_agendamento = st.checkbox("Agendar OS?", value=False)
            
            data_agendamento = None
            hora_agendamento = None
            if is_agendamento:
                with c_ag2:
                    data_agendamento = st.date_input("Data do Serviço")
                with c_ag3:
                    import datetime
                    hora_agendamento = st.time_input("Hora", value=datetime.time(9, 0))"""
content = content.replace(old_agend, new_agend)

# Also fix the dt_agend generation
old_dt_agend = 'dt_agend = data_agendamento.isoformat() if is_agendamento and data_agendamento else None'
new_dt_agend = 'dt_agend = f"{data_agendamento.isoformat()} {hora_agendamento.strftime(\'%H:%M\')}" if is_agendamento and data_agendamento and hora_agendamento else (data_agendamento.isoformat() if is_agendamento and data_agendamento else None)'
content = content.replace(old_dt_agend, new_dt_agend)

# 3. Fix Reagendar dialog
old_reag = """    nova_data = st.date_input("Nova Data", value=dt_atual)
    
    if st.button("Confirmar Reagendamento", type="primary", use_container_width=True):
        at.data_agendamento = nova_data.isoformat()"""
        
new_reag = """    nova_data = st.date_input("Nova Data", value=dt_atual)
    import datetime
    nova_hora = st.time_input("Nova Hora", value=datetime.time(9, 0))
    
    if st.button("Confirmar Reagendamento", type="primary", use_container_width=True):
        at.data_agendamento = f"{nova_data.isoformat()} {nova_hora.strftime('%H:%M')}"
        registrar_log(f"Reagendou a OS: {at.codigo}")"""
content = content.replace(old_reag, new_reag)

# 4. Fix Agenda tab logic (total sum, format time, and badge)
# A. Badge
content = content.replace(
    'agendados_hoje = db.query(Atendimento).filter(Atendimento.status == "Agendado", Atendimento.data_agendamento.like(f"{hoje_str_patio}%")).count()',
    'agendados_hoje = db.query(Atendimento).filter(Atendimento.status == "Agendado").count()'
)

# B. Tab content
old_agenda_tab = """    elif aba_selecionada == lbl_agenda:
        st.markdown(f"### {gold_icon('calendar')} Serviços Agendados", unsafe_allow_html=True)
        agendados = db.query(Atendimento).filter(Atendimento.status == "Agendado").order_by(Atendimento.data_agendamento.asc()).all()
        
        if not agendados:
            st.info("Nenhum serviço agendado.")
        else:
            for at in agendados:
                cli = clientes_map.get(at.cliente_id)
                cli_nome = cli.nome if cli else "Desconhecido"
                carro = cli.modelo_veiculo if cli and cli.modelo_veiculo else "Sem Veículo"
                placa = cli.placa_veiculo if cli and cli.placa_veiculo else "Sem Placa"
                dt_str = "Data não definida"
                if at.data_agendamento:
                    try:
                        dt_obj = datetime.fromisoformat(at.data_agendamento)
                        dt_str = dt_obj.strftime('%d/%m/%Y')
                    except:
                        dt_str = at.data_agendamento"""

new_agenda_tab = """    elif aba_selecionada == lbl_agenda:
        st.markdown(f"### {gold_icon('calendar')} Serviços Agendados", unsafe_allow_html=True)
        agendados = db.query(Atendimento).filter(Atendimento.status == "Agendado").order_by(Atendimento.data_agendamento.asc()).all()
        
        if not agendados:
            st.info("Nenhum serviço agendado.")
        else:
            total_agendado = sum(a.valor_total for a in agendados)
            st.markdown(f"<div style='background:#fcfcfc; border:1px solid #eee; border-radius:8px; padding:12px; margin-bottom:15px; display:flex; justify-content:space-between; align-items:center;'><div><span style='font-size:12px; font-weight:700; color:#888; text-transform:uppercase;'>Volume Futuro</span><br><span style='font-size:18px; font-weight:800; color:var(--accent);'>R$ {formatar_moeda(total_agendado)}</span></div><div style='text-align:right;'><span style='font-size:12px; color:#888;'>Total de Veículos</span><br><span style='font-size:18px; font-weight:800;'>{len(agendados)}</span></div></div>", unsafe_allow_html=True)
            
            for at in agendados:
                cli = clientes_map.get(at.cliente_id)
                cli_nome = cli.nome if cli else "Desconhecido"
                carro = cli.modelo_veiculo if cli and cli.modelo_veiculo else "Sem Veículo"
                placa = cli.placa_veiculo if cli and cli.placa_veiculo else "Sem Placa"
                dt_str = "Data não definida"
                if at.data_agendamento:
                    try:
                        # PODE ESTAR EM YYYY-MM-DD ou YYYY-MM-DD HH:MM
                        import datetime
                        if " " in at.data_agendamento:
                            dt_str = datetime.datetime.strptime(at.data_agendamento, "%Y-%m-%d %H:%M").strftime('%d/%m/%Y às %H:%M')
                        else:
                            dt_obj = datetime.datetime.fromisoformat(at.data_agendamento)
                            dt_str = dt_obj.strftime('%d/%m/%Y')
                    except Exception as e:
                        dt_str = str(at.data_agendamento)"""
content = content.replace(old_agenda_tab, new_agenda_tab)

with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Applied Fast Launch Updates')
