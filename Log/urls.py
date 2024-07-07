from .views import LogModelViewSet, RegisterUserModelViewSet
from rest_framework.routers import DefaultRouter

Logrouter = DefaultRouter()
Logrouter.register(r'Log', LogModelViewSet, basename='log')

Registerrouter = DefaultRouter()
Registerrouter.register(r'Register', RegisterUserModelViewSet, basename='register')

urlpatterns = Registerrouter.urls
urlpatterns = Logrouter.urls