import re

with open('db_config.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add column to model
if "data_agendamento = Column" not in content:
    content = content.replace('parcelas = Column(Integer, default=1)', 'parcelas = Column(Integer, default=1)\n    data_agendamento = Column(String)')

# Add migration
mig = """
    # Migrations for existing DB
    try:
        db.execute(text("ALTER TABLE atendimentos ADD COLUMN data_agendamento VARCHAR;"))
        db.commit()
    except Exception:
        db.rollback()
"""
if "ALTER TABLE atendimentos ADD COLUMN data_agendamento" not in content:
    content = content.replace('try:\n        db.execute(text("ALTER TABLE usuarios ADD COLUMN pode_excluir BOOLEAN DEFAULT FALSE;"))', 'try:\n        db.execute(text("ALTER TABLE usuarios ADD COLUMN pode_excluir BOOLEAN DEFAULT FALSE;"))\n        db.commit()\n    except:\n        db.rollback()\n    try:\n        db.execute(text("ALTER TABLE atendimentos ADD COLUMN data_agendamento VARCHAR;"))')

with open('db_config.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Added data_agendamento to db_config.py')
