import json
from functools import wraps

from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.core import signing
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Categoria, Marca, Modelo


TOKEN_SALT = "motosapp.api"
TOKEN_MAX_AGE = 60 * 60
MODEL_FIELDS = {
    "nombre",
    "anio",
    "cilindraje",
    "tipo_motor",
    "potencia_hp",
    "precio_referencia",
    "activo",
}
REQUIRED_FIELDS = {"nombre", "marca_id", "categoria_id"}
ALLOWED_FIELDS = MODEL_FIELDS | {"marca_id", "categoria_id"}


def _error(message, status):
    return JsonResponse({"error": message}, status=status)


def _read_json_object(request):
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, _error("El cuerpo debe contener JSON válido.", 400)

    if not isinstance(payload, dict):
        return None, _error("El JSON debe ser un objeto.", 400)

    return payload, None


@csrf_exempt
@require_http_methods(["POST"])
def obtener_token(request):
    payload, error_response = _read_json_object(request)
    if error_response:
        return error_response

    username = payload.get("username")
    password = payload.get("password")
    if not isinstance(username, str) or not username.strip():
        return _error("El campo username es obligatorio.", 400)
    if not isinstance(password, str) or not password:
        return _error("El campo password es obligatorio.", 400)

    user = authenticate(request, username=username.strip(), password=password)
    if user is None or not user.is_active or not user.is_superuser:
        return _error("Credenciales inválidas o usuario sin permisos de superusuario.", 401)

    token = signing.dumps({"user_id": user.pk}, salt=TOKEN_SALT)
    return JsonResponse(
        {
            "token": token,
            "token_type": "Bearer",
            "expires_in": TOKEN_MAX_AGE,
        }
    )


def requiere_token(view):
    @wraps(view)
    def wrapped_view(request, *args, **kwargs):
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not separator or not token.strip():
            return _error("Falta un token Bearer válido en el encabezado Authorization.", 401)

        try:
            data = signing.loads(
                token.strip(),
                salt=TOKEN_SALT,
                max_age=TOKEN_MAX_AGE,
            )
        except signing.BadSignature:
            return _error("El token es inválido o ha expirado.", 401)

        if not isinstance(data, dict) or not isinstance(data.get("user_id"), int):
            return _error("El token es inválido.", 401)

        user = get_user_model().objects.filter(
            pk=data["user_id"],
            is_active=True,
            is_superuser=True,
        ).first()
        if user is None:
            return _error("El token no pertenece a un superusuario activo.", 401)

        request.user = user
        return view(request, *args, **kwargs)

    return wrapped_view


def _parse_payload(request):
    payload, error_response = _read_json_object(request)
    if error_response:
        return None, error_response

    unknown_fields = set(payload) - ALLOWED_FIELDS
    if unknown_fields:
        return None, JsonResponse(
            {
                "errors": {
                    "campos": [
                        f"Campo no permitido: {field}."
                        for field in sorted(unknown_fields)
                    ]
                }
            },
            status=400,
        )

    return payload, None


def _get_related_object(model, payload, field_name):
    object_id = payload.get(field_name)
    if isinstance(object_id, bool) or not isinstance(object_id, int):
        raise ValidationError({field_name: "Debe indicar un ID entero válido."})

    try:
        return model.objects.get(pk=object_id)
    except model.DoesNotExist:
        raise ValidationError({field_name: "No existe un registro con ese ID."}) from None


def _save_model(payload, modelo=None):
    missing_fields = REQUIRED_FIELDS - payload.keys()
    if missing_fields:
        raise ValidationError(
            {field: "Este campo es obligatorio." for field in sorted(missing_fields)}
        )

    if "activo" in payload and not isinstance(payload["activo"], bool):
        raise ValidationError({"activo": "Debe ser un valor booleano."})

    modelo = modelo or Modelo()
    modelo.marca = _get_related_object(Marca, payload, "marca_id")
    modelo.categoria = _get_related_object(Categoria, payload, "categoria_id")

    for field_name in MODEL_FIELDS.intersection(payload):
        field = Modelo._meta.get_field(field_name)
        try:
            value = field.clean(payload[field_name], modelo)
        except ValidationError as error:
            raise ValidationError({field_name: error.messages}) from None
        setattr(modelo, field_name, value)

    modelo.full_clean()
    modelo.save()
    return modelo


def _serialize_model(modelo):
    return {
        "id": modelo.pk,
        "nombre": modelo.nombre,
        "marca_id": modelo.marca_id,
        "marca": modelo.marca.nombre,
        "categoria_id": modelo.categoria_id,
        "categoria": modelo.categoria.nombre,
        "anio": modelo.anio,
        "cilindraje": modelo.cilindraje,
        "tipo_motor": modelo.tipo_motor,
        "potencia_hp": modelo.potencia_hp,
        "precio_referencia": modelo.precio_referencia,
        "activo": modelo.activo,
    }


def _validation_error_response(error):
    return JsonResponse({"errors": error.message_dict}, status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
@requiere_token
def modelos(request):
    if request.method == "GET":
        queryset = Modelo.objects.select_related("marca", "categoria").all()
        return JsonResponse({"data": [_serialize_model(item) for item in queryset]})

    payload, error_response = _parse_payload(request)
    if error_response:
        return error_response

    try:
        modelo = _save_model(payload)
    except ValidationError as error:
        return _validation_error_response(error)

    return JsonResponse(_serialize_model(modelo), status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
@requiere_token
def modelo_detalle(request, modelo_id):
    try:
        modelo = Modelo.objects.select_related("marca", "categoria").get(pk=modelo_id)
    except Modelo.DoesNotExist:
        return _error("Modelo no encontrado.", 404)

    if request.method == "GET":
        return JsonResponse(_serialize_model(modelo))

    if request.method == "DELETE":
        try:
            modelo.delete()
        except ProtectedError:
            return _error("No se puede eliminar el modelo porque tiene motos asociadas.", 409)
        return JsonResponse({"mensaje": "Modelo eliminado correctamente."})

    payload, error_response = _parse_payload(request)
    if error_response:
        return error_response

    try:
        modelo = _save_model(payload, modelo)
    except ValidationError as error:
        return _validation_error_response(error)

    return JsonResponse(_serialize_model(modelo))