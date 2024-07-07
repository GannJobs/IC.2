# Create your views here.
from rest_framework.viewsets import ModelViewSet
from .models import Log
from .serializer import LogSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from rest_framework.response import Response
from django.http import JsonResponse
from django.contrib.auth.models import User


class LogModelViewSet(ModelViewSet):
    # authenticacao
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = LogSerializer
    queryset = Log.objects.all()

    # Listar logs
    def list(self, request):
        logs = Log.objects.all()
        serial = LogSerializer(logs, many=True)
        if len(serial.data) > 0:
            return Response({
                'status': 302, 'logs': serial.data
            })
        return Response({'status': 204, 'msg': 'No Content'})

class RegisterUserModelViewSet(ModelViewSet):
    def create(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        hashed_password = make_password(password)
        user_exists = User.objects.filter(username=username).exists()

        if user_exists:
            response_data = {'status': 409, 'errorType': 'NameError', 'errorAt': 'username'}
            return JsonResponse(response_data, status=409)

        email = request.data.get('email')
        if not email:
            response_data = {'status': 400, 'errorType': 'ValidationError', 'errorAt': 'email', 'msg': 'Email is required'}
            return JsonResponse(response_data, status=400)

        try:
            validate_email(email)
        except ValidationError:
            response_data = {'status': 400, 'errorType': 'ValidationError', 'errorAt': 'email', 'msg': 'Invalid email'}
            return JsonResponse(response_data, status=400)

        email_exists = User.objects.filter(email=email).exists()
        if email_exists:
            response_data = {'status': 409, 'errorType': 'NameError', 'errorAt': 'email', 'msg': 'Email already registered'}
            return JsonResponse(response_data, status=409)

        name = request.data.get('first name', '')

        usuario = User.objects.create(
            username=username, password=hashed_password, email=email, first_name=name, last_name=" ")
        usuario.save()
        
        return Response({'status': 201, 'msg': 'registered successfully'})