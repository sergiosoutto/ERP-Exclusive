import streamlit as st
import pandas as pd
from datetime import datetime
from db_config import engine, get_db, ContaBancaria, CategoriaFinanceira, SubcategoriaFinanceira, LancamentoFinanceiro, OrcamentoMeta, Atendimento, Cliente
from modules.fast_launch import gold_icon, dialog_decorator

def registrar_receita_pdv(atendimento_id, db):
    at = db.query(Atendimento).filter(Atendimento.id == atendimento_id).first()
    if not at or at.status != "Finalizado":
        return
        
    existente = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.atendimento_id == atendimento_id).first()
    if existente:
        return
        
    forma = at.forma_pagamento
    conta_nome = "Banco 2 (Varejo B2C)"
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
    tipo = st.radio("Tipo de Lançamento", ["Despesa", "Receita"], horizontal=True, label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    data_lanc = st.date_input("Data do Lançamento (Primeiro Vencimento)")
    
    categorias = db.query(CategoriaFinanceira).filter(CategoriaFinanceira.tipo == tipo).all()
    cat_nomes = [c.nome for c in categorias]
    
    col1, col2 = st.columns(2)
    with col1:
        categoria_sel = st.selectbox("Categoria", options=cat_nomes if cat_nomes else ["Nenhuma"])
    with col2:
        subcategorias = []
        if categoria_sel != "Nenhuma":
            cat = db.query(CategoriaFinanceira).filter(CategoriaFinanceira.nome == categoria_sel).first()
            if cat:
                subs = db.query(SubcategoriaFinanceira).filter(SubcategoriaFinanceira.categoria_id == cat.id).all()
                subcategorias = [s.nome for s in subs]
        subcat_sel = st.selectbox("Subcategoria (Opcional)", options=["Nenhuma"] + subcategorias)
        
    contas = db.query(ContaBancaria).all()
    contas_nomes = ["Usar Banco Padrão da Categoria"] + [c.nome for c in contas]
    
    conta_sel = st.selectbox("Conta Bancária (Para Baixa)", options=contas_nomes)
    desc = st.text_input("Descrição", placeholder="Ex: Conta de Luz")
    
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("<p style='font-size: 14px; margin-bottom: 2px;'>Recorrência</p>", unsafe_allow_html=True)
        recorrencia = st.radio("Recorrência", ["Único", "Parcelado", "Fixo"], horizontal=True, label_visibility="collapsed")
    with col4:
        status = st.selectbox("Status Atual", ["Pago", "Pendente"])
        
    qtd_parcelas = 1
    if recorrencia == "Parcelado":
        qtd_parcelas = st.number_input("Quantidade de Parcelas", min_value=2, max_value=72, value=2)
    elif recorrencia == "Fixo":
        qtd_parcelas = 12 # Projeta 12 meses
        
    col5, col6 = st.columns(2)
    with col5:
        valor_real = st.number_input("Valor Real (R$)", min_value=0.0, format="%.2f")
    with col6:
        valor_prev = st.number_input("Valor Previsto (R$)", min_value=0.0, format="%.2f")
        
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Salvar", type="primary", use_container_width=True):
            cat = db.query(CategoriaFinanceira).filter(CategoriaFinanceira.nome == categoria_sel).first()
            subcat = db.query(SubcategoriaFinanceira).filter(SubcategoriaFinanceira.nome == subcat_sel).first() if subcat_sel != "Nenhuma" else None
            
            # Determinar a conta de destino
            cta = None
            if conta_sel != "Usar Banco Padrão da Categoria":
                cta = db.query(ContaBancaria).filter(ContaBancaria.nome == conta_sel).first()
            else:
                # Tentar subcategoria primeiro, depois categoria
                bp_id = subcat.banco_padrao_id if subcat and subcat.banco_padrao_id else (cat.banco_padrao_id if cat else None)
                if bp_id:
                    cta = db.query(ContaBancaria).filter(ContaBancaria.id == bp_id).first()
                else:
                    cta = db.query(ContaBancaria).first() # Fallback seguro
            
            if cat and cta and desc:
                from dateutil.relativedelta import relativedelta
                lancamentos_inserir = []
                
                for i in range(qtd_parcelas):
                    data_venc = data_lanc + relativedelta(months=i)
                    
                    # Apenas a primeira parcela considera o status selecionado se for pago
                    # As subsequentes são sempre pendentes
                    status_parcela = status if i == 0 else "Pendente"
                    data_pag_parcela = data_venc.strftime('%Y-%m-%d') if status_parcela == "Pago" else None
                    
                    desc_final = desc
                    if recorrencia == "Parcelado":
                        desc_final = f"{desc} ({i+1}/{qtd_parcelas})"
                    elif recorrencia == "Fixo" and i > 0:
                        desc_final = f"{desc} (Projeção)"
                        
                    novo = LancamentoFinanceiro(
                        descricao=desc_final,
                        tipo=tipo,
                        valor=valor_real if i == 0 else 0.0, # valor real só na primeira se já estiver pago
                        valor_previsto=valor_prev if valor_prev > 0 else valor_real,
                        data_vencimento=data_venc.strftime('%Y-%m-%d'),
                        data_pagamento=data_pag_parcela,
                        status=status_parcela,
                        recorrencia=recorrencia,
                        categoria_id=cat.id,
                        subcategoria_id=subcat.id if subcat else None,
                        conta_id=cta.id
                    )
                    lancamentos_inserir.append(novo)
                
                db.add_all(lancamentos_inserir)
                
                if status == "Pago" and valor_real > 0:
                    if tipo == "Receita":
                        cta.saldo_atual += valor_real
                    else:
                        cta.saldo_atual -= valor_real
                        
                db.commit()
                st.toast("Lançamento salvo com sucesso!", icon="✅")
            else:
                st.error("Preencha a descrição, categoria e certifique-se de haver uma conta válida.")
    with col_btn2:
        if st.button("Fechar", use_container_width=True):
            st.toast("Fechando...", icon="ℹ️")

@dialog_decorator("Gerenciar Pendentes")
def dialog_pendentes():
    db = next(get_db())
    pendentes = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.status == "Pendente").order_by(LancamentoFinanceiro.data_vencimento).all()
    if not pendentes:
        st.success("Não há lançamentos pendentes!")
        return
        
    contas = db.query(ContaBancaria).all()
    contas_nomes = ["Usar Banco Padrão"] + [c.nome for c in contas]
    
    for idx, p in enumerate(pendentes):
        if idx > 0:
            st.divider()
            
        edit_key = f"edit_pend_{p.id}"
        
        if st.session_state.get(edit_key, False):
            # Modo Edição
            n_desc = st.text_input("Descrição", value=p.descricao, key=f"ndesc_{p.id}")
            c_val, c_dat = st.columns(2)
            with c_val:
                n_val = st.number_input("Valor Previsto", value=p.valor_previsto, format="%.2f", key=f"nval_{p.id}")
            with c_dat:
                from datetime import datetime
                try:
                    d_venc = datetime.strptime(p.data_vencimento, '%Y-%m-%d').date()
                except:
                    d_venc = datetime.now().date()
                n_dat = st.date_input("Vencimento", value=d_venc, key=f"ndat_{p.id}")
            
            c_s, c_c = st.columns(2)
            with c_s:
                if st.button("Salvar Alterações", type="primary", use_container_width=True, key=f"sv_{p.id}"):
                    p.descricao = n_desc
                    p.valor_previsto = n_val
                    p.data_vencimento = n_dat.strftime('%Y-%m-%d')
                    db.commit()
                    st.session_state[edit_key] = False
                    st.toast("Lançamento atualizado!", icon="✅")
            with c_c:
                if st.button("Cancelar", use_container_width=True, key=f"cx_{p.id}"):
                    st.session_state[edit_key] = False
        else:
            # Modo Visualização
            col1, col2 = st.columns([1, 1.2])
            with col1:
                st.markdown(f"<p style='margin:0; font-weight:bold; font-size:15px; color:#1D1D1F;'>{p.descricao}</p>", unsafe_allow_html=True)
                cor = "#34C759" if p.tipo == "Receita" else "#FF3B30"
                st.markdown(f"<p style='margin:0; font-size:14px; font-weight:600; color:{cor};'>R$ {p.valor_previsto:,.2f} <span style='font-size:11px; font-weight:400; color:#86868B;'>({p.tipo})</span></p>", unsafe_allow_html=True)
                st.markdown(f"<p style='margin-top:5px; font-size:12px; color:#86868B;'>Vencimento: <b>{p.data_vencimento}</b></p>", unsafe_allow_html=True)
                
            with col2:
                st.markdown("<div style='font-size: 11px; color: #86868B; margin-bottom: 2px;'>Conta de Baixa:</div>", unsafe_allow_html=True)
                banco_sel = st.selectbox("Confirmar Banco para Baixa", contas_nomes, key=f"banco_pend_{p.id}", label_visibility="collapsed")
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("Baixar", key=f"baixar_{p.id}", use_container_width=True, type="primary"):
                        cta = None
                        if banco_sel != "Usar Banco Padrão":
                            cta = db.query(ContaBancaria).filter(ContaBancaria.nome == banco_sel).first()
                        else:
                            cat = db.query(CategoriaFinanceira).filter(CategoriaFinanceira.id == p.categoria_id).first()
                            subcat = db.query(SubcategoriaFinanceira).filter(SubcategoriaFinanceira.id == p.subcategoria_id).first() if p.subcategoria_id else None
                            bp_id = subcat.banco_padrao_id if subcat and subcat.banco_padrao_id else (cat.banco_padrao_id if cat else None)
                            
                            if bp_id:
                                cta = db.query(ContaBancaria).filter(ContaBancaria.id == bp_id).first()
                            else:
                                cta = db.query(ContaBancaria).filter(ContaBancaria.id == p.conta_id).first() # Fallback
                        
                        if cta:
                            p.status = "Pago"
                            from datetime import datetime
                            p.data_pagamento = datetime.now().strftime('%Y-%m-%d')
                            p.valor = p.valor_previsto
                            p.conta_id = cta.id
                            
                            if p.tipo == "Receita":
                                cta.saldo_atual += p.valor
                            else:
                                cta.saldo_atual -= p.valor
                            db.commit()
                            st.toast("Baixa realizada com sucesso!", icon="✅")
                        else:
                            st.error("Banco não encontrado.")
                with c2:
                    if st.button("Editar", key=f"ed_{p.id}", use_container_width=True):
                        st.session_state[edit_key] = True
                with c3:
                    if st.button("Excluir", key=f"excluir_pend_{p.id}", use_container_width=True):
                        db.delete(p)
                        db.commit()
                        st.toast("Lançamento excluído!", icon="✅")

