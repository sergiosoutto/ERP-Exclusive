import streamlit as st
from db_config import get_db, Colaborador
from modules.fast_launch import gold_icon, dialog_decorator

@dialog_decorator("Cadastrar Novo Colaborador")
def dialog_novo_colaborador():
    db = next(get_db())
    nome = st.text_input("Nome do Colaborador")
    cargo = st.text_input("Cargo / Função")
    telefone = st.text_input("Telefone")
    
    if st.button("Salvar Colaborador", type="primary", use_container_width=True):
        if not nome:
            st.error("Preencha o nome.")
            return
        c = Colaborador(nome=nome, cargo=cargo, telefone=telefone)
        db.add(c)
        db.commit()
        st.success("✅ Colaborador cadastrado!")
        st.rerun()

def render_personnel():
    st.markdown(f"### {gold_icon('people')} Gestão de Pessoal", unsafe_allow_html=True)
    st.markdown("<p style='font-size:13px; color:var(--text-sec); margin-top:-10px; margin-bottom:20px;'>Gerencie seus colaboradores, mecânicos e equipe administrativa.</p>", unsafe_allow_html=True)
    
    db = next(get_db())
    col_t1, col_t2 = st.columns([0.8, 0.2])
    with col_t2:
        if st.button("+ Novo Colaborador", use_container_width=True, type="primary"): dialog_novo_colaborador()
            
    st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
    colabs = db.query(Colaborador).all()
    if colabs:
        for c in colabs:
            with st.expander(f"{c.nome} - {c.cargo or 'Sem cargo'}"):
                c1, c2, c3 = st.columns([2,2,1])
                with c1: st.write(f"**Telefone:** {c.telefone or 'N/I'}")
                with c2: st.write(f"**Status:** {'Ativo' if c.ativo else 'Inativo'}")
                with c3:
                    if st.button("Excluir", key=f"del_colab_{c.id}", type="primary"):
                        db.delete(c)
                        db.commit()
                        st.rerun()
    else:
        st.info("Nenhum colaborador cadastrado.")
