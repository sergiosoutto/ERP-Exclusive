import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_lazy = """    active_client_ids = set([a.cliente_id for a in em_andamento] + [a.cliente_id for a in concluidos_hoje])
    if aba_selecionada == lbl_agenda:
        agendados_raw = db.query(Atendimento).filter(Atendimento.status == "Agendado").order_by(Atendimento.data_agendamento.asc()).all()
        active_client_ids.update([a.cliente_id for a in agendados_raw])"""
        
new_lazy = """    active_client_ids = set([a.cliente_id for a in em_andamento] + [a.cliente_id for a in concluidos_hoje])
    agendados_raw = []
    if aba_selecionada == lbl_agenda:
        agendados_raw = db.query(Atendimento).filter(Atendimento.status == "Agendado").order_by(Atendimento.data_agendamento.asc()).all()
        active_client_ids.update([a.cliente_id for a in agendados_raw])"""

content = content.replace(old_lazy, new_lazy)

with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Definitively fixed agendados_raw")
