import os, re
import glob

helper = '''
def formatar_moeda(valor):
    try:
        return f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return '0,00'
'''

def replace_moeda(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip files that already have the helper
    if 'def formatar_moeda' not in content and '{' in content and ':,.' in content:
        # Just put it after imports or at the top
        content = helper + '\n' + content
        
    original = content
    content = re.sub(r'\{([a-zA-Z0-9_]+):,\.2f\}', r'{formatar_moeda(\1)}', content)
    content = re.sub(r'\{([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+):,\.2f\}', r'{formatar_moeda(\1)}', content)
    content = re.sub(r'\{abs\(([a-zA-Z0-9_]+)\):,\.2f\}', r'{formatar_moeda(abs(\1))}', content)
    content = re.sub(r'\{([a-zA-Z0-9_]+ - [a-zA-Z0-9_]+\.[a-zA-Z0-9_]+):,\.2f\}', r'{formatar_moeda(\1)}', content)
    
    # Catch array indexing row['Gasto Total']
    content = re.sub(r'\{row\[\'([a-zA-Z0-9_ ]+)\'\]:,\.2f\}', r'{formatar_moeda(row[\'\1\'])}', content)
    
    if original != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

for root, _, files in os.walk('modules'):
    for f in files:
        if f.endswith('.py'):
            replace_moeda(os.path.join(root, f))
print('Done formatar_moeda across all files')
