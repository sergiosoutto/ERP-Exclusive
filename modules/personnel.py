import streamlit as st
import pandas as pd
from datetime import datetime, date
from sqlalchemy import func
from db_config import get_db, Colaborador, EsquemaSalarial, Adiantamento, Recibo
from modules.fast_launch import gold_icon, dialog_decorator
from modules.pdf_generator import gerar_recibo_pdf

@dialog_decorator("Cadastrar Colaborador")
def dialog_novo_colaborador():
    db = next(get_db())
    nome = st.text_input("Nome do Colaborador")
    cargo = st.text_input("Cargo / Função")
    telefone = st.text_input("Telefone")
    data_inicio = st.date_input("Data de Início")
    
    if st.button("Salvar Colaborador", type="primary", use_container_width=True):
        if not nome:
            st.error("Preencha o nome.")
            return
        c = Colaborador(nome=nome, cargo=cargo, telefone=telefone, data_inicio=data_inicio)
        db.add(c)
        db.commit()
        st.success("✅ Colaborador cadastrado!")
        st.rerun()

def render_personnel():
    st.markdown(f"### {gold_icon('people')} Gestão de Pessoal", unsafe_allow_html=True)
    st.markdown("<p style='font-size:13px; color:var(--text-sec); margin-top:-10px; margin-bottom:20px;'>Gerencie folha de pagamento, comissões, vales e recibos de forma unificada.</p>", unsafe_allow_html=True)
    
    db = next(get_db())
    
    tab_colabs, tab_esquemas, tab_vales, tab_fechamento, tab_historico = st.tabs([
        "Colaboradores", 
        "Esquemas Salariais", 
        "Vales e Adiantamentos", 
        "Fechamento (Recibos)", 
        "Histórico e PDFs"
    ])
    
    # ==========================
    # 1. TAB COLABORADORES
    # ==========================
    with tab_colabs:
        col_t1, col_t2 = st.columns([0.8, 0.2])
        with col_t2:
            if st.button("+ Novo Colaborador", use_container_width=True, type="primary"): dialog_novo_colaborador()
                
        st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
        colabs = db.query(Colaborador).all()
        if colabs:
            for c in colabs:
                with st.expander(f"{c.nome} - {c.cargo or 'Sem cargo'}"):
                    c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1])
                    with c1: st.write(f"**Telefone:** {c.telefone or 'N/I'}")
                    with c2: st.write(f"**Status:** {'Ativo' if c.ativo else 'Inativo'}")
                    
                    dt_ini_str = c.data_inicio.strftime('%d/%m/%Y') if c.data_inicio else "N/I"
                    with c3: st.write(f"**Início:** {dt_ini_str}")
                    with c4:
                        if st.button("Excluir", key=f"del_colab_{c.id}", type="primary"):
                            db.delete(c)
                            db.commit()
                            st.rerun()
        else:
            st.info("Nenhum colaborador cadastrado.")
            
    # ==========================
    # 2. TAB ESQUEMAS SALARIAIS
    # ==========================
    with tab_esquemas:
        st.markdown("Defina parâmetros de remuneração baseados no Cargo. Quando o fechamento for feito para um colaborador, o sistema usará o esquema associado ao seu cargo.")
        
        # Buscar todos os cargos únicos
        cargos = db.query(Colaborador.cargo).filter(Colaborador.cargo != None).distinct().all()
        cargos_list = [c[0] for c in cargos if c[0].strip() != ""]
        
        if not cargos_list:
            st.warning("Cadastre colaboradores com cargos primeiro para definir esquemas.")
        else:
            esq_col1, esq_col2 = st.columns([1, 2])
            with esq_col1:
                cargo_sel = st.selectbox("Selecione o Cargo", cargos_list)
                
            esquema = db.query(EsquemaSalarial).filter(EsquemaSalarial.cargo == cargo_sel).first()
            if not esquema:
                esquema = EsquemaSalarial(cargo=cargo_sel, salario_fixo=0, diaria_alimentacao=0, diaria_transporte=0, perc_comissao=0, gatilho_meta=0)
            
            with st.form(f"form_esq_{cargo_sel}"):
                c1, c2 = st.columns(2)
                sal_fixo = c1.number_input("Salário Fixo Mensal Base (R$)", value=float(esquema.salario_fixo))
                perc_com = c2.number_input("Percentual de Comissão (%)", value=float(esquema.perc_comissao))
                
                c3, c4 = st.columns(2)
                dia_alim = c3.number_input("Diária de Alimentação (R$/dia)", value=float(esquema.diaria_alimentacao))
                dia_trans = c4.number_input("Diária de Transporte (R$/dia)", value=float(esquema.diaria_transporte))
                
                gat_meta = st.number_input("Gatilho de Meta para Bônus (R$ - opcional)", value=float(esquema.gatilho_meta))
                
                submit_esq = st.form_submit_button("Salvar Esquema", type="primary")
                if submit_esq:
                    if not esquema.id:
                        db.add(esquema)
                    esquema.salario_fixo = sal_fixo
                    esquema.perc_comissao = perc_com
                    esquema.diaria_alimentacao = dia_alim
                    esquema.diaria_transporte = dia_trans
                    esquema.gatilho_meta = gat_meta
                    db.commit()
                    st.success("Esquema salvo com sucesso!")
                    
    # ==========================
    # 3. TAB VALES E ADIANTAMENTOS
    # ==========================
    with tab_vales:
        st.markdown("Registro contínuo de retiradas financeiras por colaborador. Estes valores são descontados automaticamente no próximo fechamento de recibo.")
        
        with st.form("form_novo_vale"):
            col_v1, col_v2, col_v3 = st.columns([2, 1, 1])
            todos_colabs = db.query(Colaborador).all()
            dict_colabs = {f"{c.nome} ({c.cargo})": c.id for c in todos_colabs}
            
            colab_vale = col_v1.selectbox("Colaborador", list(dict_colabs.keys()) if dict_colabs else ["Nenhum"])
            valor_vale = col_v2.number_input("Valor (R$)", min_value=0.01)
            data_vale = col_v3.date_input("Data do Vale")
            desc_vale = st.text_input("Descrição / Motivo", placeholder="Ex: Vale semanal, Adiantamento para farmácia...")
            
            if st.form_submit_button("Lançar Vale", type="primary"):
                if dict_colabs:
                    cid = dict_colabs[colab_vale]
                    novo_vale = Adiantamento(colaborador_id=cid, data=data_vale, valor=valor_vale, descricao=desc_vale)
                    db.add(novo_vale)
                    db.commit()
                    st.success("Vale lançado!")
                    st.rerun()
                    
        st.markdown("---")
        st.markdown("#### Histórico de Vales em Aberto (Ainda não descontados)")
        vales_abertos = db.query(Adiantamento).filter(Adiantamento.recibo_id == None).order_by(Adiantamento.data.desc()).all()
        if vales_abertos:
            colabs_map = {c.id: c.nome for c in todos_colabs}
            for v in vales_abertos:
                nome_cv = colabs_map.get(v.colaborador_id, "Desconhecido")
                with st.container(border=True):
                    x1, x2, x3, x4 = st.columns([1, 2, 2, 1])
                    dt_v = v.data.strftime('%d/%m/%Y') if v.data else "N/I"
                    with x1: st.write(f"**{dt_v}**")
                    with x2: st.write(f"**{nome_cv}**")
                    with x3: st.write(f"{v.descricao} (R$ {v.valor:,.2f})")
                    with x4:
                        if st.button("Excluir", key=f"del_vale_{v.id}"):
                            db.delete(v)
                            db.commit()
                            st.rerun()
        else:
            st.info("Nenhum vale pendente de desconto no momento.")

    # ==========================
    # 4. TAB FECHAMENTO
    # ==========================
    with tab_fechamento:
        st.markdown("Geração de contra-cheque. Preencha os dias úteis do mês e os dias efetivamente trabalhados para o cálculo proporcional de benefícios.")
        
        if not dict_colabs:
            st.warning("Cadastre colaboradores primeiro.")
        else:
            col_f1, col_f2 = st.columns([1, 1])
            sel_colab = col_f1.selectbox("Selecione o Colaborador para Fechamento", list(dict_colabs.keys()), key="sel_fechamento")
            colab_id = dict_colabs[sel_colab]
            colab_obj = db.query(Colaborador).filter(Colaborador.id == colab_id).first()
            
            esq = db.query(EsquemaSalarial).filter(EsquemaSalarial.cargo == colab_obj.cargo).first()
            
            if not esq:
                st.error(f"O cargo '{colab_obj.cargo}' não possui um Esquema Salarial definido. Configure na aba ao lado.")
            else:
                col_d1, col_d2, col_d3 = st.columns(3)
                hoje = date.today()
                
                dt_ini_fech = col_d1.date_input("Data Inicial", date(hoje.year, hoje.month, 1))
                dt_fim_fech = col_d2.date_input("Data Final", hoje)
                
                # Para proporcionalidade salarial, usamos a proporção de dias trabalhados sobre dias úteis do mês.
                dias_uteis_mes = col_d3.number_input("Dias Úteis do Mês (Para Salário Fixo)", value=22, min_value=1)
                dias_trabalhados = col_d3.number_input("Dias Efetivamente Trabalhados (Faltas abatidas)", value=22, min_value=0)
                
                st.markdown("---")
                
                # Buscar Vales não descontados no período
                vales_periodo = db.query(Adiantamento).filter(
                    Adiantamento.colaborador_id == colab_id,
                    Adiantamento.recibo_id == None,
                    Adiantamento.data >= dt_ini_fech,
                    Adiantamento.data <= dt_fim_fech
                ).all()
                total_vales = sum(v.valor for v in vales_periodo)
                
                # Cálculos Base
                prop_salarial = float(esq.salario_fixo) * (dias_trabalhados / dias_uteis_mes) if dias_uteis_mes > 0 else 0
                tot_alim = float(esq.diaria_alimentacao) * dias_trabalhados
                tot_trans = float(esq.diaria_transporte) * dias_trabalhados
                
                # Layout Fechamento Editável
                st.markdown("#### Ajustes Finais do Recibo")
                
                with st.form("form_gerar_recibo"):
                    c_p1, c_p2 = st.columns(2)
                    c_p1.markdown("**PROVENTOS**")
                    f_sal_prop = c_p1.number_input("Salário Proporcional (Calculado)", value=prop_salarial)
                    f_alim = c_p1.number_input("Total Alimentação (Calculado)", value=tot_alim)
                    f_trans = c_p1.number_input("Total Transporte (Calculado)", value=tot_trans)
                    f_comis = c_p1.number_input("Comissões Totais", value=0.0)
                    f_bonus = c_p1.number_input("Bônus Extra (Manual)", value=0.0)
                    
                    c_p2.markdown("**DESCONTOS**")
                    f_vales = c_p2.number_input("Vales/Adiantamentos (Buscado Automático)", value=float(total_vales))
                    f_outros_desc = c_p2.number_input("Outros Descontos (Manual)", value=0.0)
                    
                    st.markdown("<hr>", unsafe_allow_html=True)
                    
                    total_p = f_sal_prop + f_alim + f_trans + f_comis + f_bonus
                    total_d = f_vales + f_outros_desc
                    liq = total_p - total_d
                    
                    st.markdown(f"<h3 style='text-align:right; color: {'red' if liq < 0 else 'green'};'>Líquido a Receber: R$ {liq:,.2f}</h3>", unsafe_allow_html=True)
                    
                    submit_fechamento = st.form_submit_button("Salvar Fechamento e Gerar Recibo", type="primary", use_container_width=True)
                    
                    if submit_fechamento:
                        novo_recibo = Recibo(
                            colaborador_id=colab_id,
                            data_geracao=hoje,
                            data_inicial=dt_ini_fech,
                            data_final=dt_fim_fech,
                            dias_trabalhados=dias_trabalhados,
                            salario_proporcional=f_sal_prop,
                            total_alimentacao=f_alim,
                            total_transporte=f_trans,
                            total_comissoes=f_comis,
                            bonus=f_bonus,
                            desconto_adiantamentos=f_vales,
                            outros_descontos=f_outros_desc,
                            valor_liquido=liq
                        )
                        db.add(novo_recibo)
                        db.commit()
                        
                        # Atualiza os vales atrelando a este recibo (para não descontar novamente)
                        for v in vales_periodo:
                            v.recibo_id = novo_recibo.id
                        db.commit()
                        
                        st.success("Recibo gerado com sucesso! Vá para a aba Histórico para exportar o PDF.")
                        
    # ==========================
    # 5. TAB HISTÓRICO DE RECIBOS
    # ==========================
    with tab_historico:
        st.markdown("Histórico de todos os recibos gerados no sistema. Exporte o comprovante em formato PDF mobile-first para envio no WhatsApp.")
        
        recibos_hist = db.query(Recibo).order_by(Recibo.id.desc()).all()
        if recibos_hist:
            todos_c = db.query(Colaborador).all()
            colabs_dict = {c.id: c for c in todos_c}
            for r in recibos_hist:
                c_r = colabs_dict.get(r.colaborador_id)
                nome_c = c_r.nome if c_r else "Excluído"
                
                with st.container(border=True):
                    h1, h2, h3, h4 = st.columns([1, 2, 1, 1])
                    with h1: 
                        dt_r = r.data_geracao.strftime('%d/%m/%Y') if r.data_geracao else "N/I"
                        st.write(f"**Data:** {dt_r}")
                    with h2: st.write(f"**{nome_c}**")
                    with h3: st.write(f"**Líquido:** R$ {r.valor_liquido:,.2f}")
                    
                    with h4:
                        if st.button("📄 Gerar PDF", key=f"pdf_recibo_{r.id}", type="primary"):
                            path_pdf = gerar_recibo_pdf(r, c_r)
                            with open(path_pdf, "rb") as pdf_file:
                                btn = st.download_button(
                                    label="📥 Baixar Comprovante",
                                    data=pdf_file,
                                    file_name=f"Recibo_{nome_c.replace(' ', '_')}_{dt_r.replace('/','')}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_pdf_{r.id}"
                                )
                            if btn:
                                pass # O próprio componente faz o download
                            
                        if st.button("🗑️", key=f"del_recibo_{r.id}"):
                            # Estornar vales
                            vales_vinculados = db.query(Adiantamento).filter(Adiantamento.recibo_id == r.id).all()
                            for vv in vales_vinculados:
                                vv.recibo_id = None
                            db.delete(r)
                            db.commit()
                            st.rerun()
        else:
            st.info("Nenhum recibo gerado ainda.")
