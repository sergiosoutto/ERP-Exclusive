import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update OS Creation to use "Aguardando"
content = content.replace('stts = "Agendado" if is_agendamento else "Em Andamento"', 'stts = "Agendado" if is_agendamento else "Aguardando"')

# 2. Update the em_andamento query globally
old_em_andamento_query = 'em_andamento = db.query(Atendimento).filter(Atendimento.status == "Em Andamento").order_by(Atendimento.id.asc()).all()'
new_em_andamento_query = 'em_andamento = db.query(Atendimento).filter(Atendimento.status.in_(["Aguardando", "Em Andamento", "Lavando", "Pronto"])).order_by(Atendimento.id.asc()).all()'
content = content.replace(old_em_andamento_query, new_em_andamento_query)

# 3. Modify the Patio Render Logic
# Search for: `if em_andamento:` block and replace it
# We will use regex to find the whole block:
patio_block_pattern = re.compile(
    r'elif aba_selecionada == lbl_patio:(.*?)elif aba_selecionada == lbl_hist:', 
    re.DOTALL
)

new_patio_block = """elif aba_selecionada == lbl_patio:
        st.markdown(f"### {gold_icon('clock')} Veículos no Pátio", unsafe_allow_html=True)
        
        if em_andamento:
            fila = [a for a in em_andamento if a.status in ("Aguardando", "Em Andamento")]
            lavando = [a for a in em_andamento if a.status == "Lavando"]
            prontos = [a for a in em_andamento if a.status == "Pronto"]
            
            def render_os_card(at):
                cli = clientes_map.get(at.cliente_id)
                itens_at = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id == at.id).all()
                total_val = sum(i.valor_cobrado for i in itens_at)
                
                servs = []
                for i in itens_at:
                    s_nome = "Item"
                    if i.tipo == "Serviço" and i.referencia_id in servico_map:
                        s_nome = servico_map[i.referencia_id].nome
                    servs.append(s_nome)
                
                dt_str = "Agora"
                if at.data_criacao:
                    try:
                        dt = datetime.fromisoformat(at.data_criacao)
                        dt_str = dt.strftime('%H:%M')
                    except: pass
                
                carro_info = cli.modelo_veiculo if cli and cli.modelo_veiculo else "Sem Veículo"
                placa_info = cli.placa_veiculo if cli and cli.placa_veiculo else "Sem Placa"
                
                with st.container(border=True):
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.markdown(f"<p style='margin:0; font-size:14px; font-weight:700; color:var(--text-main);'>{cli.nome if cli else 'Desconhecido'} <span style='font-size:11px; font-weight:normal; color:#888;'>({at.codigo})</span></p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='margin:0; font-size:11px; color:#555;'>*{carro_info} | {placa_info}*</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='margin:2px 0 0 0; font-size:11px;'>Entrada: <b>{dt_str}</b></p>", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"<div style='text-align:right;'><span style='font-size:10px; background:#f0f0f0; padding:2px 6px; border-radius:10px;'>{len(servs)} itens</span><br><span style='font-size:15px; font-weight:800; color:var(--accent);'>R$ {formatar_moeda(total_val)}</span></div>", unsafe_allow_html=True)
                    
                    st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)
                    
                    # Ações Dinâmicas por Status
                    if at.status in ("Aguardando", "Em Andamento"):
                        if st.button(f"▶ Iniciar Lavagem", key=f"btn_ini_{at.id}", type="primary", use_container_width=True):
                            at.status = "Lavando"
                            at.data_inicio = obter_hora_local().isoformat()
                            db.commit()
                            st.toast(f"OS {at.codigo} em execução!")
                            st.rerun()
                    elif at.status == "Lavando":
                        if st.button(f"✔ Sinalizar Pronto", key=f"btn_pro_{at.id}", type="primary", use_container_width=True):
                            at.status = "Pronto"
                            at.data_pronto = obter_hora_local().isoformat()
                            db.commit()
                            st.toast(f"OS {at.codigo} concluída! Aguardando entrega.")
                            st.rerun()
                    elif at.status == "Pronto":
                        if st.button(f"💲 Entregar e Receber", key=f"btn_rec_{at.id}", type="primary", use_container_width=True):
                            dialog_checkout(at.id)
                    
                    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
                    
                    # Pulo Dinâmico / Ações Secundárias
                    options = ["Checkout Direto", "Editar", "Excluir"] if st.session_state.get("pode_excluir", False) else ["Checkout Direto", "Editar"]
                    if at.status == "Pronto": options.remove("Checkout Direto") # Já é a ação principal
                    
                    if options:
                        op_os = st.pills("Outras Ações", options=options, key=f"pill_sec_{at.id}", label_visibility="collapsed")
                        if op_os == "Checkout Direto":
                            dialog_checkout(at.id)
                        elif op_os == "Editar":
                            dialog_editar_os(at.id)
                        elif op_os == "Excluir":
                            dialog_excluir_os(at.id)
            
            c_fila, c_lav, c_pronto = st.columns(3)
            with c_fila:
                st.markdown(f"<div style='text-align:center; padding:5px; background:rgba(0,0,0,0.05); border-radius:8px; margin-bottom:10px; font-weight:700; font-size:13px;'>🚗 Fila ({len(fila)})</div>", unsafe_allow_html=True)
                for a in fila: render_os_card(a)
            with c_lav:
                st.markdown(f"<div style='text-align:center; padding:5px; background:rgba(197, 160, 89, 0.15); border-radius:8px; margin-bottom:10px; font-weight:700; color:var(--accent); font-size:13px;'>💦 Lavando ({len(lavando)})</div>", unsafe_allow_html=True)
                for a in lavando: render_os_card(a)
            with c_pronto:
                st.markdown(f"<div style='text-align:center; padding:5px; background:rgba(46, 204, 113, 0.15); border-radius:8px; margin-bottom:10px; font-weight:700; color:#27ae60; font-size:13px;'>✨ Prontos ({len(prontos)})</div>", unsafe_allow_html=True)
                for a in prontos: render_os_card(a)
                
        else:
            st.info("Nenhuma OS no pátio.")

    # ==========================================
    # ABA 3: HISTÓRICO CONCLUÍDOS
    # ==========================================
    elif aba_selecionada == lbl_hist:"""

content = patio_block_pattern.sub(new_patio_block, content)

# 4. Agendar action sets to "Aguardando" if not using "Em Andamento" anymore
# Wait, for Agenda `Iniciar OS` button, we should set it to `Aguardando` too, to put it in the queue.
agenda_old = """                    if op_ag == "Iniciar OS":
                        at.status = "Em Andamento"
                        at.data_agendamento = None"""
agenda_new = """                    if op_ag == "Iniciar OS":
                        at.status = "Aguardando"
                        at.data_agendamento = None"""
content = content.replace(agenda_old, agenda_new)

with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated Pátio to Dynamic Status 1-Click')
