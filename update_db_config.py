import re

with open('db_config.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add LogAuditoria
log_model = """
class LogAuditoria(Base):
    __tablename__ = "log_auditoria"
    id = Column(Integer, primary_key=True, index=True)
    data_hora = Column(String)
    usuario = Column(String)
    acao = Column(String)
    detalhes = Column(String)
"""
if "class LogAuditoria" not in content:
    content = content.replace("class Adiantamento(Base):", log_model + "\nclass Adiantamento(Base):")

# Add pode_excluir to Usuario
if "pode_excluir = Column" not in content:
    content = content.replace('permissoes = Column(String, default="todas")', 'permissoes = Column(String, default="todas")\n    pode_excluir = Column(Boolean, default=False)')

# Add ALTER TABLE to init_db
alter_pode_excluir = """
    # Migrations
    try:
        db.execute(text("ALTER TABLE usuarios ADD COLUMN pode_excluir BOOLEAN DEFAULT FALSE;"))
        db.commit()
    except Exception:
        db.rollback()
"""
if "ALTER TABLE usuarios ADD COLUMN pode_excluir" not in content:
    content = content.replace("def seed_db():", alter_pode_excluir + "\ndef seed_db():")

# We also need to import text if it's not imported
if "from sqlalchemy import text" not in content:
    content = content.replace("from sqlalchemy import create_engine", "from sqlalchemy import create_engine, text")
    
# Finally add a helper function to register logs
log_helper = """
def registrar_log(acao, detalhes=""):
    import streamlit as st
    from datetime import datetime, timedelta, timezone
    
    usuario = "Sistema"
    if 'username' in st.session_state:
        usuario = st.session_state['username']
        
    fuso_brasil = timezone(timedelta(hours=-3))
    agora = datetime.now(fuso_brasil).replace(tzinfo=None).isoformat()
    
    db = SessionLocal()
    try:
        log = LogAuditoria(data_hora=agora, usuario=usuario, acao=acao, detalhes=detalhes)
        db.add(log)
        db.commit()
    except Exception as e:
        print("Erro ao registrar log:", e)
    finally:
        db.close()
"""
if "def registrar_log" not in content:
    content += "\n" + log_helper

with open('db_config.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated db_config.py")
