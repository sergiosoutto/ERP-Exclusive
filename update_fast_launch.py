import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add the 'agendar' logic before the button
agendar_ui = """
            c_ag1, c_ag2 = st.columns([1, 2])
            with c_ag1:
                is_agendamento = st.checkbox("Agendar OS?", value=False)
            with c_ag2:
                data_agendamento = None
                if is_agendamento:
                    data_agendamento = st.date_input("Data do Serviço")
                    
            btn_label = "Agendar Serviço" if is_agendamento else "Enviar para o Pátio"
            if st.button(btn_label, type="primary", use_container_width=True):
"""

content = content.replace('            if st.button("Enviar para o Pátio", type="primary", use_container_width=True):', agendar_ui)

# Update the new Atendimento logic
novo_at_old = """                    novo_at = Atendimento(
                        codigo=codigo_seq, cliente_id=cliente_ref.id, status="Em Andamento",
                        valor_total=total_atendimento, data_criacao=obter_hora_local().isoformat()
                    )"""

novo_at_new = """                    stts = "Agendado" if is_agendamento else "Em Andamento"
                    dt_agend = data_agendamento.isoformat() if is_agendamento and data_agendamento else None
                    novo_at = Atendimento(
                        codigo=codigo_seq, cliente_id=cliente_ref.id, status=stts,
                        valor_total=total_atendimento, data_criacao=obter_hora_local().isoformat(),
                        data_agendamento=dt_agend
                    )"""
                    
if 'stts = "Agendado"' not in content:
    content = content.replace(novo_at_old, novo_at_new)

# Add pill with bell icon
# Look for: abas_disponiveis = ["Novo", lbl_patio, lbl_hist, "Resumo"]
abas_old = 'abas_disponiveis = ["Novo", lbl_patio, lbl_hist, "Resumo"]'
abas_new = """
    lbl_agenda = f"{gold_icon('bell')} Agenda"
    abas_disponiveis = ["Novo", lbl_patio, lbl_hist, lbl_agenda, "Resumo"]
"""
if "lbl_agenda =" not in content:
    content = content.replace(abas_old, abas_new)

# Add the handling for lbl_agenda
agenda_handling = """
    # ==========================================
    # ABA: AGENDA (Agendados)
    # ==========================================
    elif aba_selecionada == lbl_agenda:
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
                        dt_str = at.data_agendamento
                        
                with st.container(border=True):
                    st.markdown(f"<p style='margin:0; font-size:14px; font-weight:600;'>{cli_nome} <span style='font-size:10px; font-weight:normal; color:var(--text-sec);'>({at.codigo})</span></p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:0; font-size:12px; color:var(--text-sec);'>*{carro} | Placa: {placa}*</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:2px 0 6px 0; font-size:12px;'>{gold_icon('calendar-check')} <b>{dt_str}</b> &nbsp;|&nbsp; <b>R$ {formatar_moeda(at.valor_total)}</b></p>", unsafe_allow_html=True)
                    
                    options = ["Iniciar OS", "Excluir"] if st.session_state.get("pode_excluir", False) else ["Iniciar OS"]
                    op_ag = st.pills("Ações Agenda", options=options, key=f"pill_ag_{at.id}", label_visibility="collapsed")
                    
                    if op_ag == "Iniciar OS":
                        at.status = "Em Andamento"
                        at.data_agendamento = None
                        at.data_criacao = obter_hora_local().isoformat()
                        db.commit()
                        st.rerun()
                    elif op_ag == "Excluir":
                        db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id == at.id).delete()
                        db.delete(at)
                        db.commit()
                        st.rerun()

"""

if "lbl_agenda:" not in content:
    content = content.replace('    elif aba_selecionada == "Resumo":', agenda_handling + '    elif aba_selecionada == "Resumo":')


# Need to fix the lbl_agenda pill number (bell with number of scheduled services TODAY)
pill_number_logic = """
    # Contagem de Agendados para hoje
    agendados_hoje = db.query(Atendimento).filter(Atendimento.status == "Agendado", Atendimento.data_agendamento.like(f"{hoje_str_patio}%")).count()
    if agendados_hoje > 0:
        lbl_agenda = f"{gold_icon('bell-fill')} Agenda ({agendados_hoje})"
    else:
        lbl_agenda = f"{gold_icon('bell')} Agenda"
    abas_disponiveis = ["Novo", lbl_patio, lbl_hist, lbl_agenda, "Resumo"]
"""

if "agendados_hoje = db.query(Atendimento)" not in content:
    content = content.replace('    lbl_agenda = f"{gold_icon(\'bell\')} Agenda"\n    abas_disponiveis = ["Novo", lbl_patio, lbl_hist, lbl_agenda, "Resumo"]', pill_number_logic)

with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated fast_launch with Agendamento')
