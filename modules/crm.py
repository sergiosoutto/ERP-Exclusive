import streamlit as st
import pandas as pd
from datetime import datetime
from db_config import get_db, Cliente, Atendimento
from modules.fast_launch import gold_icon, dialog_novo_cliente, dialog_decorator

@dialog_decorator("Editar Cliente")
def dialog_editar_cliente(cliente_id):
    db = next(get_db())
    c = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not c:
        st.error("Cliente não encontrado.")
        return
        
    nome = st.text_input("Nome", value=c.nome)
    telefone = st.text_input("Celular/WhatsApp", value=c.telefone or "")
    veiculo = st.text_input("Veículo (Modelo/Cor)", value=c.modelo_veiculo or "")
    placa = st.text_input("Placa", value=c.placa_veiculo or "")
    
    if st.button("Salvar Alterações", type="primary", use_container_width=True):
        c.nome = nome
        c.telefone = telefone
        c.modelo_veiculo = veiculo
        c.placa_veiculo = placa
        db.commit()
        st.rerun()

@dialog_decorator("Excluir Cliente")
def dialog_excluir_cliente(cliente_id):
    db = next(get_db())
    c = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    st.warning(f"Tem certeza que deseja excluir o cliente **{c.nome}**?")
    st.markdown("Isso não apagará o histórico financeiro já registrado nas OSs antigas, mas o cliente não aparecerá mais no CRM.")
    
    if st.button("Sim, Excluir Cliente", type="primary", use_container_width=True):
        db.delete(c)
        db.commit()
        st.rerun()

def get_selo(valor_total):
    if valor_total >= 1000:
        return "💎 Diamante"
    elif valor_total >= 300:
        return "🥇 Ouro"
    elif valor_total > 0:
        return "🥈 Prata"
    return "N/A"

