from django.test import TestCase
from django.urls import reverse

from . import views


class MotoCrudTests(TestCase):
    def setUp(self):
        views.MOTOS[:] = [
            {"id": 1, "nombre": "Yamaha R15", "marca": "Yamaha", "anio": 2024, "precio": 2500000, "imagen": "https://example.com/r15.jpg"},
            {"id": 2, "nombre": "Honda CBR 250", "marca": "Honda", "anio": 2023, "precio": 2200000, "imagen": "https://example.com/cbr.jpg"},
        ]

    def test_crear_moto_funciona(self):
        payload = {
            "nombre": "KTM Duke 390",
            "marca": "KTM",
            "anio": 2025,
            "precio": 3000000,
            "imagen": "https://example.com/duke.jpg",
        }

        response = self.client.post(reverse("crear"), payload)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(views.MOTOS), 3)
        self.assertEqual(views.MOTOS[-1]["nombre"], "KTM Duke 390")

    def test_editar_moto_funciona(self):
        payload = {
            "nombre": "Yamaha R7",
            "marca": "Yamaha",
            "anio": 2025,
            "precio": 2700000,
            "imagen": "https://example.com/r7.jpg",
        }

        response = self.client.post(reverse("editar", args=[1]), payload)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(views.MOTOS[0]["nombre"], "Yamaha R7")
        self.assertEqual(views.MOTOS[0]["precio"], 2700000)

    def test_eliminar_moto_funciona(self):
        response = self.client.post(reverse("eliminar", args=[1]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(views.MOTOS), 1)
        self.assertNotIn(1, [moto["id"] for moto in views.MOTOS])
