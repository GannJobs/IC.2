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
from .utils import gerar_analise_e_pdf
from django.contrib.auth.models import User
from google.generativeai import generate_text
import google.generativeai as genai

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
        query_user = request.data.get('GPT')

        try:
            generated_text = generate_generative_text(query_user)
            pdf_buffer = gerar_analise_e_pdf(generated_text)

            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="analise.pdf"'

            Log.objects.create(user=user, description=f'The user is creating a record Name = {title}')

            return response
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)