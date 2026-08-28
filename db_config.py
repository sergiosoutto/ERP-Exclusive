import os
import hashlib
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

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="admin") # admin, basico
    permissoes = Column(String, default="todas")

class FormaPagamento(Base):
    __tablename__ = "formas_pagamento"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)
    taxa_juros_vista = Column(Float, default=0.0)
    taxa_juros_parcela = Column(Float, default=0.0)

class ContaBancaria(Base):
    __tablename__ = "contas_bancarias"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True) 
    saldo_atual = Column(Float, default=0.0)

class CategoriaFinanceira(Base):
    __tablename__ = "categorias_financeiras"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)
    tipo = Column(String) # "Receita" ou "Despesa"
    banco_padrao_id = Column(Integer, ForeignKey("contas_bancarias.id"), nullable=True)

class SubcategoriaFinanceira(Base):
    __tablename__ = "subcategorias_financeiras"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    categoria_id = Column(Integer, ForeignKey("categorias_financeiras.id"))
    banco_padrao_id = Column(Integer, ForeignKey("contas_bancarias.id"), nullable=True)

class LancamentoFinanceiro(Base):
    __tablename__ = "lancamentos_financeiros"
    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String)
    tipo = Column(String) # "Receita" ou "Despesa"
    valor = Column(Float, default=0.0) # Valor Real
    valor_previsto = Column(Float, default=0.0) # Valor Previsto
    data_vencimento = Column(String) 
    data_pagamento = Column(String) 
    status = Column(String, default="Pendente") # "Pendente" ou "Pago"
    recorrencia = Column(String, default="Único") # "Único", "Parcelado", "Fixo"
    categoria_id = Column(Integer, ForeignKey("categorias_financeiras.id"))
    subcategoria_id = Column(Integer, ForeignKey("subcategorias_financeiras.id"), nullable=True)
    conta_id = Column(Integer, ForeignKey("contas_bancarias.id"))
    atendimento_id = Column(Integer, ForeignKey("atendimentos.id"), nullable=True)

class OrcamentoMeta(Base):
    __tablename__ = "orcamentos_metas"
    id = Column(Integer, primary_key=True, index=True)
    mes_ano = Column(String) # "08/2026"
    categoria_id = Column(Integer, ForeignKey("categorias_financeiras.id"))
    valor_previsto = Column(Float, default=0.0)

class Produto(Base):
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    unidade_medida = Column(String) # ml, g, un
    quantidade_estoque = Column(Float, default=0.0)
    preco_venda = Column(Float, default=0.0) # Legacy
    custo_unidade = Column(Float, default=0.0) 
    produto_monofasico = Column(Boolean, default=False) 

class ServicoInsumo(Base):
    __tablename__ = "servicos_insumos"
    id = Column(Integer, primary_key=True, index=True)
    servico_id = Column(Integer, ForeignKey("servicos.id"))
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    quantidade_utilizada = Column(Float, default=0.0)

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True) 
    nome = Column(String, index=True)
    telefone = Column(String)
    placa_veiculo = Column(String)
    modelo_veiculo = Column(String) 

class Servico(Base):
    __tablename__ = "servicos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    preco_padrao = Column(Float, default=0.0)
    custo_agua = Column(Float, default=0.0)
    custo_luz = Column(Float, default=0.0)
    custo_fixo = Column(Float, default=0.0)
    custo_total = Column(Float, default=0.0)
    margem_lucro = Column(Float, default=0.0)

class Atendimento(Base):
    __tablename__ = "atendimentos"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True) 
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    status = Column(String, default="Em andamento") 
    desconto_total = Column(Float, default=0.0)
    valor_total = Column(Float, default=0.0)
    forma_pagamento = Column(String) 
    data_criacao = Column(String)
    data_conclusao = Column(String)
    observacoes = Column(String)
    parcelas = Column(Integer, default=1)

class ItemAtendimento(Base):
    __tablename__ = "itens_atendimento"
    id = Column(Integer, primary_key=True, index=True)
    atendimento_id = Column(Integer, ForeignKey("atendimentos.id"))
    tipo = Column(String) # "Serviço"
    referencia_id = Column(Integer) 
    valor_cobrado = Column(Float, default=0.0)

class Colaborador(Base):
    __tablename__ = "colaboradores"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    cargo = Column(String)
    telefone = Column(String)
    ativo = Column(Boolean, default=True)

class MetaApp(Base):
    __tablename__ = "metas_app"
    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String)
    valor = Column(Float, default=0.0)
    data_inicial = Column(Date)
    data_final = Column(Date)
    peso_seg = Column(Float, default=16.66)
    peso_ter = Column(Float, default=16.66)
    peso_qua = Column(Float, default=16.66)
    peso_qui = Column(Float, default=16.66)
    peso_sex = Column(Float, default=16.66)
    peso_sab = Column(Float, default=16.70)

