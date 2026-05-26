import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

# Configuramos o SQLite para desenvolvimento local, com fácil transição para PostgreSQL via Supabase
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///data/erp.db")

# Conexão com o banco de dados
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# Exemplo de Modelos Base (Hardcoded Rules)
# ==========================================

class ContaBancaria(Base):
    __tablename__ = "contas_bancarias"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True) # "Banco 1 (B2B)", "Banco 2 (Varejo B2C)", "Banco 3 (Reserva PIX)"
    saldo_atual = Column(Float, default=0.0)

class Produto(Base):
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    unidade_medida = Column(String) # ml, g, un
    quantidade_estoque = Column(Float, default=0.0)
    preco_venda = Column(Float, default=0.0)
    produto_monofasico = Column(Boolean, default=False) # Para dedução futura de PIS/COFINS

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True) # Ex: CLI-0001
    nome = Column(String, index=True)
    telefone = Column(String)
    placa_veiculo = Column(String)
    modelo_veiculo = Column(String) # Ex: Corolla, Onix

class Servico(Base):
    __tablename__ = "servicos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    preco_padrao = Column(Float, default=0.0)

class Atendimento(Base):
    __tablename__ = "atendimentos"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True) # Ex: OS-0001
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    status = Column(String, default="Em andamento") # "Em andamento", "Finalizado", "Cancelado"
    desconto_total = Column(Float, default=0.0)
    valor_total = Column(Float, default=0.0)
    forma_pagamento = Column(String) # Débito, Crédito, Pix, Dinheiro
    data_criacao = Column(String)
    data_conclusao = Column(String)

class ItemAtendimento(Base):
    __tablename__ = "itens_atendimento"
    id = Column(Integer, primary_key=True, index=True)
    atendimento_id = Column(Integer, ForeignKey("atendimentos.id"))
    tipo = Column(String) # "Serviço" ou "Produto"
    referencia_id = Column(Integer) # ID do Servico ou ID do Produto
    valor_cobrado = Column(Float, default=0.0)


def init_db():
    """Cria as tabelas no banco de dados, se não existirem."""
    if not os.path.exists("data"):
        os.makedirs("data")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    from sqlalchemy import text
    
    # 1. Migração para a coluna 'codigo' em 'clientes'
    try:
        db.execute(text("SELECT codigo FROM clientes LIMIT 1"))
    except Exception:
        try:
            db.rollback()
            db.execute(text("ALTER TABLE clientes ADD COLUMN codigo VARCHAR"))
            db.commit()
            
            # Atualiza clientes existentes sem código
            clientes_sem_codigo = db.query(Cliente).filter(Cliente.codigo == None).all()
            for i, c in enumerate(clientes_sem_codigo):
                c.codigo = f"CLI-{i+1:04d}"
            db.commit()
        except Exception as e:
            print("Erro ao migrar clientes:", e)
            db.rollback()

    # 2. Migração para a coluna 'codigo' em 'atendimentos'
    try:
        db.execute(text("SELECT codigo FROM atendimentos LIMIT 1"))
    except Exception:
        try:
            db.rollback()
            db.execute(text("ALTER TABLE atendimentos ADD COLUMN codigo VARCHAR"))
            db.commit()
            
            # Atualiza atendimentos existentes sem código
            atendimentos_sem_codigo = db.query(Atendimento).filter(Atendimento.codigo == None).all()
            for i, at in enumerate(atendimentos_sem_codigo):
                at.codigo = f"OS-{i+1:04d}"
            db.commit()
        except Exception as e:
            print("Erro ao migrar código de atendimentos:", e)
            db.rollback()

    # 3. Migração para a coluna 'forma_pagamento' em 'atendimentos'
    try:
        db.execute(text("SELECT forma_pagamento FROM atendimentos LIMIT 1"))
    except Exception:
        try:
            db.rollback()
            db.execute(text("ALTER TABLE atendimentos ADD COLUMN forma_pagamento VARCHAR"))
            db.commit()
        except Exception as e:
            print("Erro ao migrar forma_pagamento de atendimentos:", e)
            db.rollback()

    # 4. Migração para a coluna 'modelo_veiculo' em 'clientes'
    try:
        db.execute(text("SELECT modelo_veiculo FROM clientes LIMIT 1"))
    except Exception:
        try:
            db.rollback()
            db.execute(text("ALTER TABLE clientes ADD COLUMN modelo_veiculo VARCHAR"))
            db.commit()
        except Exception as e:
            print("Erro ao migrar modelo_veiculo de clientes:", e)
            db.rollback()

    # 5. Migração para a coluna 'data_conclusao' em 'atendimentos'
    try:
        db.execute(text("SELECT data_conclusao FROM atendimentos LIMIT 1"))
    except Exception:
        try:
            db.rollback()
            db.execute(text("ALTER TABLE atendimentos ADD COLUMN data_conclusao VARCHAR"))
            db.commit()
        except Exception as e:
            print("Erro ao migrar data_conclusao de atendimentos:", e)
            db.rollback()

    db.close()
    seed_db()

