import re

with open('db_config.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add columns to Atendimento
if "data_inicio = Column" not in content:
    content = content.replace('data_agendamento = Column(String)', 'data_agendamento = Column(String)\n    data_inicio = Column(String)\n    data_pronto = Column(String)')

# Add migrations
mig_inicio = '        db.execute(text("ALTER TABLE atendimentos ADD COLUMN data_inicio VARCHAR;"))'
mig_pronto = '        db.execute(text("ALTER TABLE atendimentos ADD COLUMN data_pronto VARCHAR;"))'

if "data_inicio VARCHAR;" not in content:
    old_mig = '        db.execute(text("ALTER TABLE atendimentos ADD COLUMN data_agendamento VARCHAR;"))'
    new_mig = f"""{old_mig}
    except:
        db.rollback()
    try:
{mig_inicio}
    except:
        db.rollback()
    try:
{mig_pronto}"""
    content = content.replace(old_mig, new_mig)

with open('db_config.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated db_config.py with new columns')
