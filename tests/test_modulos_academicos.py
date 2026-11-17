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
        self.assertEqual(len(result["escenarios_producto"]),4)
        self.assertTrue(all(x["unidadesEscenario"]>=0 for x in result["escenarios_producto"]))
        self.assertTrue(all(x["visitasSupuestas"]>0 for x in result["escenarios_producto"]))
        self.assertGreaterEqual(len(result["ejemplos"]), 10)
        self.assertTrue(all("fecha" in row and "estimado" in row for row in result["ejemplos"]))
        escenario = {"idProducto": 2, "precioSoles": 49.9,
                     "descuentoPorcentaje": 10, "visitasSemana": 120}
        modificado = ejecutar("DEMANDA", rows, "PRUEBA", escenario_demanda=escenario)
        self.assertEqual(modificado["mae_unidades"], result["mae_unidades"])
        self.assertEqual(modificado["r2_prueba"], result["r2_prueba"])
        self.assertEqual(modificado["escenario_personalizado"]["idProducto"], 2)
        self.assertGreaterEqual(modificado["escenario_personalizado"]["unidadesEscenario"], 0)
        with self.assertRaisesRegex(ValueError, "identificador"):
            ejecutar("DEMANDA", rows, "PRUEBA", escenario_demanda={
                "idProducto": 999, "precioSoles": 49.9,
                "descuentoPorcentaje": 0, "visitasSemana": 120})
        with self.assertRaisesRegex(ValueError, "solo admite"):
            ejecutar("DEMANDA", rows, "REALES", escenario_demanda=escenario)
        with self.assertRaisesRegex(ValueError, "descuento"):
            ejecutar("DEMANDA", rows, "PRUEBA", escenario_demanda={
                **escenario, "descuentoPorcentaje": 110})



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


    def test_real_outfits_ignore_simulated_style(self):
        rows=[
            {"id_variante_superior":3,"superior":"Blusa",
             "precio_superior_soles":45,
             "id_variante_inferior":18,"inferior":"Pantalón",
             "precio_inferior_soles":65,
             "puntuacion_estilo_simulada_0_100":100,
             "presupuesto_soles":180},
            {"id_variante_superior":4,"superior":"Blusa",
             "precio_superior_soles":55,
             "id_variante_inferior":19,"inferior":"Pantalón",
             "precio_inferior_soles":85,
             "puntuacion_estilo_simulada_0_100":0,
             "presupuesto_soles":180},
        ]
        result=ejecutar("OUTFITS",rows,"REALES",180)
        self.assertEqual(result["a_estrella"]["combinacion"]["precio_soles"],140)
        self.assertIn("sin evaluación de estilo",result["nota"])

    def test_no_outfits_under_budget(self):
        rows=[{"id_variante_superior":3,"superior":"Blusa",
              "precio_superior_soles":90,"id_variante_inferior":18,
              "inferior":"Pantalón","precio_inferior_soles":140,
              "puntuacion_estilo_simulada_0_100":0,"presupuesto_soles":180}]
        result=ejecutar("OUTFITS",rows,"REALES",50)
        self.assertEqual(result["factibles"],0)


if __name__ == "__main__":
    unittest.main()
