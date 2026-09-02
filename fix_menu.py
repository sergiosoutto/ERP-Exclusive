import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the old static menu_options definition
old_pattern = r'menu_options = \[\s*"Fluxo do [Dd]ia".*?\]'
new_code = """        all_menu_options = [
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

content = re.sub(old_pattern, new_code, content, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed menu logic')
