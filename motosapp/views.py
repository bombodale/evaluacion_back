from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .models import Categoria, Marca, Modelo


def home(request):
    if request.method != "GET":
        return HttpResponse("Método no permitido.", status=405)
    return render(request, "motosapp/home.html")


def inicio(request):
    if request.method != "GET":
        return HttpResponse("Método no permitido.", status=405)

    motos = [
        _datos_vista(modelo)
        for modelo in Modelo.objects.select_related("marca").filter(activo=True)
    ]
    return render(request, "motosapp/inicio.html", {"motos": motos})


def _datos_vista(modelo):
    return {
        "id": modelo.pk,
        "nombre": modelo.nombre,
        "marca": modelo.marca.nombre,
        "anio": modelo.anio,
        "precio": modelo.precio_referencia,
        "imagen": "",
    }


def _guardar_modelo(request, modelo=None):
    nombre = request.POST.get("nombre", "").strip()
    nombre_marca = request.POST.get("marca", "").strip()

    if not nombre:
        raise ValidationError("El nombre de la motocicleta es obligatorio.")
    if not nombre_marca:
        raise ValidationError("La marca de la motocicleta es obligatoria.")

    modelo = modelo or Modelo()
    modelo.nombre = nombre
    modelo.anio = Modelo._meta.get_field("anio").clean(
        request.POST.get("anio", ""), modelo
    )
    modelo.precio_referencia = Modelo._meta.get_field("precio_referencia").clean(
        request.POST.get("precio", ""), modelo
    )
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
        _guardar_modelo(request)
    except ValidationError as error:
        return HttpResponse("; ".join(error.messages), status=400)

    return redirect("inicio")


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
        return HttpResponse("; ".join(error.messages), status=400)

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
