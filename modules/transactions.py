import streamlit as st
import pandas as pd
import io
import unicodedata
from db_config import engine
from modules.fast_launch import gold_icon

def remove_accents(input_str):
    if pd.isna(input_str):
        return ""
    nfkd_form = unicodedata.normalize('NFKD', str(input_str))
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

def render_transactions():
    # Remover emoji genérico e usar HTML com o gold_icon
    st.markdown(f"<h2 style='margin-top: 0px;'>{gold_icon('arrow-left-right')} Transações</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="premium-card">
        <h4 style="margin-bottom: 0px;">Filtros de Transações</h4>
        <p style="font-size: 13px; color: #86868B;">Encontre rapidamente qualquer transação no sistema.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Busca de dados no banco
    query = """
    SELECT 
        a.codigo as "Código",
        a.data_criacao as "Data",
        c.nome as "Cliente",
        a.valor_total as "Valor",
        a.forma_pagamento as "Tipo (Pagamento)",
        a.status as "Status",
        c.placa_veiculo as "Placa",
        c.modelo_veiculo as "Veículo"
    FROM atendimentos a
    LEFT JOIN clientes c ON a.cliente_id = c.id
    ORDER BY a.data_criacao DESC
    """
    df = pd.read_sql(query, con=engine)
    
    # Adicionar coluna auxiliar de Mês/Ano para o filtro
    df_dates = pd.to_datetime(df['Data'], errors='coerce')
    df['MesAno'] = df_dates.dt.strftime('%m/%Y')
    meses_disponiveis = sorted(df['MesAno'].dropna().unique().tolist(), reverse=True)
    
    # ==========================
    # FILTROS - LINHA 1
    # ==========================
    # Retiramos os emojis dos labels e encurtamos os nomes para não quebrar a linha
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_query = st.text_input("Busca (Nome, Placa, Código)")
    with col2:
        filter_type = st.selectbox("Forma de Pagamento", options=["Todos"] + list(df["Tipo (Pagamento)"].dropna().unique()))
    with col3:
        filter_status = st.selectbox("Status da Transação", options=["Todos"] + list(df["Status"].dropna().unique()))
        
    # ==========================
    # FILTROS - LINHA 2
    # ==========================
    col4, col5, col6, col7 = st.columns(4)
    with col4:
        filter_mes = st.selectbox("Mês de Referência", options=["Todos"] + meses_disponiveis)
    with col5:
        filter_date = st.date_input("Dia Específico", value=None)
    with col6:
        val_min = st.number_input("Valor Mín. (R$)", min_value=0.0, step=50.0, format="%.2f")
    with col7:
        val_max = st.number_input("Valor Máx. (R$)", min_value=0.0, value=0.0, step=50.0, format="%.2f", help="Deixe 0.0 para não limitar o máximo")
        
    # ==========================
    # APLICAÇÃO DOS FILTROS
    # ==========================
    filtered_df = df.copy()
    
    if search_query:
        search_norm = remove_accents(search_query)
        mask = filtered_df.apply(lambda row: 
            search_norm in remove_accents(row['Código']) or 
            search_norm in remove_accents(row['Cliente']) or 
            search_norm in remove_accents(row['Placa'])
        , axis=1)
        filtered_df = filtered_df[mask]
        
    if filter_type != "Todos":
        filtered_df = filtered_df[filtered_df["Tipo (Pagamento)"] == filter_type]
        
    if filter_status != "Todos":
        filtered_df = filtered_df[filtered_df["Status"] == filter_status]
        
    if filter_mes != "Todos":
        filtered_df = filtered_df[filtered_df['MesAno'] == filter_mes]
        
    if filter_date:
        try:
            if isinstance(filter_date, tuple) and len(filter_date) > 0:
                start_date = filter_date[0].strftime('%Y-%m-%d')
                end_date = filter_date[1].strftime('%Y-%m-%d') if len(filter_date) > 1 else start_date
                filtered_df = filtered_df[filtered_df['Data'].str.slice(0, 10) >= start_date]
                filtered_df = filtered_df[filtered_df['Data'].str.slice(0, 10) <= end_date]
            else:
                date_str = filter_date.strftime('%Y-%m-%d')
                filtered_df = filtered_df[filtered_df['Data'].str.startswith(date_str)]
        except Exception:
            pass 

    # Filtro de valor
    if val_min > 0:
        filtered_df = filtered_df[filtered_df['Valor'] >= val_min]
    if val_max > 0:
        filtered_df = filtered_df[filtered_df['Valor'] <= val_max]
            
    # Formatar Valor como Moeda apenas para exibição
    display_df = filtered_df.drop(columns=['MesAno']).copy()
    display_df['Data'] = pd.to_datetime(display_df['Data'], format='mixed', errors='coerce').dt.strftime('%d/%m/%Y %H:%M')
    
    st.markdown("---")
    
    # Alinhando Total de Registros e Botão Exportar
    col_tot, col_btn = st.columns([3, 1], vertical_alignment="bottom")
    with col_tot:
        st.markdown(f"**Total de registros encontrados: {len(filtered_df)}**")
    with col_btn:
        def to_excel(d):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                d.to_excel(writer, index=False, sheet_name='Transações')
            return output.getvalue()
            
        excel_data = to_excel(display_df)
        st.download_button(
            label="Exportar Planilha (Excel)",
            data=excel_data,
            file_name='transacoes.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            type="primary",
            use_container_width=True
        )
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Valor": st.column_config.NumberColumn(
                "Valor",
                help="Valor total da transação",
                format="R$ %.2f",
            )
        }
    )
