"""
Title: locustfile.py
Description: Este archivo contiene la definición de un usuario de prueba para 
realizar pruebas de carga en la API RESTful utilizando Locust. El usuario simula 
la acción de un comprador relámpago que realiza compras rápidas de productos 
electrónicos, además de consultar el catálogo y productos individuales.
fecha: 14 de octubre de 2026
Autor: Juan Emmanuel Sanchez Castañon
"""

from locust import HttpUser, task, between
import random


class CompradorRelampago(HttpUser):
    wait_time = between(0.1, 0.3)

    @task(3)
    def comprarProducto(self):
        #producto_id = random.randint(1, 10)
        self.client.post(
            f"/productos/2",
            name="Comprar Producto"
        )

    @task(1)
    def verCatalogo(self):
        self.client.get("/productos", name="Ver Catálogo")

    @task(1)
    def verProductoIndividual(self):
        producto_id = random.randint(1, 10)
        self.client.get(
            f"/productos/{producto_id}",
            name="Ver Producto Individual"
        )