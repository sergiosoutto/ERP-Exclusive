import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add hora_prevista to the Novo OS form
old_form = """            st.markdown("<br>", unsafe_allow_html=True)
            

            c_ag1, c_ag2, c_ag3 = st.columns([1, 1.5, 1.5])"""

new_form = """            st.markdown("<br>", unsafe_allow_html=True)
            hora_prevista = st.text_input("Previsão de Saída (Ex: Imediato, 17:30, Fim da Tarde)", value="Imediato")
            st.markdown("<br>", unsafe_allow_html=True)

            c_ag1, c_ag2, c_ag3 = st.columns([1, 1.5, 1.5])"""
content = content.replace(old_form, new_form)

# And add to object creation
old_create = """                    novo_at = Atendimento(
                        codigo=codigo_seq, cliente_id=cliente_ref.id, status=stts,
                        valor_total=total_atendimento, data_criacao=obter_hora_local().isoformat(),
                        data_agendamento=dt_agend
                    )"""
                    
new_create = """                    novo_at = Atendimento(
                        codigo=codigo_seq, cliente_id=cliente_ref.id, status=stts,
                        valor_total=total_atendimento, data_criacao=obter_hora_local().isoformat(),
                        data_agendamento=dt_agend, hora_prevista_saida=hora_prevista
                    )"""
content = content.replace(old_create, new_create)

# 2. Add hora_prevista to the OS Card in Patio
old_card = """                <span style='font-size:11px; color:#555;'>{gold_icon('person')} {cli.telefone if cli else 'N/A'}</span><br>
                <div style='margin-top:8px;'>
                    <span style='font-size:16px; font-weight:700; color:var(--text-main);'>R$ {at.valor_total:.2f}</span>
                </div>
            </div>"""

new_card = """                <span style='font-size:11px; color:#555;'>{gold_icon('person')} {cli.telefone if cli else 'N/A'}</span><br>
                <span style='font-size:11px; font-weight:600; color:var(--accent);'>⏱ Prev. Saída: {getattr(at, "hora_prevista_saida", "Imediato") or "Imediato"}</span><br>
                <div style='margin-top:8px;'>
                    <span style='font-size:16px; font-weight:700; color:var(--text-main);'>R$ {at.valor_total:.2f}</span>
                </div>
            </div>"""
content = content.replace(old_card, new_card)

with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added hora_prevista_saida")
