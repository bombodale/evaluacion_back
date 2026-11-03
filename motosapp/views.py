from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from decimal import Decimal, InvalidOperation
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer

from rest_framework import status
from rest_framework.response import Response

from rest_framework.views import APIView

from .models import Categoria, Marca, Modelo
 

IMAGENES_DEMO = {
    ("Yamaha R1", "Yamaha"): (
        "https://www.yamahamotos.cl/wp-content/uploads/2016/09/r1_negra.jpg"
    ),
    ("Moto Eléctrica", "GL Chile"): (
        "https://glchile.com/wp-content/uploads/2025/03/JGW-ROJO-045-430x430.jpg"
    ),
    ("GSX-R 1000", "Suzuki"): (
        "https://motollopis.es/wp-content/uploads/2021/09/GSXR1000-1024x676.jpg"
    ),
    ("Kawasaki Ninja", "Kawasaki"): (
        "https://images.unsplash.com/photo-1558981806-ec527fa84c39?auto=format&fit=crop&w=900&q=80"
    ),
    ("Honda CBR", "Honda"): (
        "https://images.unsplash.com/photo-1571068316344-75bc8c34e2b6?auto=format&fit=crop&w=900&q=80"
    ),
}

MOTOS_DEMO = (
    {"nombre": "Yamaha R1", "marca": "Yamaha", "anio": 2024, "precio": 2500000},
    {"nombre": "Moto Eléctrica", "marca": "GL Chile", "anio": 2025, "precio": 2200000},
    {"nombre": "GSX-R 1000", "marca": "Suzuki", "anio": 2025, "precio": 3000000},
    {"nombre": "Kawasaki Ninja", "marca": "Kawasaki", "anio": 2023, "precio": 2800000},
    {"nombre": "Honda CBR", "marca": "Honda", "anio": 2024, "precio": 2600000},
)


#def home(request):
#   return inicio(request)


def _cargar_motos_demo():
    categoria, _ = Categoria.objects.get_or_create(nombre="General")

    for moto in MOTOS_DEMO:
        marca, _ = Marca.objects.get_or_create(nombre=moto["marca"])
        Modelo.objects.get_or_create(
            marca=marca,
            nombre=moto["nombre"],
            anio=moto["anio"],
            defaults={
                "categoria": categoria,
                "precio_referencia": moto["precio"],
                "activo": True,
            },
        )


def _datos_vista(modelo):
    return {
        "id": modelo.pk,
        "nombre": modelo.nombre,
        "marca": modelo.marca.nombre,
        "anio": modelo.anio,
        "precio": modelo.precio_referencia,
        "imagen": IMAGENES_DEMO.get(
            (modelo.nombre, modelo.marca.nombre),
            "https://images.unsplash.com/photo-1558981806-ec527fa84c39?auto=format&fit=crop&w=900&q=80",
        ),
    }


def inicio(request):
    if request.method != "GET":
        return HttpResponse("Método no permitido.", status=405)

    _cargar_motos_demo()
    motos = [
        _datos_vista(modelo)
        for modelo in Modelo.objects.select_related("marca").filter(activo=True)
    ]
    return render(request, "motosapp/home.html", {"motos": motos})


def _guardar_modelo(request, modelo=None):
    nombre = request.POST.get("nombre", "").strip()
    nombre_marca = request.POST.get("marca", "").strip()
    anio_raw = request.POST.get("anio", "").strip()
    precio_raw = request.POST.get("precio", "").strip()

    if not nombre:
        raise ValidationError("El nombre de la motocicleta es obligatorio.")
    if not nombre_marca:
        raise ValidationError("La marca de la motocicleta es obligatoria.")
    if not anio_raw:
        raise ValidationError("El año es obligatorio.")
    if not precio_raw:
        raise ValidationError("El precio es obligatorio.")

    try:
        anio = int(anio_raw)
    except (TypeError, ValueError):
        raise ValidationError("El año debe ser un número entero.")

    if anio < 1885 or anio > timezone.now().year + 1:
        raise ValidationError(
            f"El año debe estar entre 1885 y {timezone.now().year + 1}."
        )

    try:
        precio = Decimal(precio_raw)
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError("El precio debe ser un número válido.")

    if not precio.is_finite() or precio <= 0:
        raise ValidationError("El precio debe ser mayor que cero.")

    modelo = modelo or Modelo()
    modelo.nombre = Modelo._meta.get_field("nombre").clean(nombre, modelo)
    modelo.anio = Modelo._meta.get_field("anio").clean(anio, modelo)
    modelo.precio_referencia = Modelo._meta.get_field(
        "precio_referencia"
    ).clean(precio, modelo)

    nombre_marca = Marca._meta.get_field("nombre").clean(nombre_marca, None)
    modelo.marca, _ = Marca.objects.get_or_create(nombre=nombre_marca)
    modelo.categoria, _ = Categoria.objects.get_or_create(nombre="General")

    modelo.full_clean()
    modelo.save()
    return modelo


