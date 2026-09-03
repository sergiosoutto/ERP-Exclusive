import re

with open('modules/cadastros.py', 'r', encoding='utf-8') as f:
    content = f.read()

if "registrar_log" not in content:
    content = content.replace("from db_config import get_db, Cliente, Servico, Produto, Usuario", "from db_config import get_db, Cliente, Servico, Produto, Usuario, registrar_log")
    
# Cliente creation
content = content.replace(
    'st.success(f"Cliente {nome} cadastrado!")',
    'registrar_log(f"Cadastrou o cliente: {nome}")\n                st.success(f"Cliente {nome} cadastrado!")'
)

# Cliente deletion
content = content.replace(
    'st.success("Cliente e registros dependentes removidos!")',
    'registrar_log(f"Excluiu o cliente ID {c_id}")\n                st.success("Cliente e registros dependentes removidos!")'
)

# Cliente update
content = content.replace(
    'st.success("Cliente atualizado!")',
    'registrar_log(f"Editou o cliente: {novo_nome}")\n                        st.success("Cliente atualizado!")'
)

with open('modules/cadastros.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Applied Cadastros Updates')
