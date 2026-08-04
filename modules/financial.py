import streamlit as st
import pandas as pd
from datetime import datetime
from db_config import engine, get_db, ContaBancaria, CategoriaFinanceira, LancamentoFinanceiro, OrcamentoMeta, Atendimento, Cliente
from modules.fast_launch import gold_icon, dialog_decorator

def registrar_receita_pdv(atendimento_id, db):
    at = db.query(Atendimento).filter(Atendimento.id == atendimento_id).first()
    if not at or at.status != "Finalizado":
        return
        
    # Verifica se já foi lançado
    existente = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.atendimento_id == atendimento_id).first()
    if existente:
        return
        
    # Determina a conta destino baseada na forma de pagamento
    forma = at.forma_pagamento
    conta_nome = "Banco 2 (Varejo B2C)" # Dinheiro e outros vão para B2C
    if forma in ["Crédito", "Débito"]:
        conta_nome = "Maquininha"
    elif forma == "Pix":
        conta_nome = "Banco 3 (Reserva PIX)"
        
    conta = db.query(ContaBancaria).filter(ContaBancaria.nome == conta_nome).first()
    if not conta:
        conta = db.query(ContaBancaria).first()
        
    cat = db.query(CategoriaFinanceira).filter(CategoriaFinanceira.nome == "Serviços Realizados").first()
    
    if conta and cat:
        data_str = at.data_conclusao[:10] if at.data_conclusao else datetime.now().strftime('%Y-%m-%d')
        novo_lanc = LancamentoFinanceiro(
            descricao=f"OS {at.codigo} - Cliente: {db.query(Cliente).filter(Cliente.id == at.cliente_id).first().nome if at.cliente_id else 'Balcão'}",
            tipo="Receita",
            valor=at.valor_total,
            valor_previsto=at.valor_total,
            data_vencimento=data_str,
            data_pagamento=data_str,
            status="Pago",
            recorrencia="Único",
            categoria_id=cat.id,
            conta_id=conta.id,
            atendimento_id=at.id
        )
        db.add(novo_lanc)
        conta.saldo_atual += at.valor_total
        db.commit()

