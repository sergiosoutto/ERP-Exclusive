def formatar_moeda(valor):
    try:
        return f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return '0,00'

import streamlit as st
import pandas as pd
from datetime import datetime
from db_config import engine, get_db, ContaBancaria, CategoriaFinanceira, LancamentoFinanceiro, Atendimento, Cliente
from modules.fast_launch import gold_icon, dialog_decorator

def registrar_receita_pdv(atendimento_id, db):
    at = db.query(Atendimento).filter(Atendimento.id == atendimento_id).first()
    if not at or at.status != "Finalizado":
        return
        
    existente = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.atendimento_id == atendimento_id).first()
    if existente:
        return
        
    forma = at.forma_pagamento
    conta = db.query(ContaBancaria).first()
    cat = db.query(CategoriaFinanceira).filter(CategoriaFinanceira.nome == "Serviços Realizados").first()
    
    if conta and cat:
        data_str = at.data_conclusao[:10] if at.data_conclusao else datetime.now().strftime('%Y-%m-%d')
        cli = db.query(Cliente).filter(Cliente.id == at.cliente_id).first()
        cli_nome = cli.nome if cli else 'Balcão'
        
        novo_lanc = LancamentoFinanceiro(
            descricao=f"OS {at.codigo} - {cli_nome} ({forma})",
            tipo="Receita",
            valor=at.valor_total,
            valor_previsto=at.valor_total,
            data_vencimento=data_str,
            data_pagamento=None,
            status="Pendente",
            recorrencia="Único",
            categoria_id=cat.id,
            conta_id=conta.id,
            atendimento_id=at.id
        )
        db.add(novo_lanc)
        db.commit()

@dialog_decorator("Auditar Receita")
def dialog_auditar_receita(lanc_id):
    db = next(get_db())
    lanc = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.id == lanc_id).first()
    if not lanc: return
    
    st.markdown(f"**Origem:** {lanc.descricao}")
    st.markdown(f"**Valor Base da OS:** R$ {formatar_moeda(lanc.valor_previsto)}")
    
    with st.form("form_audit"):
        valor_liquido = st.number_input("Valor Líquido (após taxas/deságios)", value=float(lanc.valor_previsto), min_value=0.0)
        dt_pag = st.date_input("Data Real do Crédito na Conta", value=datetime.today())
        
        contas = db.query(ContaBancaria).all()
        conta_sel = st.selectbox("Conta Destino", [c.nome for c in contas], index=0)
        
        if st.form_submit_button("Confirmar e Lançar no Caixa", type="primary", use_container_width=True):
            conta_obj = next((c for c in contas if c.nome == conta_sel), None)
            
            lanc.valor = valor_liquido
            lanc.data_pagamento = dt_pag.strftime("%Y-%m-%d")
            lanc.conta_id = conta_obj.id if conta_obj else lanc.conta_id
            lanc.status = "Pago"
            
            # Update bank balance
            if conta_obj:
                conta_obj.saldo_atual += valor_liquido
                
            db.commit()
            st.session_state['success_msg'] = "Receita auditada e lançada no caixa!"
            st.rerun()

