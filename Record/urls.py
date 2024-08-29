from .views import RecordModelViewSet, RecordListView
from rest_framework.routers import DefaultRouter

Recordrouter = DefaultRouter()
Recordrouter.register(r'Record', RecordModelViewSet, basename='Record')

RecordCrouter = DefaultRouter()
RecordCrouter.register(r'RecordC', RecordListView, basename='Record')

urlpatterns = Recordrouter.urls
urlpatterns = RecordCrouter.urls