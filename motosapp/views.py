from django.http import Http404
from django.shortcuts import redirect, render

MOTOS = [
    {"id": 1, "nombre": "Yamaha R1", "marca": "Yamaha", "anio": 2024, "precio": 2500000, "imagen": "https://www.yamahamotos.cl/wp-content/uploads/2016/09/r1_negra.jpg"},
    {"id": 2, "nombre": "Moto Eléctrica", "marca": "GL Chile", "anio": 2025, "precio": 2200000, "imagen": "https://glchile.com/wp-content/uploads/2025/03/JGW-ROJO-045-430x430.jpg"},
    {"id": 3, "nombre": "GSX-R 1000", "marca": "Suzuki", "anio": 2025, "precio": 3000000, "imagen": "https://motollopis.es/wp-content/uploads/2021/09/GSXR1000-1024x676.jpg"},
    {"id": 4, "nombre": "Kawasaki Ninja", "marca": "Kawasaki", "anio": 2023, "precio": 2800000, "imagen": "https://images.unsplash.com/photo-1558981806-ec527fa84c39?auto=format&fit=crop&w=900&q=80"},
    {"id": 5, "nombre": "Honda CBR", "marca": "Honda", "anio": 2024, "precio": 2600000, "imagen": "https://images.unsplash.com/photo-1571068316344-75bc8c34e2b6?auto=format&fit=crop&w=900&q=80"},
]


def _buscar_moto(moto_id):
    moto = next((m for m in MOTOS if m["id"] == moto_id), None)
    if moto is None:
        raise Http404("Moto no encontrada")
    return moto


def _normalizar_numero(valor, valor_por_defecto=0):
    if valor in (None, ""):
        return valor_por_defecto
    return int(valor)


def home(request):
    return render(request, "motohttpapp/home.html")


def inicio(request):
    return render(request, "motohttpapp/inicio.html", {"motos": MOTOS})


def crear(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre", "Moto nueva").strip() or "Moto nueva"
        marca = request.POST.get("marca", "Sin marca").strip() or "Sin marca"
        anio = _normalizar_numero(request.POST.get("anio"), 2025)
        precio = _normalizar_numero(request.POST.get("precio"), 0)
        imagen = request.POST.get("imagen", "").strip() or "https://images.unsplash.com/photo-1558981806-ec527fa84c39?auto=format&fit=crop&w=900&q=80"

        moto = {
            "id": max((m["id"] for m in MOTOS), default=0) + 1,
            "nombre": nombre,
            "marca": marca,
            "anio": anio,
            "precio": precio,
            "imagen": imagen,
        }
        MOTOS.append(moto)
        return redirect("detalle", moto_id=moto["id"])

    return render(request, "motohttpapp/crear.html")


def detalle(request, moto_id):
    moto = _buscar_moto(moto_id)
    return render(request, "motohttpapp/detalle.html", {"moto": moto})


def editar(request, moto_id):
    moto = _buscar_moto(moto_id)

    if request.method == "POST":
        moto["nombre"] = request.POST.get("nombre", moto["nombre"]).strip() or moto["nombre"]
        moto["marca"] = request.POST.get("marca", moto["marca"]).strip() or moto["marca"]
        moto["anio"] = _normalizar_numero(request.POST.get("anio"), moto["anio"])
        moto["precio"] = _normalizar_numero(request.POST.get("precio"), moto["precio"])
        moto["imagen"] = request.POST.get("imagen", moto["imagen"]).strip() or moto["imagen"]
        return redirect("detalle", moto_id=moto["id"])

    return render(request, "motohttpapp/editar.html", {"moto": moto})


def eliminar(request, moto_id):
    moto = _buscar_moto(moto_id)

    if request.method == "POST":
        global MOTOS
        MOTOS = [m for m in MOTOS if m["id"] != moto_id]
        return redirect("inicio")

    return render(request, "motohttpapp/eliminar.html", {"moto": moto})
