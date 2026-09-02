import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the card render logic
old_card_logic = """                with st.container(border=True):
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.markdown(f"<p style='margin:0; font-size:14px; font-weight:700; color:var(--text-main);'>{cli.nome if cli else 'Desconhecido'} <span style='font-size:11px; font-weight:normal; color:#888;'>({at.codigo})</span></p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='margin:0; font-size:11px; color:#555;'>*{carro_info} | {placa_info}*</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='margin:2px 0 0 0; font-size:11px;'>Entrada: <b>{dt_str}</b></p>", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"<div style='text-align:right;'><span style='font-size:10px; background:#f0f0f0; padding:2px 6px; border-radius:10px;'>{len(servs)} itens</span><br><span style='font-size:15px; font-weight:800; color:var(--accent);'>R$ {formatar_moeda(total_val)}</span></div>", unsafe_allow_html=True)
                    
                    st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)"""

new_card_logic = """                with st.container(border=True):
                    st.markdown(f"<p style='margin:0; font-size:14px; font-weight:600;'>{cli.nome if cli else 'Desconhecido'} <span style='font-size:10px; font-weight:normal; color:var(--text-sec);'>({at.codigo})</span></p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:0; font-size:12px; color:var(--text-sec);'>*{carro_info} | Placa: {placa_info}*</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:2px 0 6px 0; font-size:12px;'>{gold_icon('clock')} {dt_str} &nbsp;|&nbsp; <b>R$ {formatar_moeda(total_val)}</b></p>", unsafe_allow_html=True)"""
content = content.replace(old_card_logic, new_card_logic)

# Replace the layout
old_layout = """            c_fila, c_lav, c_pronto = st.columns(3)
            with c_fila:
                st.markdown(f"<div style='text-align:center; padding:5px; background:rgba(0,0,0,0.05); border-radius:8px; margin-bottom:10px; font-weight:700; font-size:13px;'>🚗 Fila ({len(fila)})</div>", unsafe_allow_html=True)
                for a in fila: render_os_card(a)
            with c_lav:
                st.markdown(f"<div style='text-align:center; padding:5px; background:rgba(197, 160, 89, 0.15); border-radius:8px; margin-bottom:10px; font-weight:700; color:var(--accent); font-size:13px;'>💦 Lavando ({len(lavando)})</div>", unsafe_allow_html=True)
                for a in lavando: render_os_card(a)
            with c_pronto:
                st.markdown(f"<div style='text-align:center; padding:5px; background:rgba(46, 204, 113, 0.15); border-radius:8px; margin-bottom:10px; font-weight:700; color:#27ae60; font-size:13px;'>✨ Prontos ({len(prontos)})</div>", unsafe_allow_html=True)
                for a in prontos: render_os_card(a)"""

new_layout = """            # Layout em abas (Pills) para não amassar os cards
            lbl_f = f"🚗 Fila ({len(fila)})"
            lbl_l = f"💦 Lavando ({len(lavando)})"
            lbl_p = f"✨ Prontos ({len(prontos)})"
            
            aba_fase = st.pills("Fase do Pátio", [lbl_f, lbl_l, lbl_p], default=lbl_f, label_visibility="collapsed")
            
            if aba_fase == lbl_f:
                for a in fila: render_os_card(a)
                if not fila: st.info("Nenhum carro na fila.")
            elif aba_fase == lbl_l:
                for a in lavando: render_os_card(a)
                if not lavando: st.info("Nenhum carro sendo lavado.")
            elif aba_fase == lbl_p:
                for a in prontos: render_os_card(a)
                if not prontos: st.info("Nenhum carro pronto aguardando entrega.")"""
content = content.replace(old_layout, new_layout)

with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated patio layout to avoid squishing')
