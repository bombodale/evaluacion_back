import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Marca, Modelo


class ModeloAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.marca = Marca.objects.create(nombre="Honda")
        cls.categoria = Categoria.objects.create(nombre="Deportiva")
        cls.superuser = get_user_model().objects.create_superuser(
            username="admin-api",
            email="admin@example.com",
            password="ClaveSegura123!",
        )

    def setUp(self):
        response = self.client.post(
            reverse("api_token"),
            data={"username": "admin-api", "password": "ClaveSegura123!"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.headers = {
            "HTTP_AUTHORIZATION": f"Bearer {response.json()['token']}"
        }

    def payload(self, **overrides):
        return {
            "nombre": "CB500",
            "marca_id": self.marca.pk,
            "categoria_id": self.categoria.pk,
            "anio": 2024,
            "cilindraje": 500,
            "tipo_motor": "Bicilíndrico",
            "potencia_hp": "47.50",
            "precio_referencia": "6500.00",
            "activo": True,
            **overrides,
        }

    def test_get_lista_y_detalle(self):
        modelo = Modelo.objects.create(
            nombre="CB500",
            marca=self.marca,
            categoria=self.categoria,
            anio=2024,
        )

        lista = self.client.get(reverse("api_modelos"), **self.headers)
        detalle = self.client.get(
            reverse("api_modelo_detalle", args=[modelo.pk]), **self.headers
        )

        self.assertEqual(lista.status_code, 200)
        self.assertEqual(lista.json()["data"][0]["id"], modelo.pk)
        self.assertEqual(detalle.status_code, 200)
        self.assertEqual(detalle.json()["nombre"], "CB500")

    def test_post_crea_modelo(self):
        response = self.client.post(
            reverse("api_modelos"),
            data=self.payload(),
            content_type="application/json",
            **self.headers,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["marca"], "Honda")
        self.assertTrue(Modelo.objects.filter(nombre="CB500").exists())

    def test_put_actualiza_modelo(self):
        modelo = Modelo.objects.create(
            nombre="CB500",
            marca=self.marca,
            categoria=self.categoria,
        )

        response = self.client.put(
            reverse("api_modelo_detalle", args=[modelo.pk]),
            data=json.dumps(self.payload(nombre="CB650")),
            content_type="application/json",
            **self.headers,
        )

        self.assertEqual(response.status_code, 200)
        modelo.refresh_from_db()
        self.assertEqual(modelo.nombre, "CB650")

    def test_delete_elimina_modelo(self):
        modelo = Modelo.objects.create(
            nombre="CB500",
            marca=self.marca,
            categoria=self.categoria,
        )

        response = self.client.delete(
            reverse("api_modelo_detalle", args=[modelo.pk]), **self.headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Modelo.objects.filter(pk=modelo.pk).exists())

    def test_rechaza_json_invalido_y_campos_obligatorios(self):
        url = reverse("api_modelos")

        invalid_json = self.client.post(
            url, data="{", content_type="application/json", **self.headers
        )
        missing_fields = self.client.post(
            url,
            data={"nombre": "CB500"},
            content_type="application/json",
            **self.headers,
        )

        self.assertEqual(invalid_json.status_code, 400)
        self.assertEqual(missing_fields.status_code, 400)
        self.assertIn("marca_id", missing_fields.json()["errors"])

    def test_rechaza_datos_invalidos(self):
        response = self.client.post(
            reverse("api_modelos"),
            data=self.payload(anio=-1),
            content_type="application/json",
            **self.headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("anio", response.json()["errors"])
        self.assertFalse(Modelo.objects.exists())

    def test_rechaza_ids_de_relaciones_inexistentes(self):
        response = self.client.post(
            reverse("api_modelos"),
            data=self.payload(marca_id=999),
            content_type="application/json",
            **self.headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("marca_id", response.json()["errors"])

    def test_responde_404_para_modelo_inexistente(self):
        response = self.client.get(
            reverse("api_modelo_detalle", args=[999]), **self.headers
        )

        self.assertEqual(response.status_code, 404)

    def test_token_solo_se_entrega_a_superusuario(self):
        response = self.client.post(
            reverse("api_token"),
            data={"username": "admin-api", "password": "incorrecta"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)

    def test_api_rechaza_token_ausente_o_invalido(self):
        url = reverse("api_modelos")
        sin_token = self.client.get(url)
        token_invalido = self.client.get(
            url, HTTP_AUTHORIZATION="Bearer token-falso"
        )

        self.assertEqual(sin_token.status_code, 401)
        self.assertEqual(token_invalido.status_code, 401)
