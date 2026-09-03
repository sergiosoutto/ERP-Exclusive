import re

with open('db_config.py', 'r', encoding='utf-8') as f:
    content = f.read()

if "hora_prevista_saida = Column(String" not in content:
    content = content.replace(
        'data_pronto = Column(String)',
        'data_pronto = Column(String)\n    hora_prevista_saida = Column(String)'
    )

mig_hps = '        db.execute(text("ALTER TABLE atendimentos ADD COLUMN hora_prevista_saida VARCHAR;"))'

if "hora_prevista_saida VARCHAR;" not in content:
    old_mig = '        db.execute(text("ALTER TABLE atendimentos ADD COLUMN data_pronto VARCHAR;"))'
    new_mig = f"""{old_mig}
    except:
        db.rollback()
    try:
{mig_hps}"""
    content = content.replace(old_mig, new_mig)

with open('db_config.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated db_config.py with hora_prevista_saida')