@dialog_decorator("Lançar Despesa")
def dialog_nova_despesa():
    db = next(get_db())
    with st.form("form_despesa"):
        desc = st.text_input("Descrição (Ex: Conta de Luz, Fornecedor X)")
        valor = st.number_input("Valor", min_value=0.0, value=0.0)
        venc = st.date_input("Data de Vencimento")
        
        cats = db.query(CategoriaFinanceira).filter(CategoriaFinanceira.tipo == "Despesa").all()
        cat_sel = st.selectbox("Categoria", [c.nome for c in cats] if cats else ["Sem Categoria"])
        
        pago_agora = st.checkbox("Já foi pago?")
        
        if st.form_submit_button("Salvar Despesa", type="primary", use_container_width=True):
            if desc and valor > 0:
                cat_obj = next((c for c in cats if c.nome == cat_sel), None) if cats else None
                cat_id = cat_obj.id if cat_obj else None
                
                status = "Pago" if pago_agora else "Pendente"
                dt_pag = datetime.today().strftime("%Y-%m-%d") if pago_agora else None
                
                lanc = LancamentoFinanceiro(
                    descricao=desc, tipo="Despesa", valor=valor, valor_previsto=valor,
                    data_vencimento=venc.strftime("%Y-%m-%d"), data_pagamento=dt_pag,
                    status=status, categoria_id=cat_id, conta_id=db.query(ContaBancaria).first().id
                )
                db.add(lanc)
                if pago_agora:
                    conta = db.query(ContaBancaria).first()
                    if conta: conta.saldo_atual -= valor
                db.commit()
                st.session_state['success_msg'] = "Despesa registrada!"
                st.rerun()

@dialog_decorator("Pagar Despesa")
def dialog_pagar_despesa(lanc_id):
    db = next(get_db())
    lanc = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.id == lanc_id).first()
    if not lanc: return
    
    st.write(f"**Despesa:** {lanc.descricao}")
    st.write(f"**Vencimento:** {lanc.data_vencimento}")
    st.write(f"**Valor:** R$ {formatar_moeda(lanc.valor_previsto)}")
    
    with st.form("form_pagar_desp"):
        dt_pag = st.date_input("Data do Pagamento", value=datetime.today())
        contas = db.query(ContaBancaria).all()
        conta_sel = st.selectbox("Conta Saída", [c.nome for c in contas])
        
        if st.form_submit_button("Confirmar Pagamento", type="primary", use_container_width=True):
            conta_obj = next((c for c in contas if c.nome == conta_sel), None)
            if conta_obj:
                conta_obj.saldo_atual -= lanc.valor_previsto
                lanc.conta_id = conta_obj.id
                
            lanc.status = "Pago"
            lanc.data_pagamento = dt_pag.strftime("%Y-%m-%d")
            db.commit()
            st.session_state['success_msg'] = "Despesa paga e baixada!"
            st.rerun()

