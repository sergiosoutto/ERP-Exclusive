import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add Reagendar to options
old_opts = 'options = ["Iniciar OS", "Excluir"] if st.session_state.get("pode_excluir", False) else ["Iniciar OS"]'
new_opts = 'options = ["Iniciar OS", "Reagendar", "Excluir"] if st.session_state.get("pode_excluir", False) else ["Iniciar OS", "Reagendar"]'

content = content.replace(old_opts, new_opts)

# Add logic for Reagendar using st.date_input right on the spot (since we can't easily open a modal without dialog)
# Oh wait, we can just use @dialog_decorator for Reagendar, just like dialog_editar_os!
reagendar_dialog = """
@dialog_decorator("Reagendar Serviço")
def dialog_reagendar(at_id):
    db = next(get_db())
    at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
    
    if not at: return
    
    dt_atual = None
    if at.data_agendamento:
        try:
            dt_atual = datetime.fromisoformat(at.data_agendamento).date()
        except: pass
        
    nova_data = st.date_input("Nova Data", value=dt_atual)
    
    if st.button("Confirmar Reagendamento", type="primary", use_container_width=True):
        at.data_agendamento = nova_data.isoformat()
        db.commit()
        st.session_state['success_msg'] = "OS reagendada com sucesso!"
        st.rerun()
"""

# Put it before dialog_editar_os
if 'def dialog_reagendar' not in content:
    content = content.replace('def dialog_editar_os(at_id):', reagendar_dialog + '\ndef dialog_editar_os(at_id):')

# Handle the click
handling_old = """                    if op_ag == "Iniciar OS":
                        at.status = "Em Andamento"
                        at.data_agendamento = None
                        at.data_criacao = obter_hora_local().isoformat()
                        db.commit()
                        st.rerun()
                    elif op_ag == "Excluir":"""

handling_new = """                    if op_ag == "Iniciar OS":
                        at.status = "Em Andamento"
                        at.data_agendamento = None
                        at.data_criacao = obter_hora_local().isoformat()
                        db.commit()
                        st.rerun()
                    elif op_ag == "Reagendar":
                        dialog_reagendar(at.id)
                    elif op_ag == "Excluir":"""

if 'elif op_ag == "Reagendar":' not in content:
    content = content.replace(handling_old, handling_new)

with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Added Reagendar to Agenda')