def crear(request):
    if request.method == "GET":
        return render(request, "motosapp/crear.html")
    if request.method != "POST":
        return HttpResponse("Método no permitido.", status=405)

    try:
        modelo = _guardar_modelo(request)
    except ValidationError as error:
        return render(
            request,
            "motosapp/crear.html",
            {"error": "; ".join(error.messages)}, status=400
        )

    return redirect("detalle", moto_id=modelo.pk)


def detalle(request, moto_id):
    if request.method != "GET":
        return HttpResponse("Método no permitido.", status=405)

    modelo = (
        Modelo.objects.select_related("marca")
        .filter(pk=moto_id, activo=True)
        .first()
    )
    if modelo is None:
        return HttpResponse("Motocicleta no encontrada.", status=404)

    return render(
        request,
        "motosapp/detalle.html",
        {"moto": _datos_vista(modelo)},
    )


def editar(request, moto_id):
    modelo = (
        Modelo.objects.select_related("marca")
        .filter(pk=moto_id, activo=True)
        .first()
    )
    if modelo is None:
        return HttpResponse("Motocicleta no encontrada.", status=404)

    if request.method == "GET":
        return render(
            request,
            "motosapp/editar.html",
            {"moto": _datos_vista(modelo)},
        )
    if request.method != "POST":
        return HttpResponse("Método no permitido.", status=405)

    try:
        _guardar_modelo(request, modelo)
    except ValidationError as error:
        return render(
            request,
            "motosapp/editar.html",
            {
            "moto": _datos_vista(modelo), 
            "error": "; ".join(error.messages),
            }, status=400
        )

    return redirect("detalle", moto_id=modelo.pk)


def eliminar(request, moto_id):
    modelo = (
        Modelo.objects.select_related("marca")
        .filter(pk=moto_id, activo=True)
        .first()
    )
    if modelo is None:
        return HttpResponse("Motocicleta no encontrada.", status=404)

    if request.method == "GET":
        return render(
            request,
            "motosapp/eliminar.html",
            {"moto": _datos_vista(modelo)},
        )
    if request.method != "POST":
        return HttpResponse("Método no permitido.", status=405)

    try:
        modelo.delete()
    except ProtectedError:
        return HttpResponse(
            "No se puede eliminar el modelo porque hay motocicletas asociadas.",
            status=400,
        )

    return redirect("inicio")

def _api_errores_validacion(error):
    if hasattr(error, "message_dict"):
        return error.message_dict
    return {"detail": error.messages}


