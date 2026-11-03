from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path('', views.inicio, name='home'),
    path('tienda/', views.inicio, name='inicio'),
    path('crear/', views.crear, name='crear'),
    path('detalle/<int:moto_id>/', views.detalle, name='detalle'),
    path('editar/<int:moto_id>/', views.editar, name='editar'),
    path('eliminar/<int:moto_id>/', views.eliminar, name='eliminar'),
    
    path("api/token/", obtain_auth_token, name="api_token"),
    path("api/modelos/", views.ModeloListaAPI.as_view(), name="api_modelos"),
    
    path("api/modelos/<int:modelo_id>/",views.ModeloDetalleAPI.as_view(),   name="api_modelo_detalle"),
    
    
]