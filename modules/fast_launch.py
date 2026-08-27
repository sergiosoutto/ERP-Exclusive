import streamlit as st
from db_config import get_db, Cliente, Servico, Produto, Atendimento, ItemAtendimento, FormaPagamento, ServicoInsumo
from datetime import datetime, timedelta, timezone
import unicodedata

# Helper para remover acentuação de strings
def remover_acentos(texto):
    if not texto: return ""
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

dialog_decorator = st.dialog if hasattr(st, "dialog") else st.experimental_dialog

def obter_hora_local():
    fuso_brasil = timezone(timedelta(hours=-3))
    return datetime.now(fuso_brasil).replace(tzinfo=None)

def formatar_telefone(tel_str):
    digitos = "".join([c for c in tel_str if c.isdigit()])
    if len(digitos) == 11: return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    elif len(digitos) == 10: return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    return tel_str

def gold_icon(icon_name):
    icons = {
        "user": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>',
        "service": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path></svg>',
        "payment": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect><line x1="1" y1="10" x2="23" y2="10"></line></svg>',
        "lightning": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:6px;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>',
        "check": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:4px;"><polyline points="20 6 9 17 4 12"></polyline></svg>',
        "clock": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C5A059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:middle; margin-right:4px;"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>'
    }
    return icons.get(icon_name, "")


@dialog_decorator("Cadastrar Novo Cliente")
def dialog_novo_cliente():
    db = next(get_db())
    qtd = db.query(Cliente).count()
    codigo_seq = f"CLI-{qtd+1:04d}"
    
    st.info(f"Código: **{codigo_seq}**")
    novo_nome = st.text_input("Nome do Cliente")
    novo_tel_num = st.text_input("Telefone com DDD", placeholder="61999999999")
    nova_placa = st.text_input("Placa do Veículo")
    novo_modelo = st.text_input("Modelo do Veículo")
    
    if st.button("Salvar Cliente", type="primary", use_container_width=True):
        if novo_nome:
            tel_formatado = formatar_telefone(novo_tel_num)
            novo_cliente = Cliente(
                codigo=codigo_seq, 
                nome=novo_nome, 
                telefone=tel_formatado, 
                placa_veiculo=nova_placa,
                modelo_veiculo=novo_modelo
            )
            db.add(novo_cliente)
            db.commit()
            st.success(f"Cliente cadastrado com sucesso!")
            st.rerun()

@dialog_decorator("Checkout e Finalização")
def dialog_checkout(at_id):
    db = next(get_db())
    at = db.query(Atendimento).filter(Atendimento.id == at_id).first()
    if not at: return
    
    st.write(f"Finalizando OS: **{at.codigo}**")
    
    # Formas de pagamento do DB
    fps = db.query(FormaPagamento).all()
    fp_nomes = [f.nome for f in fps]
    
    fp_selecionada = st.selectbox("Forma de Pagamento", fp_nomes)
    forma_obj = next((f for f in fps if f.nome == fp_selecionada), None)
    
    parcelas = 1
    if forma_obj and "Cartão" in forma_obj.nome:
        parcelas = st.number_input("Qtd Parcelas", min_value=1, max_value=12, value=1)
        
    valor_base = at.valor_total
    
    # Calculo Juros
    juros = 0.0
    if forma_obj:
        if parcelas == 1:
            juros = valor_base * (forma_obj.taxa_juros_vista / 100)
        else:
            juros = valor_base * (forma_obj.taxa_juros_parcela / 100) * parcelas
            
    valor_final = valor_base + juros
    
    if juros > 0:
        st.write(f"Juros Aplicados: R$ {juros:.2f}")
    st.markdown(f"### Total a Pagar: R$ {valor_final:.2f}")
    
    obs = st.text_input("Observação (Opcional)", placeholder="Ex: Higienização impecável concluída...")
    
    if st.button("Confirmar Pagamento e Baixar Estoque", type="primary", use_container_width=True):
        at.status = "Finalizado"
        at.data_conclusao = obter_hora_local().isoformat()
        at.observacoes = obs
        at.forma_pagamento = fp_selecionada
        at.parcelas = parcelas
        at.valor_total = valor_final # Atualiza valor final
        
        # Baixa de Insumos
        itens = db.query(ItemAtendimento).filter(ItemAtendimento.atendimento_id == at.id).all()
        for i in itens:
            if i.tipo == "Serviço":
                # Acha os insumos do servico
                s_insumos = db.query(ServicoInsumo).filter(ServicoInsumo.servico_id == i.referencia_id).all()
                for si in s_insumos:
                    prod = db.query(Produto).filter(Produto.id == si.produto_id).first()
                    if prod:
                        prod.quantidade_estoque -= si.quantidade_utilizada
                        
        db.commit()
        
        try:
            from modules.financial import registrar_receita_pdv
            registrar_receita_pdv(at.id, db)
        except Exception as e: pass
        
        st.session_state['success_msg'] = f"Venda Finalizada! Baixa de insumos concluída."
        st.rerun()

