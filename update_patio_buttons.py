import re

with open('modules/fast_launch.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """                    # Ações Dinâmicas por Status
                    if at.status in ("Aguardando", "Em Andamento"):
                        if st.button(f" Iniciar Lavagem", key=f"btn_ini_{at.id}", type="primary", use_container_width=True):
                            at.status = "Lavando"
                            at.data_inicio = obter_hora_local().isoformat()
                            db.commit()
                            st.toast(f"OS {at.codigo} em execução!")
                            st.rerun()
                    elif at.status == "Lavando":
                        if st.button(f" Sinalizar Pronto", key=f"btn_pro_{at.id}", type="primary", use_container_width=True):
                            at.status = "Pronto"
                            at.data_pronto = obter_hora_local().isoformat()
                            db.commit()
                            st.toast(f"OS {at.codigo} concluída! Aguardando entrega.")
                            st.rerun()
                    elif at.status == "Pronto":
                        if st.button(f" Entregar e Receber", key=f"btn_rec_{at.id}", type="primary", use_container_width=True):
                            dialog_checkout(at.id)"""
                            
new_block = """                    # Ações Dinâmicas por Status
                    if at.status in ("Aguardando", "Em Andamento"):
                        if st.button(f" Iniciar Lavagem", key=f"btn_ini_{at.id}", type="primary", use_container_width=True):
                            dialog_iniciar_lavagem(at.id)
                    elif at.status == "Lavando":
                        if st.button(f" Sinalizar Pronto", key=f"btn_pro_{at.id}", type="primary", use_container_width=True):
                            dialog_sinalizar_pronto(at.id)
                    elif at.status == "Pronto":
                        if st.button(f" Entregar e Receber", key=f"btn_rec_{at.id}", type="primary", use_container_width=True):
                            dialog_checkout(at.id)"""
                            
# Remove diacritics for matching because terminal read gives weird output sometimes
import unicodedata
def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

# Create a regex to match the logic blocks irrespective of encoding issues
regex_pattern = r"# A[^e]es Din[^m]micas por Status.*?dialog_checkout\(at\.id\)"

content = re.sub(regex_pattern, new_block, content, flags=re.DOTALL)

with open('modules/fast_launch.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated buttons")