@dialog_decorator("Novo Lançamento")
def dialog_novo_lancamento():
    db = next(get_db())
    
    # Abas como Radio Button simulando Tabs (referência do usuário)
    tipo = st.radio("Tipo de Lançamento", ["Despesa", "Receita"], horizontal=True, label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    data_lanc = st.date_input("Data do Lançamento")
    
    # Buscar categorias do tipo selecionado
    categorias = db.query(CategoriaFinanceira).filter(CategoriaFinanceira.tipo == tipo).all()
    cat_nomes = [c.nome for c in categorias]
    
    # Contas Bancárias
    contas = db.query(ContaBancaria).all()
    contas_nomes = [c.nome for c in contas]
    
    col1, col2 = st.columns(2)
    with col1:
        conta_sel = st.selectbox("Conta Bancária", options=contas_nomes if contas_nomes else ["Nenhuma"])
    with col2:
        categoria_sel = st.selectbox("Categoria", options=cat_nomes if cat_nomes else ["Nenhuma"])
    
    desc = st.text_input("Descrição", placeholder="Ex: Conta de Luz")
    
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("<p style='font-size: 14px; margin-bottom: 2px;'>Recorrência</p>", unsafe_allow_html=True)
        recorrencia = st.radio("Recorrência", ["Único", "Parcelado", "Fixo"], horizontal=True, label_visibility="collapsed")
    with col4:
        status = st.selectbox("Status", ["Pago", "Pendente"])
        
    col5, col6 = st.columns(2)
    with col5:
        valor_real = st.number_input("Valor Real (R$)", min_value=0.0, format="%.2f")
    with col6:
        valor_prev = st.number_input("Valor Previsto (R$)", min_value=0.0, format="%.2f")
        
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Salvar", type="primary", use_container_width=True):
            cat = db.query(CategoriaFinanceira).filter(CategoriaFinanceira.nome == categoria_sel).first()
            cta = db.query(ContaBancaria).filter(ContaBancaria.nome == conta_sel).first()
            
            if cat and cta and desc:
                novo = LancamentoFinanceiro(
                    descricao=desc,
                    tipo=tipo,
                    valor=valor_real,
                    valor_previsto=valor_prev,
                    data_vencimento=data_lanc.strftime('%Y-%m-%d'),
                    data_pagamento=data_lanc.strftime('%Y-%m-%d') if status == "Pago" else None,
                    status=status,
                    recorrencia=recorrencia,
                    categoria_id=cat.id,
                    conta_id=cta.id
                )
                db.add(novo)
                
                # Se for "Pago", atualiza o saldo da conta bancária
                if status == "Pago" and valor_real > 0:
                    if tipo == "Receita":
                        cta.saldo_atual += valor_real
                    else:
                        cta.saldo_atual -= valor_real
                        
                db.commit()
                st.success("Lançamento salvo com sucesso!")
                st.rerun()
            else:
                st.error("Preencha a descrição, categoria e conta válidas.")
    with col_btn2:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()

def render_financial():
    st.markdown(f"<h2 style='margin-top:0;'>{gold_icon('wallet2')} Gestão Financeira</h2>", unsafe_allow_html=True)
    
    # Container para o filtro de meses (simulando a interface de meses horizontal)
    st.markdown("""
    <style>
    div.stRadio > div[role='radiogroup'] { flex-direction: row; flex-wrap: wrap; gap: 10px; }
    </style>
    """, unsafe_allow_html=True)
    
    meses_opcoes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year
    
    col_ano, col_mes = st.columns([1, 6])
    with col_ano:
        ano_selecionado = st.selectbox("Ano", [ano_atual - 1, ano_atual, ano_atual + 1], index=1, label_visibility="collapsed")
    with col_mes:
        mes_selecionado = st.radio("Mês", meses_opcoes, index=mes_atual - 1, label_visibility="collapsed")
    
    mes_num = meses_opcoes.index(mes_selecionado) + 1
    mes_filtro = f"{ano_selecionado}-{mes_num:02d}"
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard & Lançamentos", "🎯 Orçamentos", "🏦 Bancos", "🏷️ Categorias"])
    
    with tab1:
        col_title, col_btn = st.columns([4, 1])
        with col_title:
            st.markdown("<h3 style='margin-top:0;'>Fluxo de Caixa Mensal</h3>", unsafe_allow_html=True)
        with col_btn:
            if st.button("Lançar +", type="primary", use_container_width=True):
                dialog_novo_lancamento()
                
        # Obter dados do BD
        db = next(get_db())
        lancamentos = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.data_vencimento.startswith(mes_filtro)).all()
        
        # Cálculos de KPI
        receita_prevista = sum(l.valor_previsto for l in lancamentos if l.tipo == "Receita")
        receita_real = sum(l.valor for l in lancamentos if l.tipo == "Receita" and l.status == "Pago")
        receitas_pendentes = sum(l.valor for l in lancamentos if l.tipo == "Receita" and l.status == "Pendente")
        
        despesa_prevista = sum(l.valor_previsto for l in lancamentos if l.tipo == "Despesa")
        despesa_real = sum(l.valor for l in lancamentos if l.tipo == "Despesa" and l.status == "Pago")
        despesas_pendentes = sum(l.valor for l in lancamentos if l.tipo == "Despesa" and l.status == "Pendente")
        
        saldo_contas = sum(c.saldo_atual for c in db.query(ContaBancaria).all())
        
        saldo_previsto_final = saldo_contas + receitas_pendentes - despesas_pendentes
        
        # Banner Principal
        st.markdown(f"""
        <div class="premium-card" style="border-left: 4px solid #5E5CE6; margin-bottom: 20px;">
            <p style="font-size: 11px; font-weight: bold; color: #86868B; margin-bottom: 0;">SALDO PREVISTO CONSIDERANDO TODAS AS DESPESAS E RECEITAS PENDENTES</p>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <p style="font-size: 12px; color: #86868B;">Fórmula: Saldo Atual (R$ {saldo_contas:,.2f}) + Receitas Pendentes (R$ {receitas_pendentes:,.2f}) - Despesas Pendentes (R$ {despesas_pendentes:,.2f})</p>
                <h2 style="margin: 0; color: {'#34C759' if saldo_previsto_final >= 0 else '#FF3B30'};">R$ {saldo_previsto_final:,.2f}</h2>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # KPIs Secundários
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.markdown(f"""
            <div class="premium-card">
                <p style="font-size: 11px; font-weight: bold; margin-bottom: 5px;">💳 SALDO ATUAL (Bancos)</p>
                <h3 style="margin:0;">R$ {saldo_contas:,.2f}</h3>
            </div>
            """, unsafe_allow_html=True)
        with kpi2:
            st.markdown(f"""
            <div class="premium-card">
                <p style="font-size: 11px; font-weight: bold; margin-bottom: 5px; color:#34C759;">📈 RECEITAS (MÊS)</p>
                <div style="display:flex; justify-content: space-between;">
                    <div><span style="font-size:10px; color:#86868B;">Previsto</span><br><b>R$ {receita_prevista:,.2f}</b></div>
                    <div style="text-align:right;"><span style="font-size:10px; color:#86868B;">Real</span><br><b style="color:#34C759;">R$ {receita_real:,.2f}</b></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with kpi3:
            st.markdown(f"""
            <div class="premium-card">
                <p style="font-size: 11px; font-weight: bold; margin-bottom: 5px; color:#FF3B30;">📉 DESPESAS (MÊS)</p>
                <div style="display:flex; justify-content: space-between;">
                    <div><span style="font-size:10px; color:#86868B;">Previsto</span><br><b>R$ {despesa_prevista:,.2f}</b></div>
                    <div style="text-align:right;"><span style="font-size:10px; color:#86868B;">Real</span><br><b style="color:#FF3B30;">R$ {despesa_real:,.2f}</b></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with kpi4:
            pendentes_qtd = len([l for l in lancamentos if l.status == "Pendente"])
            st.markdown(f"""
            <div class="premium-card">
                <p style="font-size: 11px; font-weight: bold; margin-bottom: 5px; color:#FF9500;">⏳ PENDENTES</p>
                <h4 style="margin:0;">{pendentes_qtd} lanç.</h4>
                <div style="display:flex; justify-content: space-between; font-size:11px; margin-top:5px;">
                    <span style="color:#34C759;">+ R$ {receitas_pendentes:,.2f}</span>
                    <span style="color:#FF3B30;">- R$ {despesas_pendentes:,.2f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Detalhamento de Lançamentos do Mês")
        # Listar em tabela
        if lancamentos:
            df = pd.DataFrame([{
                "Data": l.data_vencimento,
                "Descrição": l.descricao,
                "Tipo": l.tipo,
                "Valor": f"R$ {l.valor:,.2f}",
                "Status": l.status,
                "Recorrência": l.recorrencia
            } for l in lancamentos])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum lançamento encontrado para este mês.")

    with tab2:
        st.markdown("### 🎯 Orçamentos e Metas")
        st.write("Defina um teto de gastos para suas categorias.")
        # Em breve a implementação do CRUD de orçamentos
        st.info("Módulo de Orçamentos em desenvolvimento.")
        
    with tab3:
        st.markdown("### 🏦 Contas Bancárias")
        contas = db.query(ContaBancaria).all()
        for c in contas:
            st.markdown(f"""
            <div class='premium-card'>
                <h4>{c.nome}</h4>
                <h3 style='color: {"#34C759" if c.saldo_atual >= 0 else "#FF3B30"}; margin-top: 0;'>R$ {c.saldo_atual:,.2f}</h3>
            </div>
            """, unsafe_allow_html=True)
            
    with tab4:
        st.markdown("### 🏷️ Categorias Financeiras")
        categorias = db.query(CategoriaFinanceira).all()
        if categorias:
            df_cat = pd.DataFrame([{"Nome": c.nome, "Tipo": c.tipo} for c in categorias])
            st.dataframe(df_cat, use_container_width=True, hide_index=True)
