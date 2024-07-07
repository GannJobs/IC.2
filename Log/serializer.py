from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Log

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name')

class LogSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Log
        fields = '__all__'