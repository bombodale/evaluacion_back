from django.urls import path

from . import api


urlpatterns = [
    path("api/token/", api.obtener_token, name="api_token"),
    path("api/modelos/", api.modelos, name="api_modelos"),
    path("api/modelos/<int:modelo_id>/", api.modelo_detalle, name="api_modelo_detalle"),
]
