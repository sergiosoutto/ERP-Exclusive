import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """        if em_andamento:
            fila = [a for a in em_andamento if a.status in ("Aguardando", "Em Andamento")]
            lavando = [a for a in em_andamento if a.status == "Lavando"]
            prontos = [a for a in em_andamento if a.status == "Pronto"]
            
            def render_os_card(at):
                cli = clientes_map.get(at.cliente_id)
                itens_at = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id == at.id).all()
                total_val = sum(i.valor_cobrado for i in itens_at)"""

new_code = """        if em_andamento:
            fila = [a for a in em_andamento if a.status in ("Aguardando", "Em Andamento")]
            lavando = [a for a in em_andamento if a.status == "Lavando"]
            prontos = [a for a in em_andamento if a.status == "Pronto"]
            
            at_ids = [a.id for a in em_andamento]
            todos_itens = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id.in_(at_ids)).all() if at_ids else []
            itens_map = {}
            for item in todos_itens:
                itens_map.setdefault(item.atendimento_id, []).append(item)
            
            def render_os_card(at):
                cli = clientes_map.get(at.cliente_id)
                itens_at = itens_map.get(at.id, [])
                total_val = sum(i.valor_cobrado for i in itens_at)"""

content = content.replace(old_code, new_code)

with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed N+1 queries in Patio")
