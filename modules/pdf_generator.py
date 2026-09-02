
def formatar_moeda(valor):
    try:
        return f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return '0,00'

import os
from fpdf import FPDF
from datetime import datetime

class ReciboPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 14)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, 'RECIBO DE PAGAMENTO', ln=True, align='C')
        self.set_font('helvetica', '', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'COMPROVANTE DE PRESTAÇÃO DE SERVIÇOS', ln=True, align='C')
        self.ln(5)
        
def gerar_recibo_pdf(recibo, colaborador):
    # Proporção 9:16 approx (Mobile-First): Width 90mm, Height 160mm
    pdf = ReciboPDF(orientation='P', unit='mm', format=(108, 192))
    pdf.add_page()
    
    # Detalhes do Colaborador
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, f"Colaborador: {colaborador.nome}", ln=True)
    pdf.set_font('helvetica', '', 10)
    pdf.cell(0, 5, f"Cargo: {colaborador.cargo or 'N/I'}", ln=True)
    try:
        dt_ini = datetime.fromisoformat(str(recibo.data_inicial)).strftime('%d/%m/%Y')
        dt_fim = datetime.fromisoformat(str(recibo.data_final)).strftime('%d/%m/%Y')
    except:
        dt_ini = str(recibo.data_inicial)[:10]
        dt_fim = str(recibo.data_final)[:10]
    pdf.cell(0, 5, f"Período: {dt_ini} a {dt_fim}", ln=True)
    pdf.cell(0, 5, f"Dias Trabalhados: {recibo.dias_trabalhados}", ln=True)
    
    pdf.ln(5)
    
    # Headers da Tabela
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(42, 7, 'Descrição', border=1, fill=True)
    pdf.cell(23, 7, 'Proventos', border=1, align='R', fill=True)
    pdf.cell(23, 7, 'Descontos', border=1, align='R', fill=True)
    pdf.ln(7)
    
    pdf.set_font('helvetica', '', 9)
    
    def linha_valor(desc, prov=0.0, desc_val=0.0):
        pdf.cell(42, 6, desc, border=1)
        prov_str = f"{formatar_moeda(prov)}".replace(",", "X").replace(".", ",").replace("X", ".") if prov > 0 else "-"
        desc_str = f"{formatar_moeda(desc_val)}".replace(",", "X").replace(".", ",").replace("X", ".") if desc_val > 0 else "-"
        pdf.cell(23, 6, prov_str, border=1, align='R')
        pdf.cell(23, 6, desc_str, border=1, align='R')
        pdf.ln(6)
        
    linha_valor('Salário Proporcional', prov=recibo.salario_proporcional)
    linha_valor('Alimentação', prov=recibo.total_alimentacao)
    linha_valor('Transporte', prov=recibo.total_transporte)
    if recibo.total_comissoes > 0:
        linha_valor('Comissões', prov=recibo.total_comissoes)
    if recibo.bonus > 0:
        linha_valor('Bônus Extra', prov=recibo.bonus)
        
    if recibo.desconto_adiantamentos > 0:
        linha_valor('Vales / Retiradas', desc_val=recibo.desconto_adiantamentos)
    if recibo.outros_descontos > 0:
        linha_valor('Outros Descontos', desc_val=recibo.outros_descontos)
        
    pdf.ln(3)
    
    # Totais
    total_prov = recibo.salario_proporcional + recibo.total_alimentacao + recibo.total_transporte + recibo.total_comissoes + recibo.bonus
    total_desc = recibo.desconto_adiantamentos + recibo.outros_descontos
    
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(42, 7, 'TOTAIS', border=1, fill=True)
    prov_total_str = f"R$ {formatar_moeda(total_prov)}".replace(",", "X").replace(".", ",").replace("X", ".")
    desc_total_str = f"R$ {formatar_moeda(total_desc)}".replace(",", "X").replace(".", ",").replace("X", ".")
    pdf.cell(23, 7, prov_total_str, border=1, align='R', fill=True)
    pdf.cell(23, 7, desc_total_str, border=1, align='R', fill=True)
    pdf.ln(10)
    
    # Líquido
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_fill_color(220, 240, 220)
    liq_str = f"R$ {formatar_moeda(recibo.valor_liquido)}".replace(",", "X").replace(".", ",").replace("X", ".")
    pdf.cell(0, 10, f"LÍQUIDO A RECEBER: {liq_str}", border=1, align='C', fill=True)
    
    pdf.ln(15)
    pdf.set_font('helvetica', '', 8)
    pdf.cell(0, 5, '_________________________________________________', ln=True, align='C')
    pdf.cell(0, 5, f"Assinatura: {colaborador.nome}", ln=True, align='C')
    try:
        dt_gen = datetime.fromisoformat(str(recibo.data_geracao)).strftime('%d/%m/%Y')
    except:
        dt_gen = str(recibo.data_geracao)[:10]
    pdf.cell(0, 5, f"Data: {dt_gen}", ln=True, align='C')
    
    os.makedirs("temp_pdfs", exist_ok=True)
    path = f"temp_pdfs/recibo_{recibo.id}.pdf"
    pdf.output(path)
    return path
