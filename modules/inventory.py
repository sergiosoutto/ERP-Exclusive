import streamlit as st
from db_config import get_db, Produto
from modules.fast_launch import gold_icon, dialog_decorator

@dialog_decorator("Cadastrar Novo Insumo")
def dialog_novo_produto():
    db = next(get_db())
    nome = st.text_input("Nome do Insumo (ex: Shampoo X)")
    custo = st.number_input("Custo Unitário (R$)", min_value=0.0, format="%.4f")
    unidade = st.selectbox("Unidade", ["ml", "g", "L", "Kg", "un", "galão"])
    
    if st.button("Salvar Insumo", type="primary", use_container_width=True):
        if not nome:
            st.error("Preencha o nome do insumo.")
            return
        p = Produto(nome=nome, custo_unidade=custo, unidade_medida=unidade)
        db.add(p)
        db.commit()
        st.success("✅ Insumo cadastrado!")
        st.rerun()

def render_inventory():
    st.markdown(f"### {gold_icon('box-seam')} Estoque & Insumos", unsafe_allow_html=True)
    st.markdown("<p style='font-size:13px; color:var(--text-sec); margin-top:-10px; margin-bottom:20px;'>Gestão de estoque, insumos e custos de uso.</p>", unsafe_allow_html=True)
    
    db = next(get_db())
    col_p1, col_p2 = st.columns([0.8, 0.2])
    with col_p2:
        if st.button("+ Novo Insumo", use_container_width=True, type="primary"): dialog_novo_produto()
            
    st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
    produtos = db.query(Produto).all()
    if produtos:
        for p in produtos:
            with st.expander(f"{p.nome}"):
                p1, p2, p4 = st.columns([1,1,1])
                with p1: st.write(f"**Custo Unitário:** R$ {p.custo_unidade:,.4f}")
                with p2: st.write(f"**Estoque:** {p.quantidade_estoque} {p.unidade_medida}")
                with p4:
                    if st.button("Excluir", key=f"del_prod_{p.id}", type="primary"):
                        db.delete(p)
                        db.commit()
                        st.rerun()
    else:
        st.info("Nenhum insumo cadastrado.")
