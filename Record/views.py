# Create your views here.
from rest_framework.viewsets import ModelViewSet
from .models import Record
from Log.models import Log
from .serializer import RecordSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from django.http import JsonResponse
from django.http import HttpResponse
from django.contrib.auth.models import User
from google.generativeai import generate_text
import google.generativeai as genai
from rest_framework import status
import pdfplumber
import pandas as pd
import re
import os
from django.core.files.storage import FileSystemStorage

api_key = 'AIzaSyBKVx96_XykSFS7T4Gz_kgfEJj9yrF4BkI'
genai.configure(api_key=api_key)

# Função para gerar o texto
def generate_generative_text(prompt: str) -> str:
    response = generate_text(
        model='models/text-bison-001',  # Altere para o modelo correto se necessário
        prompt=prompt,
        temperature=0.7,  # Ajuste conforme necessário
        max_output_tokens=150
    )
    return response.result

# Dicionários de referência (exemplos, ajuste conforme necessário)
parametros = [
    "Coliformes totais", "E. coli", "‰", "pH*", "Alcalinidade", "Condutividade elétrica*", "Sólidos totais dissolvidos",
    "Salinidade*", "Turbidez", "Cor aparente", "Gosto e odor", "Dureza total", "Cálcio (Ca2+)", "Magnésio (Mg2+)",
    "Ferro total (Fe2+ + Fe3+)", "Alumínio (Al3+)", "Cromo (Cr3+ + Cr6)", "Sulfato (S04-)", "Fluoretos (F-)",
    "Nitrito (N-N02)", "Cloro residual livre", "Sódio (Na+)", "SRCNN"  
    ]
unidades = ["UFC/100mL", "UpH", "mg/L", "µS/cm", "‰", "pH*", "NTU", "uH/PCU", "Intensidade", "Adimensional"]
metodos = [
    "SMWW 9222 A/B", "SMWW 9222 A/B/H", "SMWW 4500H+ B", "SMWW 2170 B", "SMWW 2320 B", "SMWW 2150 B", "PE 10.02_00",
    "SMWW 2130 B", "SMWW 2120 B", "SMWW 2430 C", "PE 10.14_00", "SMWW 3500Al B", "SMWW 3500Zn B", "SMWW 3500Cr B",
    "PE 10.15_00", "SMWW 4500SO4 2- E", "SMWW 4500S2 - D", "SMWW 4500F- D", "PE 10.10_00", "SMWW 4500NO2- B", "SMWW 4500NH3 - F",
    "SMWW 4500Cl- G", "SMWW 4500Cl- B", "PE 10.16_00", "GM/MS 888/21 Art. 39"
    ]

def identificar_coluna(value, header):
    if any(p in value for p in parametros):
        return "PARÂMETRO"
    elif any(u in value for u in unidades):
        return "UNIDADE"
    elif any(m in value for m in metodos):  # para capturar métodos parciais
        return "MÉTODO"
    elif "RESULTADO" in header:
        return "RESULTADO"
    elif "LQ" in header:
        return "LQ"
    elif "VMP" in header:
        return "VMP"
    elif "DATA" in header:
        return "DATA DE ENSAIO"
    else:
        return header

class RecordModelViewSet(ModelViewSet):
    # authenticacao
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = RecordSerializer
    queryset = Record.objects.all()

    # Listar Registros
    def list(self, request):
        logs = Record.objects.all()
        serial = RecordSerializer(logs, many=True)
        if len(serial.data) > 0:
            return Response({
                'status': 302, 'Records': serial.data
            })
        return Response({'status': 204, 'msg': 'No Content'})

    def create(self, request):
        user = request.user
        title = request.data.get('title')
        description = request.data.get('description')
        input_file = request.FILES.get('entrada')

        if input_file:
            try:
                with pdfplumber.open(input_file) as pdf:
                    # Trabalha apenas na primeira página
                    first_page = pdf.pages[0]
                    
                    page_text = first_page.extract_text()
                    if page_text:
                        lines = page_text.splitlines()
                        # Captura as linhas de 10 a 45
                        selected_lines = lines[9:45]  # Índices são 0-based

                        page_data = {
                            'page_number': 1,
                            'lines': selected_lines
                        }
                    else:
                        return Response({
                            'error': 'Nenhum texto encontrado na primeira página'
                        }, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                return Response({
                    'error': f'Erro ao processar o PDF: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Define a regex para dividir os dados
            pattern = re.compile(
                r'(?P<param>[\w\s\(\)\+\*]+)\s+'    # Parâmetro
                r'(?P<unit>[\w\/\*°\‰]+)\s+'        # Unidade
                r'(?P<result>[<>\d\.,\-]+)\s+'      # Resultado
                r'(?P<lq>[<>\d\.,\-]+)\s+'          # LQ
                r'(?P<vmp>[<>\d\.,\-]+)\s+'         # VMP
                r'(?P<method>[\w\.\-\/\+ \d]+)\s+'  # Método
                r'(?P<date>\d{2}\/\d{2}\/\d{4})'    # Data
            )

            # Dados organizados
            organized_data = []

            for line in page_data['lines']:
                match = pattern.match(line)
                if match:
                    organized_data.append(match.groupdict())

            if organized_data:
                # Converter para DataFrame
                df = pd.DataFrame(organized_data)

                # Salvar o Excel em um caminho temporário
                fs = FileSystemStorage(location='excels/')
                excel_filename = f"{title}_resultado_analise.xlsx"
                excel_path = os.path.join('excels', excel_filename)
                df.to_excel(excel_path, index=False)

                # # Armazenar no modelo Record
                # record = Record.objects.create(
                #     user=user,
                #     title=title,
                #     description=description,
                #     arq=input_file,
                #     excel=fs.save(excel_filename, open(excel_path, 'rb'))
                # )
                # record.save()

                return Response({
                    'message': 'PDF processado com sucesso e Excel gerado.',
                    'content': organized_data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': 'Nenhuma linha corresponde ao padrão especificado.'
                }, status=status.HTTP_400_BAD_REQUEST)

        # manda os dados para o GPT
        # try:
        #     generated_text = generate_generative_text('Prompt')
        #     pdf_buffer = gerar_analise_e_pdf(generated_text)

        #     response = HttpResponse(pdf_buffer, content_type='application/pdf')
        #     response['Content-Disposition'] = 'attachment; filename="analise.pdf"'

        #     Log.objects.create(user=user, description=f'The user is creating a record Name = {title}')

              # retorna um pdf com o resultado da análise

        #     return response
        # except Exception as e:
        #     return JsonResponse({'error': str(e)}, status=500)