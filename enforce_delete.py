import re

def hide_delete(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # fast_launch.py
    if 'fast_launch.py' in filepath:
        content = content.replace('options=["Concluir", "Editar", "Excluir"],', 'options=["Concluir", "Editar", "Excluir"] if st.session_state.get("pode_excluir", False) else ["Concluir", "Editar"],')
        content = content.replace('if st.button("Excluir", key=f"hist_del_{at.id}"):', 'if st.session_state.get("pode_excluir", False) and st.button("Excluir", key=f"hist_del_{at.id}"):')
    
    # crm.py
    if 'crm.py' in filepath:
        content = content.replace('if st.button("Excluir", key=f"del_cli_{c.id}", type="primary"):', 'if st.session_state.get("pode_excluir", False) and st.button("Excluir", key=f"del_cli_{c.id}", type="primary"):')
        
    # inventory.py
    if 'inventory.py' in filepath:
        content = content.replace('if st.button("Excluir", key=f"del_prod_{p.id}", type="primary"):', 'if st.session_state.get("pode_excluir", False) and st.button("Excluir", key=f"del_prod_{p.id}", type="primary"):')

    # cadastros.py
    if 'cadastros.py' in filepath:
        content = content.replace('if st.button(f"Excluir {cat.nome}", key=f"excluir_cat_{cat.id}"):', 'if st.session_state.get("pode_excluir", False) and st.button(f"Excluir {cat.nome}", key=f"excluir_cat_{cat.id}"):')
        content = content.replace('if st.button("Excluir", key=f"excluir_sub_{s.id}"):', 'if st.session_state.get("pode_excluir", False) and st.button("Excluir", key=f"excluir_sub_{s.id}"):')
        content = content.replace('if st.button("Excluir", key=f"del_banco_{c.id}", type="primary"):', 'if st.session_state.get("pode_excluir", False) and st.button("Excluir", key=f"del_banco_{c.id}", type="primary"):')
        content = content.replace('if st.button("Excluir", key=f"del_meta_{m.id}", type="primary"):', 'if st.session_state.get("pode_excluir", False) and st.button("Excluir", key=f"del_meta_{m.id}", type="primary"):')
        content = content.replace('if st.button("Excluir", key=f"del_serv_{s.id}", type="primary"):', 'if st.session_state.get("pode_excluir", False) and st.button("Excluir", key=f"del_serv_{s.id}", type="primary"):')
        content = content.replace('if st.button("Excluir", key=f"del_fp_{f.id}", type="primary"):', 'if st.session_state.get("pode_excluir", False) and st.button("Excluir", key=f"del_fp_{f.id}", type="primary"):')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

import os
for root, _, files in os.walk('modules'):
    for f in files:
        if f.endswith('.py'):
            hide_delete(os.path.join(root, f))
print('Applied pode_excluir to all modules')
