import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add dialogs for Iniciar and Pronto before render_fast_launch
dialogs = """
@dialog_decorator("Iniciar Serviço")
def dialog_iniciar_lavagem(at_id):
    db = next(get_db())
    at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
    if not at: return
    
    st.write(f"Iniciando: **{at.codigo}**")
    
    agora = obter_hora_local()
    dt_atual = st.date_input("Data de Início", value=agora.date())
    hr_atual = st.time_input("Hora de Início", value=agora.time())
    
    if st.button("Confirmar Início", type="primary", use_container_width=True):
        at.status = "Lavando"
        dt_final = datetime.combine(dt_atual, hr_atual).astimezone(timezone(timedelta(hours=-3))).isoformat()
        at.data_inicio = dt_final
        registrar_log(f"Iniciou a OS: {at.codigo}")
        db.commit()
        st.session_state['success_msg'] = f"OS {at.codigo} em execução!"
        st.rerun()

@dialog_decorator("Sinalizar Pronto")
def dialog_sinalizar_pronto(at_id):
    db = next(get_db())
    at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
    if not at: return
    
    st.write(f"Concluindo etapa: **{at.codigo}**")
    
    agora = obter_hora_local()
    dt_atual = st.date_input("Data de Conclusão", value=agora.date())
    hr_atual = st.time_input("Hora de Conclusão", value=agora.time())
    
    if st.button("Confirmar Conclusão", type="primary", use_container_width=True):
        at.status = "Pronto"
        dt_final = datetime.combine(dt_atual, hr_atual).astimezone(timezone(timedelta(hours=-3))).isoformat()
        at.data_pronto = dt_final
        registrar_log(f"Marcou OS como pronta: {at.codigo}")
        db.commit()
        st.session_state['success_msg'] = f"OS {at.codigo} concluída!"
        st.rerun()

def render_fast_launch():
"""
content = content.replace("def render_fast_launch():", dialogs)

with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added dialogs")
