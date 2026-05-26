import os
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
            Cliente(codigo="CLI-0001", nome="João Silva", telefone="(11) 99999-1111", placa_veiculo="ABC-1234"),
            Cliente(codigo="CLI-0002", nome="Maria Oliveira", telefone="(11) 98888-2222", placa_veiculo="XYZ-9876")
        ]
        db.add_all(clientes)

        db.commit()
    db.close()

def get_db():
    """Gera uma sessão do banco de dados para ser utilizada nas operações."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
