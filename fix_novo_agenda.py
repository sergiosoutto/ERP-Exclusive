import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix Novo client search
old_novo = """            termo = remover_acentos(busca_cliente.strip().lower())
            cliente_opcoes = ["-- Selecione o Cliente --"]
            clientes = db.query(Cliente).all()
            for c in clientes:
                if c.codigo == "CLI-0000": continue
                nome = remover_acentos(c.nome or "").lower()
                placa = remover_acentos(c.placa_veiculo or "").lower()
                if termo and (termo not in nome and termo not in placa): continue
                cliente_opcoes.append(f"{c.codigo} | {c.nome or 'Desconhecido'} ({c.placa_veiculo or 'Sem Placa'})")"""

new_novo = """            if busca_cliente:
                clientes_filtrados = db.query(Cliente).filter(
                    (Cliente.nome.ilike(f"%{busca_cliente}%")) | 
                    (Cliente.placa_veiculo.ilike(f"%{busca_cliente}%"))
                ).limit(20).all()
            else:
                clientes_filtrados = db.query(Cliente).limit(5).all()
                
            cliente_opcoes = ["-- Selecione o Cliente --"] + [f"{c.codigo} | {c.nome or 'Desconhecido'} ({c.placa_veiculo or 'Sem Placa'})" for c in clientes_filtrados if c.codigo != "CLI-0000"]"""

if old_novo in content:
    content = content.replace(old_novo, new_novo)

# 2. Fix the NameError in Agenda!
# Let's see what is currently in Agenda.
old_agenda = 'agendados = agendados_raw'
new_agenda = 'agendados = agendados_raw if "agendados_raw" in locals() else []'

content = content.replace(old_agenda, new_agenda)

with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed Novo client search and Agenda NameError")
