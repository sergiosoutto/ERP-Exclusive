import os

def fix_helper(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    bad_helper = 'return f"{formatar_moeda(valor)}".replace('
    good_helper = 'return f"{valor:,.2f}".replace('
    
    if bad_helper in content:
        content = content.replace(bad_helper, good_helper)
        
    # Add datetime import to cadastros.py if not there
    if "cadastros.py" in filepath and "from datetime import datetime" not in content:
        content = content.replace("import streamlit as st", "import streamlit as st\nfrom datetime import datetime")
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for root, _, files in os.walk('modules'):
    for f in files:
        if f.endswith('.py'):
            fix_helper(os.path.join(root, f))
print('Fixed recursion error and added datetime import')