def render_fast_launch():
    if 'success_msg' not in st.session_state:
        st.session_state['success_msg'] = None
        
    if st.session_state['success_msg']:
        st.success(st.session_state['success_msg'])
        if st.button("OK", use_container_width=True):
            st.session_state['success_msg'] = None
            st.rerun()

    st.markdown(f"<h2 style='margin:0; padding:0; font-size: 24px; text-align:center;'>{gold_icon('lightning')} PDV Serviços</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    db = next(get_db())
    clientes = db.query(Cliente).all()
    servicos = db.query(Servico).all()
    
    tab1, tab2, tab3 = st.tabs(["Novo", "Pátio", "Histórico"])
    
    # ==========================================
    # ABA 1: NOVO ATENDIMENTO
    # ==========================================
    with tab1:
        with st.container(border=True):
            busca_cliente = st.text_input("🔍 Pesquisar Cliente", placeholder="Nome ou Placa...")
            if st.button("+ Novo Cliente", use_container_width=True): dialog_novo_cliente()
            
            termo = remover_acentos(busca_cliente.strip().lower())
            cliente_opcoes = ["-- Selecione o Cliente --"]
            for c in clientes:
                if c.codigo == "CLI-0000": continue
                nome = remover_acentos(c.nome or "").lower()
                placa = remover_acentos(c.placa_veiculo or "").lower()
                if termo and (termo not in nome and termo not in placa): continue
                cliente_opcoes.append(f"{c.codigo} | {c.nome} ({c.placa_veiculo or 'Sem Placa'})")
            
            index_sel = 1 if len(cliente_opcoes) == 2 else 0
            cliente_selecionado = st.selectbox("Cliente", cliente_opcoes, index=index_sel, label_visibility="collapsed")
            
            st.markdown("<hr style='margin:16px 0;'>", unsafe_allow_html=True)
            
            st.markdown(f"<label style='font-size:13px; font-weight:500;'>{gold_icon('service')} Serviço</label>", unsafe_allow_html=True)
            servico_opcoes = [s.nome for s in servicos]
            item_selecionado = st.selectbox("Serviço Principal", servico_opcoes if servico_opcoes else ["Nenhum serviço"], label_visibility="collapsed")
            
            valor_sugerido = 0.0
            if item_selecionado and item_selecionado != "Nenhum serviço":
                serv = next((s for s in servicos if s.nome == item_selecionado), None)
                valor_sugerido = serv.preco_padrao if serv else 0.0
                
            valor_final = st.number_input("Valor Cobrado (R$)", value=valor_sugerido, min_value=0.0)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("Enviar para o Pátio", type="primary", use_container_width=True):
                if cliente_selecionado and not cliente_selecionado.startswith("--"):
                    cli_codigo = cliente_selecionado.split(" |")[0]
                    cliente_ref = db.query(Cliente).filter(Cliente.codigo == cli_codigo).first()
                    
                    codigo_seq = f"OS-{db.query(Atendimento).count()+1:04d}"
                    novo_at = Atendimento(
                        codigo=codigo_seq, cliente_id=cliente_ref.id, status="Em andamento",
                        valor_total=valor_final, data_criacao=obter_hora_local().isoformat()
                    )
                    db.add(novo_at)
                    db.flush()
                    
                    serv_ref = db.query(Servico).filter(Servico.nome == item_selecionado).first()
                    if serv_ref:
                        db.add(ItemAtendimento(atendimento_id=novo_at.id, tipo="Serviço", referencia_id=serv_ref.id, valor_cobrado=valor_final))
                        
                    db.commit()
                    st.session_state['success_msg'] = f"Serviço enviado ao Pátio!"
                    st.rerun()
                else:
                    st.error("Selecione um cliente.")

    # ==========================================
    # ABA 2: PÁTIO (EM ANDAMENTO)
    # ==========================================
    with tab2:
        andamento = db.query(Atendimento).filter(Atendimento.status == "Em andamento").all()
        if andamento:
            for at in reversed(andamento):
                cli = db.query(Cliente).filter(Cliente.id == at.cliente_id).first()
                cli_nome = cli.nome if cli else "Desconhecido"
                
                with st.container(border=True):
                    st.markdown(f"**{cli_nome}** | OS: {at.codigo}")
                    st.markdown(f"*{gold_icon('clock')} Início: {datetime.fromisoformat(at.data_criacao).strftime('%H:%M')}* | Total: R$ {at.valor_total:.2f}", unsafe_allow_html=True)
                    if st.button("Finalizar e Pagar", key=f"fin_{at.id}", type="primary", use_container_width=True):
                        dialog_checkout(at.id)
        else:
            st.info("Pátio vazio.")

    # ==========================================
    # ABA 3: HISTÓRICO CONCLUÍDOS
    # ==========================================
    with tab3:
        concluidos = db.query(Atendimento).filter(Atendimento.status == "Finalizado").order_by(Atendimento.id.desc()).limit(20).all()
        if concluidos:
            for at in concluidos:
                cli = db.query(Cliente).filter(Cliente.id == at.cliente_id).first()
                with st.container(border=True):
                    st.markdown(f"**{cli.nome if cli else 'Desconhecido'}** | {at.codigo}")
                    st.markdown(f"{gold_icon('check')} *Finalizado: {datetime.fromisoformat(at.data_conclusao).strftime('%d/%m %H:%M') if at.data_conclusao else '-'}*", unsafe_allow_html=True)
                    st.markdown(f"**Pagamento:** {at.forma_pagamento} - R$ {at.valor_total:.2f}")
        else:
            st.info("Nenhum concluído hoje.")
