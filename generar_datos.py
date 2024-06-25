import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv
import random
from datetime import datetime, timedelta
import os


class Producto:
    def __init__(self, nombre, precio):
        self.nombre = nombre
        self.precio = precio

    def __str__(self):
        return f"{self.nombre}: {self.precio}"


def registrar_busqueda(func):
    def wrapper(*args, **kwargs):
        resultado = func(*args, **kwargs)
        busqueda = args[0]
        productos = [str(producto) for producto in busqueda.productos]
        data = {
            'fecha': datetime.now().strftime("%Y-%m-%d"),
            'busqueda': busqueda.url,
            'productos': busqueda.productos,
            'codigo': busqueda.codigo
        }
        guardar_registro(data, busqueda.marca, busqueda.codigo)
        return resultado
    return wrapper


def guardar_registro(data, marca, codigo):
    filename = f'registro_busquedas_{marca}.csv'
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        if file.tell() == 0:
            writer.writerow(['Fecha de búsqueda', 'Producto', 'Precio'])

        # Generar datos para 15 días
        for i in range(15):
            fecha = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            for producto in data['productos']:
                # Generar precio aleatorio
                precio_aleatorio = random.randint(500000, 2000000) / 100
                writer.writerow(
                    [fecha, producto.nombre, f"${precio_aleatorio:.2f}"])


class BuscadorProductos:
    def __init__(self, url, marca, codigo):
        self.url = url
        self.marca = marca
        self.codigo = codigo
        self.productos = []

    @registrar_busqueda
    def obtener_productos(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(self.url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to load page {self.url}")

        soup = BeautifulSoup(response.content, 'html.parser')
        lista_productos = soup.find_all(
            'li', {'class': 'ui-search-layout__item'})

        # Limitar la búsqueda a los primeros 20 productos
        for idx, producto in enumerate(lista_productos[:20], start=1):
            try:
                nombre = producto.find(
                    'h2', {'class': 'ui-search-item__title'})
                nombre = nombre.text.strip() if nombre else "No disponible"

                simbolo_moneda = producto.find(
                    'span', {'class': 'andes-money-amount__currency-symbol'})
                simbolo_moneda = simbolo_moneda.text.strip() if simbolo_moneda else "$"

                precio = producto.find(
                    'span', {'class': 'andes-money-amount__fraction'})
                precio = simbolo_moneda + precio.text.strip() if precio else "No disponible"

                self.productos.append(Producto(nombre, precio))
            except AttributeError as e:
                print(f"Error al procesar el producto: {e}")
                continue

    def productos_a_dataframe(self):
        return pd.DataFrame([(producto.nombre, producto.precio) for producto in self.productos], columns=["Producto", "Precio"])


def main():
    terminos_busqueda = [
        ("Smart Tv 50 Pulgadas 4k Ultra Hd 50uq8050psb - LG", "LG", "50uq8050psb"),
        ("smart tv samsung 50 Un50cu7000 led 4k", "Samsung", "un50cu7000"),
        ("smart tv bgh google tv 5023us6g led 4k 50", "BGH", "5023us6g"),
        ("Smart Tv Noblex Dk50x6550pi Led Hdr 4k 50", "Noblex", "dk50x6550pi"),
        ("smart tv tcl L50c645 50 4k qled google tv hdr bidcom", "TCL", "l50c645")
    ]

    for busqueda, marca, codigo in terminos_busqueda:
        busqueda_url = busqueda.strip().replace(" ", "-")
        url_busqueda = f'https://listado.mercadolibre.com.ar/{busqueda_url}#D[A:{busqueda.replace(" ", "%20")}]'

        buscador = BuscadorProductos(url_busqueda, marca, codigo)
        buscador.obtener_productos()

        df = buscador.productos_a_dataframe()


if __name__ == "__main__":
    main()
