from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken import views
from Log.urls import Logrouter, Registerrouter
from Record.urls import Recordrouter

urlpatterns = [
    path('admin', admin.site.urls),
    path('login', views.obtain_auth_token),
    path('', include(Logrouter.urls)),
    path('', include(Recordrouter.urls)),
    path('', include(Registerrouter.urls)),
]