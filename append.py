with open('modules/cadastros.py', 'a', encoding='utf-8') as f:
    f.write('''
    # --- TAB 8: METAS ---
    with t_meta:
        col_m1, col_m2 = st.columns([4, 1])
        with col_m1: st.markdown(f"### {gold_icon('graph-up')} Gestão de Metas", unsafe_allow_html=True)
        with col_m2:
            if st.button("+ Nova Meta", use_container_width=True, type="primary"): dialog_nova_meta()
        st.markdown("---")
        metas = db.query(MetaApp).order_by(MetaApp.data_inicial.desc()).all()
        if metas:
            for m in metas:
                with st.expander(f"{m.descricao} (R$ {m.valor:,.2f})"):
                    st.write(f"**Período:** {m.data_inicial.strftime('%d/%m/%Y')} a {m.data_final.strftime('%d/%m/%Y')}")
                    if st.button("Excluir", key=f"del_meta_{m.id}", type="primary"):
                        db.delete(m)
                        db.commit()
                        st.rerun()
        else:
            st.info("Nenhuma meta cadastrada.")
''')