def render_financial():
    if st.session_state.get('success_msg'):
        st.toast(st.session_state['success_msg'], icon='✅')
        st.session_state['success_msg'] = None
        
    db = next(get_db())
    st.markdown(f"<h2>{gold_icon('cash-coin')} Gestão Financeira Inteligente</h2>", unsafe_allow_html=True)
    
    abas = ["Geral & Extrato", "Auditoria (A Receber)", "Despesas (A Pagar)"]
    aba = st.pills("Módulos", abas, default="Geral & Extrato", label_visibility="collapsed")
    
    if aba == "Geral & Extrato":
        contas = db.query(ContaBancaria).all()
        saldo_real = sum(c.saldo_atual for c in contas)
        
        a_receber = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.tipo == "Receita", LancamentoFinanceiro.status == "Pendente").all()
        total_a_receber = sum(l.valor_previsto for l in a_receber)
        
        a_pagar = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.tipo == "Despesa", LancamentoFinanceiro.status == "Pendente").all()
        total_a_pagar = sum(l.valor_previsto for l in a_pagar)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div class='premium-card' style='text-align:center;'><h6>💰 Saldo em Caixa</h6><h2 style='color:#2ecc71;'>R$ {formatar_moeda(saldo_real)}</h2></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='premium-card' style='text-align:center;'><h6>⏳ Receitas a Auditar</h6><h2 style='color:#f1c40f;'>R$ {formatar_moeda(total_a_receber)}</h2></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='premium-card' style='text-align:center;'><h6>📉 Despesas a Pagar</h6><h2 style='color:#e74c3c;'>R$ {formatar_moeda(total_a_pagar)}</h2></div>", unsafe_allow_html=True)
            
        st.markdown("### 📋 Extrato Simplificado (Lançamentos Efetivados)")
        efetivados = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.status == "Pago").order_by(LancamentoFinanceiro.data_pagamento.desc()).limit(50).all()
        
        if efetivados:
            for l in efetivados:
                cor = "#2ecc71" if l.tipo == "Receita" else "#e74c3c"
                sinal = "+" if l.tipo == "Receita" else "-"
                with st.container(border=True):
                    cols = st.columns([1.5, 3, 1, 1.5])
                    cols[0].markdown(f"<span style='font-size:13px; color:#888;'>{l.data_pagamento}</span>", unsafe_allow_html=True)
                    cols[1].markdown(f"<span style='font-size:14px; font-weight:600;'>{l.descricao}</span>", unsafe_allow_html=True)
                    cols[2].markdown(f"<span style='font-size:13px; color:#555;'>{l.tipo}</span>", unsafe_allow_html=True)
                    cols[3].markdown(f"<b style='color:{cor}; font-size:15px;'>{sinal} R$ {formatar_moeda(l.valor)}</b>", unsafe_allow_html=True)
        else:
            st.info("Nenhum lançamento no caixa ainda.")
            
    elif aba == "Auditoria (A Receber)":
        st.markdown("### 🔍 Conferência de Receitas (Checkout de OS)")
        st.markdown("<p style='font-size:13px; color:#777;'>Valores das OSs finalizadas caem aqui. Ajuste taxas e deságios antes de enviar para o cofre real.</p>", unsafe_allow_html=True)
        pendentes_rec = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.tipo == "Receita", LancamentoFinanceiro.status == "Pendente").all()
        
        if pendentes_rec:
            for l in pendentes_rec:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1.5])
                    c1.markdown(f"<span style='font-size:15px; font-weight:700;'>{l.descricao}</span>", unsafe_allow_html=True)
                    c2.markdown(f"<span style='font-size:16px; font-weight:bold; color:var(--accent);'>R$ {formatar_moeda(l.valor_previsto)}</span>", unsafe_allow_html=True)
                    if c3.button("✔ Auditar e Confirmar", key=f"aud_{l.id}", type="primary", use_container_width=True):
                        dialog_auditar_receita(l.id)
        else:
            st.success("Tudo certo! Nenhuma OS aguardando auditoria.")
            
    elif aba == "Despesas (A Pagar)":
        col1, col2 = st.columns([3, 1.5])
        col1.markdown("### 📉 Previsibilidade de Despesas")
        if col2.button("+ Lançar Nova Despesa", type="primary", use_container_width=True):
            dialog_nova_despesa()
            
        pendentes_desp = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.tipo == "Despesa", LancamentoFinanceiro.status == "Pendente").order_by(LancamentoFinanceiro.data_vencimento.asc()).all()
        
        if pendentes_desp:
            hoje_str = datetime.today().strftime("%Y-%m-%d")
            for l in pendentes_desp:
                atrasada = l.data_vencimento and l.data_vencimento < hoje_str
                cor_badge = "background:#e74c3c;color:white;" if atrasada else "background:rgba(241, 196, 15, 0.2);color:#f39c12;"
                txt_badge = "VENCIDA" if atrasada else "No Prazo"
                
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1.5])
                    c1.markdown(f"<span style='font-size:15px; font-weight:700;'>{l.descricao}</span> <span style='{cor_badge} padding:2px 8px; border-radius:12px; font-size:11px; font-weight:bold; margin-left:6px;'>{txt_badge}</span><br><span style='font-size:12px; color:#888;'>Vencimento: {l.data_vencimento}</span>", unsafe_allow_html=True)
                    c2.markdown(f"<div style='font-size:16px; font-weight:bold; color:#e74c3c;'>R$ {formatar_moeda(l.valor_previsto)}</div>", unsafe_allow_html=True)
                    if c3.button("💲 Quitar e Baixar", key=f"pag_{l.id}", type="primary", use_container_width=True):
                        dialog_pagar_despesa(l.id)
        else:
            st.info("Nenhuma despesa programada.")