def _api_validar_payload(data, modelo=None):
    if not isinstance(data, dict):
        raise ValidationError({"body": "El cuerpo debe ser un objeto JSON."})

    campos = {"nombre", "marca", "anio", "precio"}
    faltantes = campos - data.keys()
    desconocidos = data.keys() - campos

    errores = {}
    if faltantes:
        errores["detail"] = [
            f"Faltan campos obligatorios: {', '.join(sorted(faltantes))}."
        ]
    if desconocidos:
        errores["detail"] = errores.get("detail", []) + [
            f"Campos no permitidos: {', '.join(sorted(desconocidos))}."
        ]
    if errores:
        raise ValidationError(errores)

    nombre = data["nombre"]
    marca = data["marca"]
    anio = data["anio"]
    precio_entrada = data["precio"]

    if not isinstance(nombre, str) or not nombre.strip():
        raise ValidationError({"nombre": "Debe ser un texto no vacío."})
    if not isinstance(marca, str) or not marca.strip():
        raise ValidationError({"marca": "Debe ser un texto no vacío."})
    if type(anio) is not int:
        raise ValidationError({"anio": "Debe ser un número entero."})
    if isinstance(precio_entrada, bool) or not isinstance(
        precio_entrada, (int, float)
    ):
        raise ValidationError({"precio": "Debe ser un número."})

    nombre = nombre.strip()
    marca = marca.strip()

    if anio < 1900 or anio > timezone.now().year + 1:
        raise ValidationError({
            "anio": f"Debe estar entre 1900 y {timezone.now().year + 1}."
        })

    try:
        precio = Decimal(str(precio_entrada))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError({"precio": "Debe ser un número válido."})

    if not precio.is_finite() or precio <= 0:
        raise ValidationError({"precio": "Debe ser mayor que cero."})

    instancia = modelo or Modelo()
    nombre = Modelo._meta.get_field("nombre").clean(nombre, instancia)
    anio = Modelo._meta.get_field("anio").clean(anio, instancia)
    precio = Modelo._meta.get_field("precio_referencia").clean(
        precio, instancia
    )
    marca = Marca._meta.get_field("nombre").clean(marca, None)

    return nombre, marca, anio, precio


def _api_guardar_modelo(data, modelo=None):
    nombre, nombre_marca, anio, precio = _api_validar_payload(data, modelo)

    with transaction.atomic():
        marca, _ = Marca.objects.get_or_create(nombre=nombre_marca)
        categoria, _ = Categoria.objects.get_or_create(nombre="General")

        instancia = modelo or Modelo()
        instancia.nombre = nombre
        instancia.marca = marca
        instancia.categoria = categoria
        instancia.anio = anio
        instancia.precio_referencia = precio

        instancia.full_clean()
        instancia.save()

    return instancia


def _api_modelo_json(modelo):
    return {
        "id": modelo.pk,
        "nombre": modelo.nombre,
        "marca": modelo.marca.nombre,
        "anio": modelo.anio,
        # Se devuelve como texto para conservar la precisión del precio.
        "precio": str(modelo.precio_referencia),
    }


class ModeloAPIBase(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    renderer_classes = [JSONRenderer]


class ModeloListaAPI(ModeloAPIBase):
    def get(self, request):
        modelos = (
            Modelo.objects.select_related("marca")
            .filter(activo=True)
            .order_by("id")
        )
        return Response([_api_modelo_json(modelo) for modelo in modelos])

    def post(self, request):
        try:
            modelo = _api_guardar_modelo(request.data)
        except ValidationError as error:
            return Response(_api_errores_validacion(error), status=400)
        except IntegrityError:
            return Response(
                {"detail": "Ya existe un modelo con esos datos."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(_api_modelo_json(modelo), status=status.HTTP_201_CREATED)


class ModeloDetalleAPI(ModeloAPIBase):
    def get(self, request, modelo_id):
        modelo = get_object_or_404(
            Modelo.objects.select_related("marca").filter(activo=True),
            pk=modelo_id,
        )
        return Response(_api_modelo_json(modelo))

    def put(self, request, modelo_id):
        modelo = get_object_or_404(
            Modelo.objects.select_related("marca").filter(activo=True),
            pk=modelo_id,
        )

        try:
            modelo = _api_guardar_modelo(request.data, modelo)
        except ValidationError as error:
            return Response(_api_errores_validacion(error), status=400)
        except IntegrityError:
            return Response(
                {"detail": "Ya existe un modelo con esos datos."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(_api_modelo_json(modelo))

    def delete(self, request, modelo_id):
        modelo = get_object_or_404(
            Modelo.objects.filter(activo=True),
            pk=modelo_id,
        )

        try:
            modelo.delete()
        except ProtectedError:
            return Response(
                {"detail": "No se puede eliminar: hay motocicletas asociadas."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)