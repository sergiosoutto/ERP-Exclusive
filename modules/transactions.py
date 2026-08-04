import streamlit as st
import pandas as pd
import io
import unicodedata
from db_config import engine

def remove_accents(input_str):
    if pd.isna(input_str):
        return ""
    nfkd_form = unicodedata.normalize('NFKD', str(input_str))
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

def render_transactions():
    st.title("🔀 Transações")
    
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
    
    # Garantir que a coluna de data seja lida corretamente (mesmo que seja string isoformat)
    # df['Data'] = pd.to_datetime(df['Data']).dt.strftime('%d/%m/%Y %H:%M')
    
    # Criar os filtros na UI
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_query = st.text_input("🔍 Busca Genérica (Nome, Código, Placa...)")
    with col2:
        filter_type = st.selectbox("💳 Forma de Pagamento", options=["Todos"] + list(df["Tipo (Pagamento)"].dropna().unique()))
    with col3:
        filter_status = st.selectbox("📌 Status", options=["Todos"] + list(df["Status"].dropna().unique()))
        
    col4, col5 = st.columns(2)
    with col4:
        # Filtro de Data (pode ser data única ou range, st.date_input aceita tuple)
        filter_date = st.date_input("📅 Data da Transação", value=None)
    with col5:
        # Exportar Excel (Ajustamos embaixo)
        st.write("")
        st.write("")
        
    # Aplicando os Filtros
    filtered_df = df.copy()
    
    if search_query:
        search_norm = remove_accents(search_query)
        
        # Filtra nas colunas (Código, Cliente, Placa)
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
        
    if filter_date:
        # Date input can return a single date or a tuple of dates if range is selected
        # But we didn't specify range here, so it's a single date.
        # We need to filter based on date part of the datetime string
        try:
            if isinstance(filter_date, tuple) and len(filter_date) > 0:
                start_date = filter_date[0].strftime('%Y-%m-%d')
                end_date = filter_date[1].strftime('%Y-%m-%d') if len(filter_date) > 1 else start_date
                filtered_df = filtered_df[filtered_df['Data'].str.slice(0, 10) >= start_date]
                filtered_df = filtered_df[filtered_df['Data'].str.slice(0, 10) <= end_date]
            else:
                date_str = filter_date.strftime('%Y-%m-%d')
                filtered_df = filtered_df[filtered_df['Data'].str.startswith(date_str)]
        except Exception as e:
            pass # Ignorar erros de formato de data por enquanto
            
    # Formatar Valor como Moeda apenas para exibição (usamos um copy ou estilizamos o dataframe)
    display_df = filtered_df.copy()
    display_df['Data'] = pd.to_datetime(display_df['Data'], format='mixed', errors='coerce').dt.strftime('%d/%m/%Y %H:%M')
    
    st.markdown("---")
    st.markdown(f"**Total de registros encontrados: {len(filtered_df)}**")
    
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
    
    # Função para gerar Excel
    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Transações')
        processed_data = output.getvalue()
        return processed_data
        
    excel_data = to_excel(display_df)
    
    # Botão de Exportação Alinhado
    st.download_button(
        label="📊 Exportar para Excel",
        data=excel_data,
        file_name='transacoes.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        type="primary"
    )
