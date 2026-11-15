import unittest
from app.recomendacion import recomendar

V = [
    {'id_variante': 1, 'talla': 'S', 'stock': 4, 'pecho': 92, 'cintura': 74},
    {'id_variante': 2, 'talla': 'M', 'stock': 3, 'pecho': 98, 'cintura': 80},
    {'id_variante': 3, 'talla': 'L', 'stock': 0, 'pecho': 104, 'cintura': 86},
]

class RecomendacionTest(unittest.TestCase):
    def test_talla_compatible(self):
        self.assertEqual(recomendar('Tops', {'pecho': 90, 'cintura': 72}, V).talla, 'S')
    def test_no_recomienda_sin_medidas(self):
        self.assertIsNone(recomendar('Tops', {'pecho': 90}, V))
    def test_no_recomienda_sin_stock(self):
        self.assertIsNone(recomendar('Tops', {'pecho': 102, 'cintura': 84}, V))
    def test_vecino_cercano(self):
        self.assertEqual(recomendar('Tops', {'pecho': 95, 'cintura': 77}, V, 'vecino_cercano').talla, 'M')
    def test_no_utiliza_otras_categorias(self):
        self.assertIsNone(recomendar('Accesorios', {'pecho': 90, 'cintura': 72}, V))

if __name__ == '__main__':
    unittest.main()
