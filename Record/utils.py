from io import BytesIO

def gerar_analise_e_pdf(texto):
    buffer = BytesIO()

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    # Função para quebrar o texto a cada 70 caracteres
    def quebrar_texto(texto, max_length=70):
        linhas = []
        while len(texto) > max_length:
            # Encontra o último espaço antes do limite de caracteres
            corte = texto[:max_length].rfind(' ')
            if corte == -1:  # Se não houver espaço, corte direto no limite
                corte = max_length
            linhas.append(texto[:corte])
            texto = texto[corte:].strip()
        linhas.append(texto)  # Adiciona o restante do texto
        return linhas

    c = canvas.Canvas(buffer, pagesize=letter)
    
    linhas = quebrar_texto(texto)

    y = 750  # Posição inicial no eixo y
    for linha in linhas:
        c.drawString(100, y, linha)
        y -= 15  # Move a posição y para a próxima linha

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer
