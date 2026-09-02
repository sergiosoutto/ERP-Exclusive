import re

with open('modules/cadastros.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('value=u.pode_excluir', 'value=getattr(u, "pode_excluir", False)')
content = content.replace("if u.pode_excluir or", "if getattr(u, 'pode_excluir', False) or")

with open('modules/cadastros.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed getattr in cadastros.py')
