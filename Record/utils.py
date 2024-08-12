from io import BytesIO

def gerar_analise_e_pdf(texto):
    buffer = BytesIO()
    # Aqui você adicionaria o código para criar o PDF e escrever no buffer
    # Exemplo com ReportLab
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, texto)
    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer
