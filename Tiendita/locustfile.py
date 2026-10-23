"""
Title: locustfile.py
Description: Este archivo contiene la definición de un usuario de prueba para realizar pruebas de carga en la API RESTful utilizando Locust. El usuario simula la acción de un comprador relámpago que realiza compras rápidas de productos electrónicos.
fecha: 14 de octubre de 2026
Autor: Juan Emmanuel Sanchez Castañon
"""

from locust import HttpUser, task, between
import random

class CompradorRelampago(HttpUser):
    # Tiempo de espera muy corto entre peticiones (0.1 a 0.3 segundos) 
    # para simular un comportamiento agresivo de "comprador relámpago".
    wait_time = between(0.1, 0.3)

    @task
    def comprarProducto(self):
        # Generamos un ID aleatorio. 
        # Rango 1-10: Probamos compras exitosas y agotamiento de inventario.
        # Rango 1-100: Probamos cómo maneja la API los errores 404 (Producto no encontrado).
        producto_id = random.randint(1, 10)
        
        # La URL debe coincidir EXACTAMENTE con el endpoint de FastAPI.
        # Usamos f-strings para insertar el ID en la ruta.
        # No necesitamos 'json=payload' porque el ID va en la URL.
        self.client.post(f"/productos/{producto_id}/comprar")