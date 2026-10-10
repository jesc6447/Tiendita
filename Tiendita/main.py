"""
Title: main.py
Description: Este archivo contiene la implementación de una API RESTful utilizando FastAPI para gestionar un inventario de productos electrónicos. La API permite consultar, agregar y eliminar productos del inventario. Además, se ha configurado CORS para permitir solicitudes desde cualquier origen.
fecha: 2024-06-15
Autor: Juan Emmanuel Sanchez Castañon
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from pydantic import BaseModel, Field
from typing import List

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


inventario = [
    {"id": 1, "nombre": "Arduino Uno R3 (Original)", "precio": 450.00, "cantidad": 15},
    {"id": 2, "nombre": "Raspberry Pi 4 Model B (4GB)", "precio": 1500.00, "cantidad": 8},
    {"id": 3, "nombre": "ESP32 DevKit V1 (Wi-Fi + BT)", "precio": 180.00, "cantidad": 30},
    {"id": 4, "nombre": "Sensor Ultrasónico HC-SR04", "precio": 45.00, "cantidad": 50},
    {"id": 5, "nombre": "Protoboard 830 Puntos", "precio": 85.00, "cantidad": 40},
    {"id": 6, "nombre": "Kit de Resistencias Variadas (500 pzs)", "precio": 120.00, "cantidad": 25},
    {"id": 7, "nombre": "Módulo Relé 5V 1 Canal", "precio": 35.00, "cantidad": 60},
    {"id": 8, "nombre": "Pantalla LCD 16x2 con Módulo I2C", "precio": 95.00, "cantidad": 20},
    {"id": 9, "nombre": "Servomotor SG90 Micro", "precio": 65.00, "cantidad": 35},
    {"id": 10, "nombre": "Fuente de Poder Regulable 5V 3A", "precio": 250.00, "cantidad": 12}
]
#Modelos de pydantic para validar los datos de entrada y salida de la API
class crearProducto(BaseModel):
    nombre: str = Field(..., min_length=1, description="Nombre del producto")
    precio: float = Field(..., gt=0, description="Precio del producto")
    cantidad: int = Field(..., ge=0, description="Cantidad del producto")
#Modelo pydantic para la respuesta de los productos
class respuestaProducto(BaseModel):
    id: int
    nombre: str
    precio: float
    cantidad: int

@app.get("/meseros")
async def consultar_db():
    await asyncio.sleep(5) 
    print("Consulta a la base de datos completada") # Simula una operación de consulta a la base de datos
    return {"status":"ok"}

@app.get("/")
def home():
    return {"Message": "Hola bienvenido"}

@app.get("/productos")
def getProductos():
    return inventario

@app.post("/productos", response_model=respuestaProducto, status_code=status.HTTP_201_CREATED)
def addProducto(producto: crearProducto):
    try:
        nuevo_id = max((p["id"] for p in inventario), default=0) + 1
        nuevo_producto = {
            "id": nuevo_id,    
            "nombre": producto.nombre,
            "precio": producto.precio,
            "cantidad": producto.cantidad
        }
        inventario.append(nuevo_producto)
        return nuevo_producto
        
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Ocurrió un error al agregar el producto: {str(error)}")

@app.delete("/productos/{producto_id}")
def deleteProducto(producto_id: int):
    try:
        for producto in inventario:
            if producto["id"] == producto_id:
                inventario.remove(producto)
                return {"Message": "El producto fue eliminado"}
        return {"Message": "No fue encontrado el producto"}
    except Exception as e:
        return {"Message": "Ocurrió un error al eliminar el producto", "Error": str(e)}

