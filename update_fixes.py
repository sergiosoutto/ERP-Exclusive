import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. success_msg to st.toast
old_success = """    if st.session_state['success_msg']:
        st.success(st.session_state['success_msg'])
        if st.button("OK", use_container_width=True):
            st.session_state['success_msg'] = None
            st.rerun()"""

new_success = """    if st.session_state['success_msg']:
        st.toast(st.session_state['success_msg'], icon='✅')
        st.session_state['success_msg'] = None"""
content = content.replace(old_success, new_success)

# Replace any other st.success after st.session_state['success_msg'] sets if they exist? No, they all use the global handler.
# Wait, dialog_novo_cliente has: `st.success(f"Cliente cadastrado com sucesso!")`
# I'll replace it with st.session_state['success_msg']
old_cli_success = '            st.success(f"Cliente cadastrado com sucesso!")'
new_cli_success = '            st.session_state["success_msg"] = "Cliente cadastrado com sucesso!"\n            st.session_state["novo_cliente_codigo"] = codigo_seq'
content = content.replace(old_cli_success, new_cli_success)


# 2. Block duplicate client
duplicate_check = """
    if st.button("Salvar Cliente", type="primary", use_container_width=True):
        if novo_nome:
            tel_formatado = formatar_telefone(novo_tel_num)
            
            if nova_placa and tel_formatado:
                existe = db.query(Cliente).filter(Cliente.placa_veiculo == nova_placa, Cliente.telefone == tel_formatado).first()
                if existe:
                    st.toast("Erro: Cliente já existe com esta placa e telefone!", icon='🚫')
                    return
            
            novo_cliente = Cliente("""

content = content.replace("""    if st.button("Salvar Cliente", type="primary", use_container_width=True):
        if novo_nome:
            tel_formatado = formatar_telefone(novo_tel_num)
            novo_cliente = Cliente(""", duplicate_check)


# 3. Pre-select client
old_index = '            index_sel = 1 if len(cliente_opcoes) == 2 else 0'
new_index = """            index_sel = 1 if len(cliente_opcoes) == 2 else 0
            if 'novo_cliente_codigo' in st.session_state:
                for idx, op in enumerate(cliente_opcoes):
                    if op.startswith(st.session_state['novo_cliente_codigo']):
                        index_sel = idx
                        break
                # Only use once
                del st.session_state['novo_cliente_codigo']"""
content = content.replace(old_index, new_index)


# 4. Add Car model to Histórico
hist_card_old = """                    <div style='display: flex; justify-content: space-between; align-items: center; margin: -5px 0;'>
                        <div>
                            <span style='font-size:13px; font-weight:600;'>{cli.nome if cli else 'Desconhecido'}</span> 
                            <span style='font-size:11px; color:#888;'>({at.codigo})</span><br>
                            <span style='font-size:11px; color:#555;'>{gold_icon('check')} {dt_str} | {at.forma_pagamento}</span>
                        </div>"""

hist_card_new = """                    <div style='display: flex; justify-content: space-between; align-items: center; margin: -5px 0;'>
                        <div>
                            <span style='font-size:13px; font-weight:600;'>{cli.nome if cli else 'Desconhecido'}</span> 
                            <span style='font-size:11px; color:#888;'>({at.codigo})</span><br>
                            <span style='font-size:11px; color:#888;'>*{cli.modelo_veiculo if cli and cli.modelo_veiculo else "Sem Veículo"}*</span><br>
                            <span style='font-size:11px; color:#555;'>{gold_icon('check')} {dt_str} | {at.forma_pagamento}</span>
                        </div>"""

content = content.replace(hist_card_old, hist_card_new)

with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Applied updates!')
