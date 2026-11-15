import csv
import tempfile
import unittest
from pathlib import Path

from src.preparar_tallas import preparar

COLUMNAS = [
    "categoria","talla_comprada","ajuste","busto_cm","cintura_cm",
    "cadera_cm","prenda_pecho_cm","prenda_cintura_cm","prenda_cadera_cm"
]

class PrepararTallasTests(unittest.TestCase):
    def test_preparar_excluye_incompletas_y_conserva_etiquetas(self):
        with tempfile.TemporaryDirectory() as tmp:
            entrada=Path(tmp)/"raw.csv"
            salida=Path(tmp)/"dataset.csv"
            filas=[
                dict(zip(COLUMNAS,["Tops","M","BIEN","90","70","","98","80",""])),
                dict(zip(COLUMNAS,["Vestidos","M","GRANDE","90","70","","98","80","100"])),
                dict(zip(COLUMNAS,["Bottoms","S","PEQUENA","","70","96","","74","100"])),
            ]
            with entrada.open("w",encoding="utf-8",newline="") as f:
                w=csv.DictWriter(f,fieldnames=COLUMNAS);w.writeheader();w.writerows(filas)
            resultado=preparar(entrada,salida)
            self.assertEqual(resultado,{"filas":3,"validas":2,"incompletas":1,"invalidas":0})
            with salida.open(encoding="utf-8",newline="") as f:
                dataset=list(csv.DictReader(f))
            self.assertEqual(len(dataset),2)
            self.assertEqual(dataset[0]["holgura_pecho_cm"],"8.0")
            self.assertEqual(dataset[0]["ajuste"],"BIEN")
            self.assertEqual(dataset[1]["ajuste"],"PEQUENA")
            self.assertNotIn("id_usuario",dataset[0])

    def test_no_inventa_etiquetas(self):
        with tempfile.TemporaryDirectory() as tmp:
            entrada=Path(tmp)/"raw.csv";salida=Path(tmp)/"dataset.csv"
            with entrada.open("w",encoding="utf-8",newline="") as f:
                w=csv.DictWriter(f,fieldnames=COLUMNAS);w.writeheader()
                w.writerow(dict(zip(COLUMNAS,["Tops","S","INDEFINIDA","90","70","","92","74",""])))
            resultado=preparar(entrada,salida)
            self.assertEqual(resultado["validas"],0)
            self.assertEqual(resultado["invalidas"],1)

if __name__=="__main__":
    unittest.main()
