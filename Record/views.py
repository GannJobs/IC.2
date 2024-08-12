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

    # Criar Registros
    def create(self, request):
        user = request.user
        Title = request.data.get('title')
        Description = request.data.get('description')

        Query_User = request.data.get('GPT')

        pdf_buffer = gerar_analise_e_pdf(Query_User)

        # Configurar a resposta para download do PDF
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="analise.pdf"'

        Log.objects.create(
            user=request.user, description='the user is creating a record Name = {}')

        return JsonResponse(response)
