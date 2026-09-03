import re

with open('db_config.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Model Atendimento
old_model = """    parcelas = Column(Integer, default=1)
    data_agendamento = Column(String)"""
new_model = """    parcelas = Column(Integer, default=1)
    data_agendamento = Column(String)
    data_inicio = Column(String)
    data_pronto = Column(String)
    hora_prevista_saida = Column(String)"""

if "hora_prevista_saida = Column" not in content:
    content = content.replace(old_model, new_model)

# 2. Add Migrations to init_db
old_mig = '        db.execute(text("ALTER TABLE usuarios ADD COLUMN bloqueado_ate VARCHAR;"))'

mig_di = '        db.execute(text("ALTER TABLE atendimentos ADD COLUMN data_inicio VARCHAR;"))'
mig_dp = '        db.execute(text("ALTER TABLE atendimentos ADD COLUMN data_pronto VARCHAR;"))'
mig_hps = '        db.execute(text("ALTER TABLE atendimentos ADD COLUMN hora_prevista_saida VARCHAR;"))'

new_mig = f"""{old_mig}
    except:
        db.rollback()
    try:
{mig_di}
    except:
        db.rollback()
    try:
{mig_dp}
    except:
        db.rollback()
    try:
{mig_hps}"""

if "data_inicio VARCHAR;" not in content:
    content = content.replace(old_mig, new_mig)

with open('db_config.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated db_config.py with missing columns")
