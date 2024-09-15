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
from rest_framework import status
import pdfplumber
import pandas as pd
import re
import os
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from rest_framework import generics
from groq import Groq
from rest_framework.permissions import AllowAny

client = Groq(
    # This is the default and can be omitted
    api_key="Insira sua key aqui"
)

def generate_generative_text(prompt: str) -> str:
    global previous_responses

    # Inicializa a lista de respostas anteriores, se ainda não existir
    if 'previous_responses' not in globals():
        previous_responses = []

    while len(previous_responses) < 2:

        # Se não houver respostas anteriores, apenas use o prompt atual
        if len(previous_responses) == 0:
            full_prompt = prompt
        else:
            # Combina as respostas anteriores com o prompt atual
            comparison_prompt = " ".join(
                ["Compare with previous analyses and make sure your analysis is robust."] + 
                [response[1] for response in previous_responses])  # Extraímos apenas o conteúdo da resposta
            full_prompt = f"The title must be 'Water quality analysis', and translate all text to portuguese brazilian REMEMBER, this translate is very important!. {prompt} {comparison_prompt}"

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": full_prompt,
                }
            ],
            model="llama3-8b-8192",
            temperature=0.4
        )

        # Avalia a qualidade da resposta usando um critério simples, como o comprimento
        quality_score = len(str(chat_completion.choices[0].message.content))

        # Armazena a resposta junto com sua pontuação de qualidade
        previous_responses.append((quality_score, str(chat_completion.choices[0].message.content)))

    # Quando tivermos 10 ou mais análises, selecionamos a melhor
    best_analysis = max(previous_responses, key=lambda x: x[0])

    # Mantém apenas as 5 melhores análises
    previous_responses = sorted(
        previous_responses, key=lambda x: x[0], reverse=True)[:5]

    return best_analysis[1]


# Dicionários de referência (exemplos, ajuste conforme necessário)
parametros = [
    "Coliformes totais", "E. coli", "‰", "pH*", "Alcalinidade", "Condutividade elétrica*", "Sólidos totais dissolvidos",
    "Salinidade*", "Turbidez", "Cor aparente", "Gosto e odor", "Dureza total", "Cálcio (Ca2+)", "Magnésio (Mg2+)",
    "Ferro total (Fe2+ + Fe3+)", "Alumínio (Al3+)", "Cromo (Cr3+ + Cr6)", "Sulfato (S04-)", "Fluoretos (F-)",
    "Nitrito (N-N02)", "Cloro residual livre", "Sódio (Na+)", "SRCNN"
]
unidades = ["UFC/100mL", "UpH", "mg/L", "µS/cm", "‰",
            "pH*", "NTU", "uH/PCU", "Intensidade", "Adimensional"]
metodos = [
    "SMWW 9222 A/B", "SMWW 9222 A/B/H", "SMWW 4500H+ B", "SMWW 2170 B", "SMWW 2320 B", "SMWW 2150 B", "PE 10.02_00",
    "SMWW 2130 B", "SMWW 2120 B", "SMWW 2430 C", "PE 10.14_00", "SMWW 3500Al B", "SMWW 3500Zn B", "SMWW 3500Cr B",
    "PE 10.15_00", "SMWW 4500SO4 2- E", "SMWW 4500S2 - D", "SMWW 4500F- D", "PE 10.10_00", "SMWW 4500NO2- B", "SMWW 4500NH3 - F",
    "SMWW 4500Cl- G", "SMWW 4500Cl- B", "PE 10.16_00", "GM/MS 888/21 Art. 39"
]

def identificar_coluna(value, header):
    value = value.strip().lower()  # Remove espaços extras e converte para minúsculas
    header = header.strip().lower()  # Remove espaços extras e converte para minúsculas

    if any(p.lower() in value for p in parametros):  # Comparar ignorando maiúsculas/minúsculas
        return "PARÂMETRO"
    elif any(u.lower() in value for u in unidades):
        return "UNIDADE"
    elif any(m.lower() in value for m in metodos):  # Comparar métodos ignorando maiúsculas/minúsculas
        return "MÉTODO"
    elif "resultado" in header:
        return "RESULTADO"
    elif "lq" in header:
        return "LQ"
    elif "vmp" in header:
        return "VMP"
    elif "data" in header:
        return "DATA DE ENSAIO"
    else:
        return header  # Retorna o header original se não corresponder a nenhum critério
    
class RecordListView(ModelViewSet):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer

    # Listar Registros
    def list(self, request):
        logs = Record.objects.all()
        serial = RecordSerializer(logs, many=True, context={'request': request})
        if len(serial.data) > 0:
            return Response({
                'status': 302, 'Records': serial.data
            })
        return Response({'status': 204, 'msg': 'No Content'})

