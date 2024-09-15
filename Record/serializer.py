from rest_framework import serializers
from Log.serializer import UserSerializer
from .models import Record

class RecordSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    arq_url = serializers.SerializerMethodField()
    returned_arq_url = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = ['id', 'user', 'title', 'description', 'created_at', 'arq_url', 'returned_arq_url']

    def get_arq_url(self, obj):
        request = self.context.get('request')
        if request and obj.arq:
            return request.build_absolute_uri(obj.arq.url)
        return None

    def get_returned_arq_url(self, obj):
        request = self.context.get('request')
        if request and obj.returned_arq:
            return request.build_absolute_uri(obj.returned_arq.url)
        return None
