from rest_framework import serializers
from Log.serializer import UserSerializer
from .models import Record

class RecordSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Record
        fields = '__all__'