def render_crm():
    st.markdown(f"### {gold_icon('user')} CRM e Fidelidade", unsafe_allow_html=True)
    st.markdown("<p style='font-size:13px; color:var(--text-sec); margin-top:-10px; margin-bottom:20px;'>Gestão de clientes, histórico de visitas e classificação de fidelidade.</p>", unsafe_allow_html=True)
    
    db = next(get_db())
    
    # Novo Cliente
    c1, c2 = st.columns([0.8, 0.2])
    with c2:
        if st.button("+ Novo Cliente", type="primary", use_container_width=True):
            dialog_novo_cliente()
            
    # Filtros
    st.markdown("<div style='font-size:12px; font-weight:600; color:#555; margin-bottom:5px;'>Filtros de Busca</div>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns([0.4, 0.3, 0.3])
    busca_nome = f1.text_input("Buscar", placeholder="Nome ou Placa", label_visibility="collapsed")
    filtro_selo = f2.selectbox("Selo", ["Todos", "💎 Diamante", "🥇 Ouro", "🥈 Prata", "N/A"], label_visibility="collapsed")
    
    # Dados
    clientes = db.query(Cliente).all()
    todas_oss = db.query(Atendimento).filter(Atendimento.status == "Finalizado").all()
    
    oss_por_cliente = {}
    for os_obj in todas_oss:
        if os_obj.cliente_id not in oss_por_cliente:
            oss_por_cliente[os_obj.cliente_id] = []
        oss_por_cliente[os_obj.cliente_id].append(os_obj)
        
    dados_crm = []
    
    for c in clientes:
        if busca_nome:
            b = busca_nome.lower()
            nome_c = (c.nome or "").lower()
            placa_c = (c.placa_veiculo or "").lower()
            if b not in nome_c and b not in placa_c:
                continue
                
        oss = oss_por_cliente.get(c.id, [])
        gasto_total = sum(os.valor_total for os in oss)
        qtd = len(oss)
        selo = get_selo(gasto_total)
        
        if filtro_selo != "Todos" and selo != filtro_selo:
            continue
            
        ultima_visita = "-"
        if oss:
            ultima_os = sorted(oss, key=lambda x: x.data_criacao, reverse=True)[0]
            try:
                ultima_visita = datetime.fromisoformat(ultima_os.data_criacao).strftime("%d/%m/%Y")
            except:
                ultima_visita = ultima_os.data_criacao[:10]
                
        dados_crm.append({
            "id": c.id,
            "Nome": c.nome or "-",
            "Celular": c.telefone or "-",
            "Veículo": c.modelo_veiculo or "-",
            "Placa": c.placa_veiculo or "-",
            "Gasto Total": gasto_total,
            "Qtd OS": qtd,
            "Última Visita": ultima_visita,
            "Selo": selo
        })
        
    df = pd.DataFrame(dados_crm)
    
    with f3:
        if not df.empty:
            df_export = df.drop(columns=["id"])
            csv = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar Excel",
                data=csv,
                file_name=f"CRM_Export_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
    st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
    
    if df.empty:
        st.info("Nenhum cliente encontrado.")
        return
        
    df = df.sort_values(by="Gasto Total", ascending=False)
    
    # Cabeçalho da tabela
    st.markdown("""
    <div style='display:grid; grid-template-columns: 2fr 1.5fr 1.5fr 1fr 1.2fr 0.8fr 1.2fr 1fr 1fr; gap:10px; padding:10px 15px; background:#f4f6f8; border-radius:6px; font-size:11px; font-weight:700; color:#555; text-transform:uppercase; margin-bottom:10px;'>
        <div>Nome</div>
        <div>Celular</div>
        <div>Veículo</div>
        <div>Placa</div>
        <div>Gasto Total</div>
        <div>Qtd</div>
        <div>Última Visita</div>
        <div>Selo</div>
        <div style='text-align:center;'>Ações</div>
    </div>
    """, unsafe_allow_html=True)
    
    for _, row in df.iterrows():
        c_id = row['id']
        gasto_f = f"R$ {row['Gasto Total']:,.2f}"
        
        selo_color = "#555"
        selo_bg = "transparent"
        if "Diamante" in row['Selo']:
            selo_color = "#2980b9"
            selo_bg = "#ebf5fb"
        elif "Ouro" in row['Selo']:
            selo_color = "#d4ac0d"
            selo_bg = "#fef9e7"
        elif "Prata" in row['Selo']:
            selo_color = "#7f8c8d"
            selo_bg = "#f2f4f4"
            
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([2, 1.5, 1.5, 1, 1.2, 0.8, 1.2, 1, 1])
        
        with col1: st.markdown(f"<div style='font-size:13px; font-weight:600; margin-top:8px;'>{row['Nome']}</div>", unsafe_allow_html=True)
        with col2: st.markdown(f"<div style='font-size:12px; color:#555; margin-top:8px;'>{row['Celular']}</div>", unsafe_allow_html=True)
        with col3: st.markdown(f"<div style='font-size:12px; color:#555; margin-top:8px;'>{row['Veículo']}</div>", unsafe_allow_html=True)
        with col4: st.markdown(f"<div style='font-size:12px; font-weight:600; color:#444; margin-top:8px;'>{row['Placa']}</div>", unsafe_allow_html=True)
        with col5: st.markdown(f"<div style='font-size:13px; font-weight:700; color:var(--accent); margin-top:8px;'>{gasto_f}</div>", unsafe_allow_html=True)
        with col6: st.markdown(f"<div style='font-size:12px; color:#555; margin-top:8px;'>{row['Qtd OS']} un</div>", unsafe_allow_html=True)
        with col7: st.markdown(f"<div style='font-size:12px; color:#555; margin-top:8px;'>{row['Última Visita']}</div>", unsafe_allow_html=True)
        with col8: st.markdown(f"<div style='font-size:11px; font-weight:700; color:{selo_color}; background:{selo_bg}; padding:2px 6px; border-radius:10px; display:inline-block; margin-top:8px;'>{row['Selo']}</div>", unsafe_allow_html=True)
        
        with col9:
            b1, b2 = st.columns(2)
            with b1:
                if st.button("✏️", key=f"edit_crm_{c_id}", help="Editar Cliente"):
                    dialog_editar_cliente(c_id)
            with b2:
                if st.button("🗑️", key=f"del_crm_{c_id}", help="Excluir Cliente"):
                    dialog_excluir_cliente(c_id)
                    
        st.markdown("<hr style='margin:4px 0; border-color:rgba(0,0,0,0.03);'>", unsafe_allow_html=True)