def render_financial():
    st.markdown(f"<h2 style='margin-top:0;'>{gold_icon('wallet2')} Gestão Financeira</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    div.stRadio > div[role='radiogroup'] { flex-direction: row; flex-wrap: wrap; gap: 10px; }
    div[data-testid="column"] > div { height: 100%; }
    .kpi-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E5EA;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        display: flex;
        flex-direction: column;
        justify-content: center;
        height: 100%;
    }
    .kpi-title {
        font-size: 11px;
        font-weight: 700;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 700;
        margin: 0;
    }
    .kpi-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 8px;
    }
    .kpi-subtext {
        font-size: 11px;
        color: #86868B;
    }
    .kpi-subval {
        font-size: 13px;
        font-weight: 600;
    }
    .toolbar-btn {
        background: transparent;
        border: 1px solid #E5E5EA;
        border-radius: 8px;
        padding: 6px 12px;
        color: #1D1D1F;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        text-decoration: none;
    }
    .toolbar-btn:hover { background: #F5F5F7; }
    </style>
    """, unsafe_allow_html=True)
    
    meses_opcoes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
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
    
    
    db = next(get_db())
    
    # Lógica de Notificações
    from datetime import timedelta
    hoje = datetime.now().strftime('%Y-%m-%d')
    amanha = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    todos_pendentes = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.status == "Pendente").all()
    vence_hoje = len([l for l in todos_pendentes if l.data_vencimento == hoje])
    vence_amanha = len([l for l in todos_pendentes if l.data_vencimento == amanha])
    atrasadas = len([l for l in todos_pendentes if l.data_vencimento < hoje])
    notif_total = vence_hoje + vence_amanha + atrasadas
    
    # Toolbar
    col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns([2, 1, 1, 1.5, 2])
    with col_t1:
        st.markdown(f"<h3 style='margin-top:0;'>{gold_icon('chart')} Fluxo de Caixa Mensal</h3>", unsafe_allow_html=True)
    with col_t2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col_t3:
        if st.button("💾 Backup", use_container_width=True):
            st.toast("Backup iniciado... (a ser implementado)", icon="💾")
    with col_t4:
        with st.popover(f"🔔 Notificações ({notif_total})", use_container_width=True):
            if notif_total == 0:
                st.write("Tudo em dia!")
            if atrasadas > 0:
                st.error(f"{atrasadas} despesa(s) atrasada(s)!")
            if vence_hoje > 0:
                st.warning(f"{vence_hoje} despesa(s) vencendo hoje!")
            if vence_amanha > 0:
                st.info(f"{vence_amanha} despesa(s) vencendo amanhã!")
    with col_t5:
        if st.button("Lançar +", type="primary", use_container_width=True):
            dialog_novo_lancamento()
            
    # Última vez salvo
    st.markdown(f"<p style='text-align:right; font-size:11px; color:#86868B; margin-top:-10px;'>Última vez atualizado: {datetime.now().strftime('%d/%m %H:%M')}</p>", unsafe_allow_html=True)
            
    lancamentos = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.data_vencimento.startswith(mes_filtro)).all()
    
    receita_prevista = sum(l.valor_previsto for l in lancamentos if l.tipo == "Receita")
    receita_real = sum(l.valor for l in lancamentos if l.tipo == "Receita" and l.status == "Pago")
    receitas_pendentes = sum(l.valor_previsto for l in lancamentos if l.tipo == "Receita" and l.status == "Pendente")
    
    despesa_prevista = sum(l.valor_previsto for l in lancamentos if l.tipo == "Despesa")
    despesa_real = sum(l.valor for l in lancamentos if l.tipo == "Despesa" and l.status == "Pago")
    despesas_pendentes = sum(l.valor_previsto for l in lancamentos if l.tipo == "Despesa" and l.status == "Pendente")
    
    saldo_contas = sum(c.saldo_atual for c in db.query(ContaBancaria).all())
    saldo_previsto_final = saldo_contas + receitas_pendentes - despesas_pendentes
    cor_saldo_final = "#34C759" if saldo_previsto_final >= 0 else "#FF3B30"
    
    st.markdown(f"""
    <div class="kpi-card" style="border-left: 4px solid #5E5CE6; margin-bottom: 20px; padding: 12px 20px;">
        <p style="font-size: 11px; font-weight: bold; color: #86868B; margin-bottom: 5px;">{gold_icon('check')} SALDO PREVISTO (CONSIDERANDO PENDÊNCIAS DO MÊS)</p>
        <div style="display: flex; justify-content: space-between; align-items: flex-end;">
            <p style="font-size: 12px; color: #86868B; margin: 0;">Fórmula: Saldo Atual (R$ {saldo_contas:,.2f}) + Receitas (R$ {receitas_pendentes:,.2f}) - Despesas (R$ {despesas_pendentes:,.2f})</p>
            <h2 style="margin: 0; color: {cor_saldo_final}; font-size: 28px;">R$ {saldo_previsto_final:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        cor_saldo_atual = "#1D1D1F" if saldo_contas >= 0 else "#FF3B30"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title" style="color: #1D1D1F;">{gold_icon('credit-card')} SALDO ATUAL (Bancos)</div>
            <div class="kpi-value" style="color: {cor_saldo_atual};">R$ {saldo_contas:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title" style="color: #34C759;">{gold_icon('graph-up-arrow')} RECEITAS (MÊS)</div>
            <div class="kpi-row">
                <div>
                    <div class="kpi-subtext">Previsto</div>
                    <div class="kpi-subval" style="color: #1D1D1F;">R$ {receita_prevista:,.2f}</div>
                </div>
                <div style="text-align:right;">
                    <div class="kpi-subtext">Real</div>
                    <div class="kpi-subval" style="color: #34C759;">R$ {receita_real:,.2f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title" style="color: #FF3B30;">{gold_icon('graph-down-arrow')} DESPESAS (MÊS)</div>
            <div class="kpi-row">
                <div>
                    <div class="kpi-subtext">Previsto</div>
                    <div class="kpi-subval" style="color: #1D1D1F;">R$ {despesa_prevista:,.2f}</div>
                </div>
                <div style="text-align:right;">
                    <div class="kpi-subtext">Real</div>
                    <div class="kpi-subval" style="color: #FF3B30;">R$ {despesa_real:,.2f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with kpi4:
        pendentes_qtd = len([l for l in lancamentos if l.status == "Pendente"])
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title" style="color: #FF9500;">{gold_icon('hourglass-split')} PENDENTES</div>
            <div class="kpi-value" style="color: #1D1D1F; font-size: 20px;">{pendentes_qtd} lanç.</div>
            <div class="kpi-row" style="margin-top: 4px;">
                <div class="kpi-subval" style="color:#34C759;">+ R$ {receitas_pendentes:,.2f}</div>
                <div class="kpi-subval" style="color:#FF3B30;">- R$ {despesas_pendentes:,.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Gerenciar Pendentes", use_container_width=True):
            dialog_pendentes()
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"#### {gold_icon('list-check')} Detalhamento de Lançamentos do Mês", unsafe_allow_html=True)
    if lancamentos:
        df = pd.DataFrame([{
            "Data": l.data_vencimento,
            "Descrição": l.descricao,
            "Categoria": db.query(CategoriaFinanceira).filter(CategoriaFinanceira.id == l.categoria_id).first().nome if l.categoria_id else "",
            "Tipo": l.tipo,
            "Valor": f"R$ {l.valor:,.2f}",
            "Status": l.status
        } for l in lancamentos])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum lançamento encontrado para este mês.")