class RecordModelViewSet(ModelViewSet):
    # authenticacao
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = RecordSerializer
    queryset = Record.objects.all()

    # Listar Registros
    def list(self, request):
        logs = Record.objects.filter(user=request.user)
        serial = RecordSerializer(logs, many=True, context={'request': request})
        if len(serial.data) > 0:
            return Response({
                'status': 302, 'Records': serial.data
            })
        return Response({'status': 204, 'msg': 'No Content'})

    def create(self, request):
        title = request.data.get('title')
        description = request.data.get('description')
        input_file = request.FILES.get('entrada')

        if input_file:
            try:
                with pdfplumber.open(input_file) as pdf:
                    # Process only the first page
                    first_page = pdf.pages[0]

                    page_text = first_page.extract_text()
                    if page_text:
                        lines = page_text.splitlines()
                        
                        selected_lines = lines[16:45]  # Indices are 0-based

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
        else:
            return Response({
                'error': 'Arquivo PDF não encontrado'
            }, status=status.HTTP_400_BAD_REQUEST)

        Console = "You're the best water quality analyst out there, so I'm coming to you with a request. I need you to see these analysis parameters that I am giving you and, based on them, analyze the results and give me a technical opinion back, remember, I don't want you to return special characters in your response, if you only need use the numeric values and, every time you change variables, put them between *, don't use emoji or anything else.. The objective is for you to give me this technical opinion and not just justify the reason for this result. Remembering that your work will be extensively analyzed and evaluated, so keep your criteria high in your opinion to provide the best solution for that set of data. You will receive conclusions from water results based on laboratory analysis. The conclusion syntax is: Conclusion of the sample analytical service process: In accordance with the legislation(s) Annex XX of Consolidation Ordinance No. 5/2017, amended by Ordinance GM/MS No. 888/2021, it is found that the parameter(s) (s) tested for X, Y, Z... DO NOT meet the limits/ranges of acceptability established by the legislation(s) cited in this report. When the water is not up to par and: Conclusion of the sample analytical service process: In accordance with the legislation(s) Annex XX of Consolidation Ordinance No. 5/2017, amended by Ordinance GM/MS No. 888/2021, it is found that the parameter(s) (s) tested meet the limits/ranges of acceptability established by the legislation(s) cited in this report. When the water agrees. Considering, when the water is NOT in compliance, I need you to provide a technical opinion, outlining action plans in the following way when X, Y, Z represent, in one, two, three or more instances, the following inadequacies for the parameters and their treatment: Total coliforms - Chlorination before the reservoir or after the filters if, in your opinion, the use of filters is suggested. E. coli - Chlorination before the reservoir or after the filters if, in your opinion, the use of filters is suggested. Total dissolved solids - Treatment with reverse osmosis systems Turbidity - Polypropylene filters and activated carbon filter Apparent color - Activated carbon filter with previous oxidative chlorination or chemical treatment with aluminum sulfate or aluminum polychloride. Odor - Activated charcoal Total hardness - Softening filters Total iron (Fe2+ + Fe3+) - Previously chlorinated zeolite filters Manganese (Mn2+) - Previously Chlorinated Zeolite Filters Aluminum (Al3+) - Zeolite filters with previous chlorination Zinc (Zn2+) - Zeolite filters with previous chlorination Chromium (Cr3+ + Cr6+) - Previously Chlorinated Zeolite Filters Copper (Cu2+) - Previously Chlorinated Zeolite Filters Sulfate (SO4-) - Previously Chlorinated Zeolite Filters Hydrogen Sulfide (S2-) - Previously Chlorinated Zeolite Filters Fluorides (F-) - Reverse osmosis systems; Nitrate (N-NO3) - Reverse osmosis systems; Nitrite (N-NO2) - Reverse osmosis systems; Ammonia (N-NH4) - Zeolite filters with previous chlorination, or breakpoint chlorination which should only be carried out by a qualified professional Free residual chlorine - Chlorination before the reservoir or after the filters if, in your opinion, the use of filters is suggested. Chlorides (Cl-) - Reverse osmosis systems; Sodium (Na+) - Reverse osmosis systems; Use concise and professional language, but easy to understand for everyone. These are the restrictions: 1. Every treatment starts with a polypropylene filter after the pump. 2. If it is necessary to use zeolite, there must be an activated carbon filter before the zeolite filter and a chlorinator before the activated carbon filter; 3. If the problem is ONLY and ONLY total coliforms, e.g. coli and/or free residual chlorine, only chlorination is proposed. 4. If the water requires activated carbon, this must be preceded by a chlorinator; 5. If the water requires chlorination and zeolite and/or activated carbon filters, oxidative chlorination must precede activated carbon and there must be additional chlorination before using the water, so that the water has chlorine levels between 0.20 and 5.00 mg.L-1. We have two chlorinations, the oxidative one to remove color and metals which will ALWAYS come before the activated carbon and the disinfection one which will always be at the end of the treatment. You will receive the conclusion in the aforementioned syntax, and I expect a brief opinion of no more than 3 paragraphs, easy to read. Make it clear to the customer that the sizing of the filters will depend on the water flow they want. Write in plain text without enumerating or using bullet points when developing the treatment. Write a simple paragraph explaining the nature of each of the non-compliant parameters and the risks involved in consuming water containing them. In the following paragraphs, define the treatment according to the previous directives. After you have the results, I want you to compare them with VMP, and return all the processed data. here your details \"content\": "

        # Iterar sobre cada linha extraída
        for line in page_data['lines']:
            # Remover espaços extras no início e fim da linha
            line = line.strip()
            Console += line + " "

        Console = Console.strip()
        
        # manda os dados para o GPT
        try:
            # Gera o texto usando a função de IA
            generated_text = generate_generative_text(Console)

            # Gera o PDF com base no texto gerado
            pdf_buffer = gerar_analise_e_pdf(generated_text)

            # Generate PDF analysis and store it
            pdf_content = ContentFile(pdf_buffer.getvalue(), name=f"{title}_analysis.pdf")


            # Criação do registro no banco de dados
            Record.objects.create(
                user=request.user,
                title=title,
                description=description,
                arq=input_file,
                returned_arq=pdf_content
            )

            return Response({'status': 200, "msg": "created"})
        except Exception as e:
            return Response({
                    'error': f'Erro ao processar o retorno: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)