def seed_db():
    db = SessionLocal()
    # Verificar se já existem serviços
    if db.query(Servico).first() is None:
        # Criar Serviços Iniciais
        servicos = [
            Servico(nome="Lavagem Americana", preco_padrao=80.0),
            Servico(nome="Lavagem Detalhada", preco_padrao=150.0),
            Servico(nome="Polimento Comercial", preco_padrao=400.0),
            Servico(nome="Vitrificação", preco_padrao=1200.0),
            Servico(nome="Higienização Interna", preco_padrao=250.0)
        ]
        db.add_all(servicos)
        
        # Criar Produtos Iniciais
        produtos = [
            Produto(nome="Vonixx V-Floc", unidade_medida="ml", quantidade_estoque=1500, preco_venda=45.0, produto_monofasico=True),
            Produto(nome="Cera de Carnaúba", unidade_medida="g", quantidade_estoque=500, preco_venda=120.0, produto_monofasico=False)
        ]
        db.add_all(produtos)

        # Criar Contas Bancárias
        contas = [
            ContaBancaria(nome="Banco 1 (B2B)", saldo_atual=0.0),
            ContaBancaria(nome="Banco 2 (Varejo B2C)", saldo_atual=0.0),
            ContaBancaria(nome="Banco 3 (Reserva PIX)", saldo_atual=0.0)
        ]
        db.add_all(contas)

        # Criar Clientes Fictícios
        clientes = [
            Cliente(codigo="CLI-0001", nome="João Silva", telefone="(11) 99999-1111", placa_veiculo="ABC-1234", modelo_veiculo="Fiat Uno"),
            Cliente(codigo="CLI-0002", nome="Maria Oliveira", telefone="(11) 98888-2222", placa_veiculo="XYZ-9876", modelo_veiculo="Chevrolet Onix"),
            Cliente(codigo="CLI-0003", nome="Carlos Souza", telefone="(11) 97777-3333", placa_veiculo="FGH-5678", modelo_veiculo="Honda Civic")
        ]
        db.add_all(clientes)
        db.commit()

        # Criar 11 atendimentos finalizados para Carlos Souza (CLI-0003) para testar "Diamante"
        carlos = db.query(Cliente).filter(Cliente.codigo == "CLI-0003").first()
        if carlos:
            for i in range(11):
                at = Atendimento(
                    codigo=f"OS-D{i+1:02d}",
                    cliente_id=carlos.id,
                    status="Finalizado",
                    desconto_total=0.0,
                    valor_total=80.0,
                    forma_pagamento="Pix",
                    data_criacao=datetime.now().isoformat()
                )
                db.add(at)
            db.commit()
    db.close()

def get_db():
    """Gera uma sessão do banco de dados para ser utilizada nas operações."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
