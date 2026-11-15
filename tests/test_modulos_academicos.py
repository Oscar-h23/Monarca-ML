import unittest
from app.modulos_academicos import ejecutar


class AcademicModulesTest(unittest.TestCase):
    def test_clustering(self):
        rows=[{
            "compras_ultimos_12_meses":i%15+1,
            "gasto_total_12_meses_soles":(i%15+1)*65,
            "ticket_promedio_soles":65,
            "dias_desde_ultima_compra":i%100,
            "visitas_web_ultimos_30_dias":i%20,
            "meses_antiguedad":i%24+1,
            "descuentos_usados_12_meses":i%5
        } for i in range(100)]
        result=ejecutar("CLUSTERING",rows,"PRUEBA")
        self.assertEqual(result["registros"],100)
        self.assertEqual(len(result["segmentos"]),4)
        self.assertEqual(sum(x["clientes"] for x in result["segmentos"]),100)

    def test_regression_with_temporal_split(self):
        rows=[{
            "fecha_inicio_semana":f"2026-{(i//4)//4+1:02d}-{(i//4)%4*7+1:02d}",
            "id_producto":i%4+2,
            "precio_soles":50+i%7,
            "descuento_porcentaje":15 if i%5==0 else 0,
            "visitas_producto_semana":40+i*2,
            "unidades_vendidas_semana":3+i%5+int(i*.12),
        } for i in range(80)]
        result=ejecutar("DEMANDA",rows,"PRUEBA")
        self.assertEqual(result["registros"],80)
        self.assertGreater(result["prueba"],0)

    def test_outfits_budget(self):
        rows=[{
            "id_variante_superior":i+1,"superior":"Blusa",
            "precio_superior_soles":50,
            "id_variante_inferior":i+100,"inferior":"Pantalón",
            "precio_inferior_soles":70,
            "puntuacion_estilo_simulada_0_100":60+i%30,
            "presupuesto_soles":140
        } for i in range(100)]
        result=ejecutar("OUTFITS",rows,"PRUEBA",140)
        self.assertEqual(result["factibles"],100)
        self.assertLessEqual(result["a_estrella"]["combinacion"]["precio_soles"],140)
        self.assertLessEqual(result["hill_climbing"]["combinacion"]["precio_soles"],140)


if __name__ == "__main__":
    unittest.main()
