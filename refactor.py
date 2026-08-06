import sys

with open('modules/financial.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
in_tab1 = False

i = 0
while i < len(lines):
    line = lines[i]
    
    if "@dialog_decorator(\"Nova Transferência Interna\")" in line:
        skip = True
    
    if skip and "def render_financial():" in line:
        skip = False
        
    if "tab1, tab2, tab3, tab4 = st.tabs([" in line:
        # Pula as definições de tabs
        while i < len(lines) and "])" not in lines[i]:
            i += 1
        i += 1
        continue
        
    if "with tab1:" in line:
        in_tab1 = True
        i += 1
        continue
        
    if "with tab2:" in line or "with tab3:" in line or "with tab4:" in line:
        in_tab1 = False
        skip = True
        
    if not skip:
        if in_tab1:
            # unindent by 4 spaces
            if line.startswith("    "):
                new_lines.append(line[4:])
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    i += 1

with open('modules/financial.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
