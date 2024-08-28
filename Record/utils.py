from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import styles
from reportlab.platypus import Paragraph, SimpleDocTemplate

def gerar_analise_e_pdf(texto):
    buffer = BytesIO()

    # Substituir * por uma nova linha
    texto = texto.replace('*', '\n\n')

    # Criar o documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []

    # Estilo de parágrafo justificado
    estilo_normal = styles.getSampleStyleSheet()['Normal']
    estilo_normal.alignment = 4  # Justifica o texto

    # Quebrar o texto em parágrafos e adicionar ao documento
    paragrafos = texto.split('\n\n')
    for paragrafo in paragrafos:
        p = Paragraph(paragrafo, estilo_normal)
        story.append(p)

    # Construir o PDF
    doc.build(story)

    buffer.seek(0)
    return buffer
