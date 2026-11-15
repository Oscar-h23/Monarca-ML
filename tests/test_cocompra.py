import unittest
from app.cocompra import complementos


class CopurchaseRecommendations(unittest.TestCase):
    def test_ranks_complementary_products_and_excludes_self(self):
        cestas=[[2,7] for _ in range(60)]+[[2,6] for _ in range(15)]+[[9,4] for _ in range(25)]
        r=complementos(cestas,2,"PRUEBA")
        self.assertEqual(r["cestas"],100)
        self.assertGreater(len(r["recomendaciones"]),0)
        self.assertTrue(all(x["idProducto"]!=2 for x in r["recomendaciones"]))
        by_id={x["idProducto"]:x for x in r["recomendaciones"]}
        self.assertAlmostEqual(by_id[7]["confianza"],60/75,places=4)
        self.assertAlmostEqual(by_id[7]["soporte"],60/100,places=4)
    def test_real_requires_a_minimum_basket_sample(self):
        r=complementos([[2,7] for _ in range(5)],2,"REALES")
        self.assertEqual(r["recomendaciones"],[])
    def test_invalid_identifiers_rejected(self):
        with self.assertRaises(ValueError):
            complementos([[0,7]],2,"PRUEBA")


if __name__=="__main__":
    unittest.main()
