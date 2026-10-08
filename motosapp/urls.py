from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tienda/', views.inicio, name='inicio'),
    path('crear/', views.crear, name='crear'),
    path('detalle/<int:moto_id>/', views.detalle, name='detalle'),
    path('editar/<int:moto_id>/', views.editar, name='editar'),
    path('eliminar/<int:moto_id>/', views.eliminar, name='eliminar'),
]
