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
from .utils import gerar_analise_e_pdf
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
        temperature=1.0,  # Ajuste conforme necessário
        max_output_tokens=10000
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
        # logs = Record.objects.all()
        # serial = RecordSerializer(logs, many=True)
        # if len(serial.data) > 0:
        #     return Response({
        #         'status': 302, 'Records': serial.data
        #     })
        # return Response({'status': 204, 'msg': 'No Content'})
        try:
            generated_text = generate_generative_text(
                "You're the best water quality analyst out there, so I'm coming to you with a request. I need you to see these analysis parameters that I am giving you and, based on them, analyze the results and give me a technical opinion back. The objective is for you to give me this technical opinion and not just justify the reason for this result. Remembering that your work will be extensively analyzed and evaluated, so keep your criteria high in your opinion to provide the best solution for that set of data. You will receive conclusions from water results based on laboratory analysis. The conclusion syntax is: Conclusion of the sample analytical service process: In accordance with the legislation(s) Annex XX of Consolidation Ordinance No. 5/2017, amended by Ordinance GM/MS No. 888/2021, it is found that the parameter(s) (s) tested for X, Y, Z... DO NOT meet the limits/ranges of acceptability established by the legislation(s) cited in this report. When the water is not up to par and: Conclusion of the sample analytical service process: In accordance with the legislation(s) Annex XX of Consolidation Ordinance No. 5/2017, amended by Ordinance GM/MS No. 888/2021, it is found that the parameter(s) (s) tested meet the limits/ranges of acceptability established by the legislation(s) cited in this report. When the water agrees. Considering, when the water is NOT in compliance, I need you to provide a technical opinion, outlining action plans in the following way when X, Y, Z represent, in one, two, three or more instances, the following inadequacies for the parameters and their treatment: Total coliforms - Chlorination before the reservoir or after the filters if, in your opinion, the use of filters is suggested. E. coli - Chlorination before the reservoir or after the filters if, in your opinion, the use of filters is suggested. Total dissolved solids - Treatment with reverse osmosis systems Turbidity - Polypropylene filters and activated carbon filter Apparent color - Activated carbon filter with previous oxidative chlorination or chemical treatment with aluminum sulfate or aluminum polychloride. Odor - Activated charcoal Total hardness - Softening filters Total iron (Fe2+ + Fe3+) - Previously chlorinated zeolite filters Manganese (Mn2+) - Previously Chlorinated Zeolite Filters Aluminum (Al3+) - Zeolite filters with previous chlorination Zinc (Zn2+) - Zeolite filters with previous chlorination Chromium (Cr3+ + Cr6+) - Previously Chlorinated Zeolite Filters Copper (Cu2+) - Previously Chlorinated Zeolite Filters Sulfate (SO4-) - Previously Chlorinated Zeolite Filters Hydrogen Sulfide (S2-) - Previously Chlorinated Zeolite Filters Fluorides (F-) - Reverse osmosis systems; Nitrate (N-NO3) - Reverse osmosis systems; Nitrite (N-NO2) - Reverse osmosis systems; Ammonia (N-NH4) - Zeolite filters with previous chlorination, or breakpoint chlorination which should only be carried out by a qualified professional Free residual chlorine - Chlorination before the reservoir or after the filters if, in your opinion, the use of filters is suggested. Chlorides (Cl-) - Reverse osmosis systems; Sodium (Na+) - Reverse osmosis systems; Use concise and professional language, but easy to understand for everyone. These are the restrictions: 1. Every treatment starts with a polypropylene filter after the pump. 2. If it is necessary to use zeolite, there must be an activated carbon filter before the zeolite filter and a chlorinator before the activated carbon filter; 3. If the problem is ONLY and ONLY total coliforms, e.g. coli and/or free residual chlorine, only chlorination is proposed. 4. If the water requires activated carbon, this must be preceded by a chlorinator; 5. If the water requires chlorination and zeolite and/or activated carbon filters, oxidative chlorination must precede activated carbon and there must be additional chlorination before using the water, so that the water has chlorine levels between 0.20 and 5.00 mg.L-1. We have two chlorinations, the oxidative one to remove color and metals which will ALWAYS come before the activated carbon and the disinfection one which will always be at the end of the treatment. You will receive the conclusion in the aforementioned syntax, and I expect a brief opinion of no more than 3 paragraphs, easy to read. Make it clear to the customer that the sizing of the filters will depend on the water flow they want. Write in plain text without enumerating or using bullet points when developing the treatment. Write a simple paragraph explaining the nature of each of the non-compliant parameters and the risks involved in consuming water containing them. In the following paragraphs, define the treatment according to the previous directives. After you have the results, I want you to compare them with VMP, and return all the processed data. here your details \"content\": [ { \"param\": \"Alcalinidade\", \"unit\": \"mg/L\", \"result\": \"20\", \"lq\": \"10\", \"vmp\": \"-\", \"method\": \"SMWW 2320 B\", \"date\": \"11/07/2024\" }, { \"param\": \"Condutividade elétrica*\", \"unit\": \"µS/cm\", \"result\": \"172,0\", \"lq\": \"1,0\", \"vmp\": \"-\", \"method\": \"10000 - SMWW 2150 B\", \"date\": \"11/07/2024\" }, { \"param\": \"Sólidos totais dissolvidos*\", \"unit\": \"mg/L\", \"result\": \"115,2\", \"lq\": \"12,0\", \"vmp\": \"500,0\", \"method\": \"PE 10.02_00\", \"date\": \"11/07/2024\" }, { \"param\": \"Turbidez\", \"unit\": \"NTU\", \"result\": \"<1,00\", \"lq\": \"1,14\", \"vmp\": \"5,00\", \"method\": \"SMWW 2130 B\", \"date\": \"11/07/2024\" }, { \"param\": \"Cor aparente\", \"unit\": \"uH/PCU\", \"result\": \"<5\", \"lq\": \"5\", \"vmp\": \"15\", \"method\": \"SMWW 2120 B\", \"date\": \"11/07/2024\" }, { \"param\": \"Gosto e odor\", \"unit\": \"Intensidade\", \"result\": \"<1\", \"lq\": \"1\", \"vmp\": \"7\", \"method\": \"SMWW 2170 B\", \"date\": \"11/07/2024\" }, { \"param\": \"Dureza total\", \"unit\": \"mg/L\", \"result\": \"60,0\", \"lq\": \"10,0\", \"vmp\": \"300,0\", \"method\": \"SMWW 2430 C\", \"date\": \"13/07/2024\" }, { \"param\": \"Cálcio (Ca2+)\", \"unit\": \"mg/L\", \"result\": \"36,0\", \"lq\": \"15,0\", \"vmp\": \"-\", \"method\": \"SMWW 2430 C\", \"date\": \"13/07/2024\" }, { \"param\": \"Magnésio (Mg2+)\", \"unit\": \"mg/L\", \"result\": \"24,0\", \"lq\": \"22,5\", \"vmp\": \"-\", \"method\": \"SMWW 2430 C\", \"date\": \"13/07/2024\" }, { \"param\": \"Ferro total (Fe2+ + Fe3+)\", \"unit\": \"mg/L\", \"result\": \"<0,25\", \"lq\": \"0,25\", \"vmp\": \"0,30\", \"method\": \"PE 10.12_00\", \"date\": \"13/07/2024\" }, { \"param\": \"Manganês (Mn2+)\", \"unit\": \"mg/L\", \"result\": \"<0,05\", \"lq\": \"0,05\", \"vmp\": \"0,10\", \"method\": \"PE 10.14_00\", \"date\": \"13/07/2024\" }, { \"param\": \"Alumínio (Al3+)\", \"unit\": \"mg/L\", \"result\": \"<0,02\", \"lq\": \"0,02\", \"vmp\": \"0,20\", \"method\": \"SMWW 3500Al B\", \"date\": \"13/07/2024\" }, { \"param\": \"Zinco (Zn2+)\", \"unit\": \"mg/L\", \"result\": \"<0,01\", \"lq\": \"0,01\", \"vmp\": \"5,00\", \"method\": \"SMWW 3500Zn B\", \"date\": \"13/07/2024\" }, { \"param\": \"Cromo (Cr3+ + Cr6+)\", \"unit\": \"mg/L\", \"result\": \"<0,01\", \"lq\": \"0,01\", \"vmp\": \"0,05\", \"method\": \"SMWW 3500Cr B\", \"date\": \"13/07/2024\" }, { \"param\": \"Cobre (Cu2+)\", \"unit\": \"mg/L\", \"result\": \"<0,02\", \"lq\": \"0,02\", \"vmp\": \"2,00\", \"method\": \"PE 10.15_00\", \"date\": \"13/07/2024\" }, { \"param\": \"Sódio (Na+)\", \"unit\": \"mg/L\", \"result\": \"<10\", \"lq\": \"10\", \"vmp\": \"200,0\", \"method\": \"PE 10.16_00\", \"date\": \"13/07/2024\" }, { \"param\": \"SRCNN\", \"unit\": \"Adimensional\", \"result\": \"<0,02\", \"lq\": \"-\", \"vmp\": \"1,00\", \"method\": \"GM/MS 888/21 Art. 39\", \"date\": \"11/07/2024\" } ]"    
            )
            pdf_buffer = gerar_analise_e_pdf(generated_text)

            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="analise.pdf"'

            return response
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

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