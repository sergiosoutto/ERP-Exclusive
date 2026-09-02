import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update login to store permissions
login_replacement = """                st.session_state['logged_in'] = True
                st.session_state['username'] = user.username
                st.session_state['user_role'] = user.role
                st.session_state['permissoes'] = user.permissoes
                st.session_state['pode_excluir'] = user.pode_excluir or user.role == "admin"
                from db_config import registrar_log
                registrar_log("Fez login no sistema")
                st.rerun()"""

content = re.sub(r'st\.session_state\[\'logged_in\'\] = True\s*st\.session_state\[\'user_role\'\] = user\.role\s*st\.rerun\(\)', login_replacement, content)

# 2. Add logout to sidebar just to be safe (or it might be there)
if "Logout" not in content and "Sair" not in content:
    logout_btn = """
        if st.button("Sair / Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
"""
    content = content.replace("st.markdown(\"<hr style='margin: 10px 0;'>\", unsafe_allow_html=True)", "st.markdown(\"<hr style='margin: 10px 0;'>\", unsafe_allow_html=True)\n" + logout_btn)


# 3. Filter menus
menu_def_old = """        menu_options = [
            "Fluxo do Dia",
            "Transações",
            "Gestão Financeira",
            "Estoque & Insumos",
            "Gestão de Pessoal",
            "CRM & Fidelidade",
            "Cadastros",
            "Central Analítica"
        ]"""
        
menu_def_new = """        all_menu_options = [
            "Fluxo do Dia",
            "Transações",
            "Gestão Financeira",
            "Estoque & Insumos",
            "Gestão de Pessoal",
            "CRM & Fidelidade",
            "Cadastros",
            "Central Analítica"
        ]
        
        # Filtrar menus baseados nas permissões
        user_perms = st.session_state.get('permissoes', 'todas')
        if user_perms == "todas" or st.session_state.get('user_role') == 'admin':
            menu_options = all_menu_options
        else:
            perms_list = user_perms.split(",")
            # Mapeamento de nomes para garantir que combinam (tradução caso necessário)
            # Como salvamos com os mesmos nomes (Estoque, CRM, etc), podemos filtrar direto
            # Mas vamos tratar casos especiais
            map_perms = {
                "Fluxo do Dia": ["Fluxo do Dia", "Transações"],
                "Financeiro": ["Gestão Financeira"],
                "Estoque": ["Estoque & Insumos"],
                "Gestão de Pessoal": ["Gestão de Pessoal"],
                "CRM": ["CRM & Fidelidade"],
                "Cadastros": ["Cadastros", "Central Analítica"]
            }
            menu_options = []
            for k, v_list in map_perms.items():
                if k in perms_list:
                    menu_options.extend(v_list)"""

if "all_menu_options" not in content:
    content = content.replace(menu_def_old, menu_def_new)
    
# Remove Transacoes from map if not needed, but wait, map_perms adds both.
# Fix icons
icons_def_old = """        icons = [
            "cart-plus", "arrow-left-right", "wallet2",
            "box-seam", "people", "person-badge", "database-add", 
            "bar-chart-line"
        ]"""

icons_def_new = """        # Icons matching the final menu_options list
        all_icons = {
            "Fluxo do Dia": "cart-plus",
            "Transações": "arrow-left-right",
            "Gestão Financeira": "wallet2",
            "Estoque & Insumos": "box-seam",
            "Gestão de Pessoal": "people",
            "CRM & Fidelidade": "person-badge",
            "Cadastros": "database-add",
            "Central Analítica": "bar-chart-line"
        }
        icons = [all_icons[m] for m in menu_options]"""
        
if "all_icons = {" not in content:
    content = content.replace(icons_def_old, icons_def_new)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated app.py with permissions logic")
