# utils.py
import openai
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

openai.api_key = settings.OPENAI_API_KEY

def gerar_analise_e_pdf(dados):
    resposta = openai.Completion.create(
        engine="text-davinci-003",
        prompt=dados,
        max_tokens=500
    )

    analise = resposta.choices[0].text.strip()
    
    # Gerar o PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, analise)
    c.save()
    
    buffer.seek(0)
    return buffer
