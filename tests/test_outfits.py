"""Regresiones de integridad del grafo y aislamiento de productos."""
import unittest

from src.generar_outfits import buscar_outfits
from src.preparar_datos import atributos, cargar_datos, dividir_productos


class IntegridadTests(unittest.TestCase):
    def test_dfs_exige_compatibilidad_entre_todas_las_piezas(self):
        a, b, c = ("1", "negro"), ("2", "azul"), ("3", "blanco")
        prendas = {a: {"categoria": "Tops"}, b: {"categoria": "Bottoms"}, c: {"categoria": "Calzado"}}
        grafo = {a: {b: 5, c: 4}, b: {a: 5}, c: {a: 4}}
        self.assertEqual(buscar_outfits(a, grafo, prendas), [])
        grafo[b][c] = grafo[c][b] = 3.5
        resultado = buscar_outfits(a, grafo, prendas)
        self.assertEqual(len(resultado), 1)
        self.assertEqual(len(resultado[0]["prendas"]), 3)

    def test_particiones_no_comparten_productos(self):
        catalogo, pares = cargar_datos("data/demo/catalogo.csv", "data/demo/valoraciones.csv")
        tablas, grupos = dividir_productos(catalogo, pares, 23)
        sets = [set(ids) for ids in grupos.values()]
        self.assertFalse(sets[0] & sets[1] or sets[1] & sets[2] or sets[0] & sets[2])
        for nombre, tabla in tablas.items():
            self.assertTrue(set(tabla.id_a) | set(tabla.id_b) <= set(grupos[nombre]))

    def test_atributos_son_simetricos(self):
        a = {"categoria": "Tops", "estilo": "casual", "color": "negro", "precio": 59}
        b = {"categoria": "Bottoms", "estilo": "formal", "color": "azul", "precio": 89}
        self.assertEqual(atributos(a, b), atributos(b, a))


if __name__ == "__main__":
    unittest.main()
