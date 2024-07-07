from .views import RecordModelViewSet
from rest_framework.routers import DefaultRouter

Recordrouter = DefaultRouter()
Recordrouter.register(r'Record', RecordModelViewSet, basename='record')

urlpatterns = Recordrouter.urls