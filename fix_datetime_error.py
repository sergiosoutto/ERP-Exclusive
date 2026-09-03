import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add time to imports
if "from datetime import datetime, timedelta, timezone, time" not in content:
    content = content.replace("from datetime import datetime, timedelta, timezone", "from datetime import datetime, timedelta, timezone, time")

# 1. Remove local import datetime and fix time(9, 0)
old_hora1 = """                    import datetime
                    hora_agendamento = st.time_input("Hora", value=datetime.time(9, 0))"""
new_hora1 = """                    hora_agendamento = st.time_input("Hora", value=time(9, 0))"""
content = content.replace(old_hora1, new_hora1)

# 2. Fix the reagendar time input
old_hora2 = """    import datetime
    nova_hora = st.time_input("Nova Hora", value=datetime.time(9, 0))"""
new_hora2 = """    nova_hora = st.time_input("Nova Hora", value=time(9, 0))"""
content = content.replace(old_hora2, new_hora2)

# 3. Fix the Agenda tab parsing where I did `import datetime` again
old_agenda_parse = """                    try:
                        # PODE ESTAR EM YYYY-MM-DD ou YYYY-MM-DD HH:MM
                        import datetime
                        if " " in at.data_agendamento:
                            dt_str = datetime.datetime.strptime(at.data_agendamento, "%Y-%m-%d %H:%M").strftime('%d/%m/%Y às %H:%M')
                        else:
                            dt_obj = datetime.datetime.fromisoformat(at.data_agendamento)
                            dt_str = dt_obj.strftime('%d/%m/%Y')
                    except Exception as e:"""
                    
new_agenda_parse = """                    try:
                        # PODE ESTAR EM YYYY-MM-DD ou YYYY-MM-DD HH:MM
                        if " " in at.data_agendamento:
                            dt_str = datetime.strptime(at.data_agendamento, "%Y-%m-%d %H:%M").strftime('%d/%m/%Y às %H:%M')
                        else:
                            dt_obj = datetime.fromisoformat(at.data_agendamento)
                            dt_str = dt_obj.strftime('%d/%m/%Y')
                    except Exception as e:"""
content = content.replace(old_agenda_parse, new_agenda_parse)

with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Removed local datetime imports causing UnboundLocalError")