def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")
    Base.metadata.create_all(bind=engine)
    
    # Auto-migration for weight columns
    with engine.connect() as conn:
        from sqlalchemy import text
        try: conn.execute(text("ALTER TABLE metas_app ADD COLUMN peso_seg FLOAT DEFAULT 16.66"))
        except: pass
        try: conn.execute(text("ALTER TABLE metas_app ADD COLUMN peso_ter FLOAT DEFAULT 16.66"))
        except: pass
        try: conn.execute(text("ALTER TABLE metas_app ADD COLUMN peso_qua FLOAT DEFAULT 16.66"))
        except: pass
        try: conn.execute(text("ALTER TABLE metas_app ADD COLUMN peso_qui FLOAT DEFAULT 16.66"))
        except: pass
        try: conn.execute(text("ALTER TABLE metas_app ADD COLUMN peso_sex FLOAT DEFAULT 16.66"))
        except: pass
        try: conn.execute(text("ALTER TABLE metas_app ADD COLUMN peso_sab FLOAT DEFAULT 16.70"))
        except: pass
        
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
            clientes_sem_codigo = db.query(Cliente).filter(Cliente.codigo == None).all()
            for i, c in enumerate(clientes_sem_codigo):
                c.codigo = f"CLI-{i+1:04d}"
            db.commit()
        except Exception:
            db.rollback()

    # 2. Migração para 'codigo' em 'atendimentos'
    try:
        db.execute(text("SELECT codigo FROM atendimentos LIMIT 1"))
    except Exception:
        try:
            db.rollback()
            db.execute(text("ALTER TABLE atendimentos ADD COLUMN codigo VARCHAR"))
            db.commit()
            atendimentos_sem_codigo = db.query(Atendimento).filter(Atendimento.codigo == None).all()
            for i, at in enumerate(atendimentos_sem_codigo):
                at.codigo = f"OS-{i+1:04d}"
            db.commit()
        except Exception:
            db.rollback()

    # 3. Migração para 'forma_pagamento' em 'atendimentos'
    try:
        db.execute(text("SELECT forma_pagamento FROM atendimentos LIMIT 1"))
    except Exception:
        try:
            db.rollback()
            db.execute(text("ALTER TABLE atendimentos ADD COLUMN forma_pagamento VARCHAR"))
            db.commit()
        except Exception:
            db.rollback()

    # 4. Migração para 'modelo_veiculo' em 'clientes'
    try:
        db.execute(text("SELECT modelo_veiculo FROM clientes LIMIT 1"))
    except Exception:
        try:
            db.rollback()
            db.execute(text("ALTER TABLE clientes ADD COLUMN modelo_veiculo VARCHAR"))
            db.commit()
        except Exception:
            db.rollback()

    # 5. Migração para 'data_conclusao' em 'atendimentos'
    try:
        db.execute(text("SELECT data_conclusao FROM atendimentos LIMIT 1"))
    except Exception:
        try:
            db.rollback()
            db.execute(text("ALTER TABLE atendimentos ADD COLUMN data_conclusao VARCHAR"))
            db.commit()
        except Exception:
            db.rollback()

    # 6. Migração para 'observacoes' em 'atendimentos'
    try:
        db.execute(text("SELECT observacoes FROM atendimentos LIMIT 1"))
    except Exception:
        try:
            db.rollback()
            db.execute(text("ALTER TABLE atendimentos ADD COLUMN observacoes VARCHAR"))
            db.commit()
        except Exception:
            db.rollback()
            
    # 7. Migração para 'subcategoria_id' em 'lancamentos_financeiros'
    try:
        db.execute(text("SELECT subcategoria_id FROM lancamentos_financeiros LIMIT 1"))
    except Exception:
        try:
            db.rollback()
            db.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN subcategoria_id INTEGER"))
            db.commit()
        except Exception:
            db.rollback()

    # 8. Migração para 'banco_padrao_id' em 'categorias_financeiras'
    try:
        db.execute(text("SELECT banco_padrao_id FROM categorias_financeiras LIMIT 1"))
    except Exception:
        try:
            db.rollback()
            db.execute(text("ALTER TABLE categorias_financeiras ADD COLUMN banco_padrao_id INTEGER"))
            db.execute(text("ALTER TABLE subcategorias_financeiras ADD COLUMN banco_padrao_id INTEGER"))
            db.commit()
        except Exception:
            db.rollback()
            
    # 9. Migração Serviços (Novos Custos)
    try:
        db.execute(text("SELECT custo_agua FROM servicos LIMIT 1"))
    except Exception:
        try:
            db.rollback()
            db.execute(text("ALTER TABLE servicos ADD COLUMN custo_agua FLOAT DEFAULT 0.0"))
            db.execute(text("ALTER TABLE servicos ADD COLUMN custo_luz FLOAT DEFAULT 0.0"))
            db.execute(text("ALTER TABLE servicos ADD COLUMN custo_fixo FLOAT DEFAULT 0.0"))
            db.execute(text("ALTER TABLE servicos ADD COLUMN custo_total FLOAT DEFAULT 0.0"))
            db.execute(text("ALTER TABLE servicos ADD COLUMN margem_lucro FLOAT DEFAULT 0.0"))
            db.commit()
        except Exception:
            db.rollback()

    # 10. Migração Produtos (Custo)
    try:
        db.execute(text("SELECT custo_unidade FROM produtos LIMIT 1"))
    except Exception:
        try:
            db.rollback()
            db.execute(text("ALTER TABLE produtos ADD COLUMN custo_unidade FLOAT DEFAULT 0.0"))
            db.execute(text("UPDATE produtos SET custo_unidade = preco_venda"))
            db.commit()
        except Exception:
            db.rollback()
            
    # 11. Migração parcelas Atendimento
    try:
        db.execute(text("SELECT parcelas FROM atendimentos LIMIT 1"))
    except Exception:
        try:
            db.rollback()
            db.execute(text("ALTER TABLE atendimentos ADD COLUMN parcelas INTEGER DEFAULT 1"))
            db.commit()
        except Exception:
            db.rollback()

    # Add Maquininha if not exists (Migration for Accounts)
    try:
        maq = db.query(ContaBancaria).filter(ContaBancaria.nome == "Maquininha").first()
        if not maq:
            db.add(ContaBancaria(nome="Maquininha", saldo_atual=0.0))
            db.commit()
    except Exception:
        db.rollback()
        
    # Seed Categorias Financeiras
    try:
        if db.query(CategoriaFinanceira).first() is None:
            categorias = [
                CategoriaFinanceira(nome="Serviços Realizados", tipo="Receita"),
                CategoriaFinanceira(nome="Venda de Produtos", tipo="Receita"),
                CategoriaFinanceira(nome="Despesa Fixa (Água/Luz/Aluguel)", tipo="Despesa"),
                CategoriaFinanceira(nome="Despesa Variável", tipo="Despesa"),
                CategoriaFinanceira(nome="Fornecedores/Insumos", tipo="Despesa"),
                CategoriaFinanceira(nome="Pró-labore", tipo="Despesa")
            ]
            db.add_all(categorias)
            db.commit()
    except Exception:
        db.rollback()

    db.close()
    seed_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def seed_db():
    db = SessionLocal()
    
    # Criar admin se nao existir
    if db.query(Usuario).filter(Usuario.username == "admin").first() is None:
        db.add(Usuario(username="admin", password_hash=hash_password("admin"), role="admin", permissoes="todas"))
        db.commit()
        
    # Formas de pagamento padrao
    if db.query(FormaPagamento).first() is None:
        fps = [
            FormaPagamento(nome="Pix", taxa_juros_vista=0.0, taxa_juros_parcela=0.0),
            FormaPagamento(nome="Dinheiro", taxa_juros_vista=0.0, taxa_juros_parcela=0.0),
            FormaPagamento(nome="Cartão Débito", taxa_juros_vista=1.5, taxa_juros_parcela=0.0),
            FormaPagamento(nome="Cartão Crédito", taxa_juros_vista=3.5, taxa_juros_parcela=1.5)
        ]
        db.add_all(fps)
        db.commit()
        
    if db.query(Servico).first() is None:
        servicos = [
            Servico(nome="Lavagem Americana", preco_padrao=80.0),
            Servico(nome="Lavagem Detalhada", preco_padrao=150.0),
            Servico(nome="Polimento Comercial", preco_padrao=400.0),
            Servico(nome="Vitrificação", preco_padrao=1200.0),
            Servico(nome="Higienização Interna", preco_padrao=250.0)
        ]
        db.add_all(servicos)
        
        produtos = [
            Produto(nome="Vonixx V-Floc", unidade_medida="ml", quantidade_estoque=1500, custo_unidade=0.05, preco_venda=45.0, produto_monofasico=True),
            Produto(nome="Cera de Carnaúba", unidade_medida="g", quantidade_estoque=500, custo_unidade=0.20, preco_venda=120.0, produto_monofasico=False)
        ]
        db.add_all(produtos)

        contas = [
            ContaBancaria(nome="Banco 1 (B2B)", saldo_atual=0.0),
            ContaBancaria(nome="Banco 2 (Varejo B2C)", saldo_atual=0.0),
            ContaBancaria(nome="Banco 3 (Reserva PIX)", saldo_atual=0.0)
        ]
        db.add_all(contas)

        clientes = [
            Cliente(codigo="CLI-0001", nome="João Silva", telefone="(11) 99999-1111", placa_veiculo="ABC-1234", modelo_veiculo="Fiat Uno"),
            Cliente(codigo="CLI-0002", nome="Maria Oliveira", telefone="(11) 98888-2222", placa_veiculo="XYZ-9876", modelo_veiculo="Chevrolet Onix"),
            Cliente(codigo="CLI-0003", nome="Carlos Souza", telefone="(11) 97777-3333", placa_veiculo="FGH-5678", modelo_veiculo="Honda Civic")
        ]
        db.add_all(clientes)
        db.commit()

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
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
