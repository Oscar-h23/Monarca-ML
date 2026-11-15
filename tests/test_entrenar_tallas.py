"""Pruebas del entrenamiento experimental: sin conexión a Supabase."""
import csv
import tempfile
import unittest
from pathlib import Path

import joblib
import pandas as pd
from src.entrenar_tallas import train


class SizeTrainingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.csv = self.root / "tallas.csv"

    def tearDown(self):
        self.temp.cleanup()

    def write_data(self, count=100):
        with self.csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "categoria", "talla_comprada", "holgura_pecho_cm",
                "holgura_cintura_cm", "holgura_cadera_cm", "ajuste"
            ])
            writer.writeheader()
            for i in range(count):
                label = ("PEQUENA", "BIEN", "GRANDE")[i % 3]
                offset = {"PEQUENA": -5, "BIEN": 6, "GRANDE": 20}[label]
                writer.writerow({
                    "categoria": ("Tops", "Bottoms", "Vestidos")[i % 3],
                    "talla_comprada": ("S", "M", "L")[i % 3],
                    "holgura_pecho_cm": offset,
                    "holgura_cintura_cm": offset,
                    "holgura_cadera_cm": offset,
                    "ajuste": label,
                })

    def test_train_exports_model_and_metrics(self):
        self.write_data()
        out = self.root / "models"
        result = train(self.csv, out, "PRUEBA")
        self.assertEqual(result["rows"], 100)
        self.assertEqual(sum(result["splits"].values()), 100)
        self.assertTrue(result["experimental"])
        self.assertEqual(result["source"], "PRUEBA")
        self.assertTrue((out / "tallas_prueba_metricas.json").exists())
        model = joblib.load(out / "tallas_prueba.joblib")
        prediction = model.predict(pd.DataFrame([{
            "categoria": "Tops", "talla_comprada": "M",
            "holgura_pecho_cm": 5, "holgura_cintura_cm": 5,
            "holgura_cadera_cm": 5,
        }]))
        self.assertIn(prediction[0], ("PEQUENA", "BIEN", "GRANDE"))

    def test_rejects_four_real_rows(self):
        self.write_data(count=4)
        with self.assertRaises(ValueError):
            train(self.csv, self.root / "models", "REALES")


if __name__ == "__main__":
    unittest.main()
