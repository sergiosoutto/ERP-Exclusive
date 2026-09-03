import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add dialogs for Iniciar and Pronto
dialogs = """
@dialog_decorator("Iniciar Serviço")
def dialog_iniciar_lavagem(at_id):
    db = next(get_db())
    at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
    if not at: return
    
    st.write(f"Iniciando: **{at.codigo}**")
    
    import datetime
    agora = obter_hora_local()
    dt_atual = st.date_input("Data de Início", value=agora.date())
    hr_atual = st.time_input("Hora de Início", value=agora.time())
    
    if st.button("Confirmar Início", type="primary", use_container_width=True):
        at.status = "Lavando"
        dt_final = datetime.datetime.combine(dt_atual, hr_atual).astimezone(timezone(timedelta(hours=-3))).isoformat()
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
    
    import datetime
    agora = obter_hora_local()
    dt_atual = st.date_input("Data de Conclusão", value=agora.date())
    hr_atual = st.time_input("Hora de Conclusão", value=agora.time())
    
    if st.button("Confirmar Conclusão", type="primary", use_container_width=True):
        at.status = "Pronto"
        dt_final = datetime.datetime.combine(dt_atual, hr_atual).astimezone(timezone(timedelta(hours=-3))).isoformat()
        at.data_pronto = dt_final
        registrar_log(f"Marcou OS como pronta: {at.codigo}")
        db.commit()
        st.session_state['success_msg'] = f"OS {at.codigo} concluída!"
        st.rerun()

def render_fast_launch():
"""
content = content.replace("def render_fast_launch():", dialogs)

# 2. Update render_os_card to use dialogs
old_buttons = """                    # Aes Dinmicas por Status
                    if at.status in ("Aguardando", "Em Andamento"):
                        if st.button(f" Iniciar Lavagem", key=f"btn_ini_{at.id}", type="primary", use_container_width=True):
                            at.status = "Lavando"
                            at.data_inicio = obter_hora_local().isoformat()
                            db.commit()
                            st.toast(f"OS {at.codigo} em execuo!")
                            st.rerun()
                    elif at.status == "Lavando":
                        if st.button(f" Sinalizar Pronto", key=f"btn_pro_{at.id}", type="primary", use_container_width=True):
                            at.status = "Pronto"
                            at.data_pronto = obter_hora_local().isoformat()
                            db.commit()
                            st.toast(f"OS {at.codigo} concluda! Aguardando entrega.")
                            st.rerun()"""

old_buttons_regex = r'# Ações Dinâmicas por Status.*?st\.rerun\(\)'
# I'll use simple string replace carefully
# First, let's normalize encoding by printing the actual block or just write a regex
import re
new_buttons = """                    # Ações Dinâmicas por Status
                    if at.status in ("Aguardando", "Em Andamento"):
                        if st.button(f" Iniciar Lavagem", key=f"btn_ini_{at.id}", type="primary", use_container_width=True):
                            dialog_iniciar_lavagem(at.id)
                    elif at.status == "Lavando":
                        if st.button(f" Sinalizar Pronto", key=f"btn_pro_{at.id}", type="primary", use_container_width=True):
                            dialog_sinalizar_pronto(at.id)"""

content = re.sub(r'# A.*?es Din.*?micas por Status.*?elif at.status == "Pronto":', new_buttons + '\n                    elif at.status == "Pronto":', content, flags=re.DOTALL)


with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated fast_launch with modal dialogs")
