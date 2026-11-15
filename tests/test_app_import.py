"""Smoke test: CI must import the production ASGI app before deployment."""
import unittest
from app.main import app, Entrada, EntrenarRequest


class FastApiSmoke(unittest.TestCase):
    def test_asgi_import_and_routes(self):
        routes = {route.path for route in app.routes}
        self.assertIn("/health", routes)
        self.assertIn("/internal/v1/tallas/entrenar", routes)
        self.assertIn("/internal/v1/tallas/recomendar", routes)
        self.assertEqual(Entrada(categoria="Tops", medidas={}, variantes=[]).metodo, "reglas")
        self.assertEqual(EntrenarRequest(fuente="PRUEBA", dataset_csv="a" * 50).fuente, "PRUEBA")


if __name__ == "__main__":
    unittest.main()
