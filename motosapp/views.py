from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import redirect, render

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


def home(request):
    if request.method != "GET":
        return HttpResponse("Método no permitido.", status=405)
    return render(request, "motosapp/home.html")


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
    return render(request, "motosapp/inicio.html", {"motos": motos})


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
        modelo = _guardar_modelo(request)
    except ValidationError as error:
        return HttpResponse("; ".join(error.messages), status=400)

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
