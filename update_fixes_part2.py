import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Restore @dialog_decorator for dialog_editar_os
if 'def dialog_editar_os(at_id):' in content and '@dialog_decorator' not in content.split('def dialog_editar_os(at_id):')[0].split('\n')[-2]:
    content = content.replace('def dialog_editar_os(at_id):', '@dialog_decorator("Editar OS")\ndef dialog_editar_os(at_id):')

# 2. Modify "Falta R$ xxx" to include patio values
# We first need to calculate valor_patio
calc_patio_logic = """    em_andamento = db.query(Atendimento).filter(Atendimento.status == "Em Andamento").order_by(Atendimento.id.asc()).all()
    qtd_andamento = len(em_andamento)
    valor_patio = sum(a.valor_total for a in em_andamento) if em_andamento else 0.0
"""
content = content.replace('    em_andamento = db.query(Atendimento).filter(Atendimento.status == "Em Andamento").order_by(Atendimento.id.asc()).all()\n    qtd_andamento = len(em_andamento)', calc_patio_logic)

# Replace txt_dia
old_txt_dia = """        if diff_dia >= 0:
            txt_dia = f"Excedente: R$ {formatar_moeda(diff_dia)}"
            cor_dia = "#2ecc71"
        else:
            txt_dia = f"Falta: R$ {formatar_moeda(abs(diff_dia))}"
            cor_dia = "#e74c3c"
            
        if diff_semana >= 0:
            txt_sem = f"Excedente: R$ {formatar_moeda(diff_semana)}"
            cor_sem = "#2ecc71"
        else:
            txt_sem = f"Falta: R$ {formatar_moeda(abs(diff_semana))}"
            cor_sem = "#e74c3c" """

new_txt_dia = """        if diff_dia >= 0:
            txt_dia = f"Excedente: R$ {formatar_moeda(diff_dia)}"
            cor_dia = "#2ecc71"
        else:
            txt_dia = f"Falta: R$ {formatar_moeda(abs(diff_dia))}"
            if valor_patio > 0:
                txt_dia += f" <span style='font-size:9px; color:#555;'> (+ R$ {formatar_moeda(valor_patio)} pátio)</span>"
            cor_dia = "#e74c3c"
            
        if diff_semana >= 0:
            txt_sem = f"Excedente: R$ {formatar_moeda(diff_semana)}"
            cor_sem = "#2ecc71"
        else:
            txt_sem = f"Falta: R$ {formatar_moeda(abs(diff_semana))}"
            if valor_patio > 0:
                txt_sem += f" <span style='font-size:9px; color:#555;'> (+ R$ {formatar_moeda(valor_patio)} pátio)</span>"
            cor_sem = "#e74c3c" """

content = content.replace(old_txt_dia, new_txt_dia)

with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Applied edit modal and patio stats fixes')
