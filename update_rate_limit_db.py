import re

with open('db_config.py', 'r', encoding='utf-8') as f:
    content = f.read()

if "tentativas_falhas = Column(Integer" not in content:
    content = content.replace(
        'pode_excluir = Column(Boolean, default=False)',
        'pode_excluir = Column(Boolean, default=False)\n    tentativas_falhas = Column(Integer, default=0)\n    bloqueado_ate = Column(String)'
    )

mig_tf = '        db.execute(text("ALTER TABLE usuarios ADD COLUMN tentativas_falhas INTEGER DEFAULT 0;"))'
mig_ba = '        db.execute(text("ALTER TABLE usuarios ADD COLUMN bloqueado_ate VARCHAR;"))'

if "tentativas_falhas INTEGER" not in content:
    old_mig = '        db.execute(text("ALTER TABLE usuarios ADD COLUMN pode_excluir BOOLEAN DEFAULT FALSE;"))'
    new_mig = f"""{old_mig}
    except:
        db.rollback()
    try:
{mig_tf}
    except:
        db.rollback()
    try:
{mig_ba}"""
    content = content.replace(old_mig, new_mig)

with open('db_config.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated db_config.py with Rate Limit columns')
