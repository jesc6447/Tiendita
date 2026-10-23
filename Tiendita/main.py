"""
Title: main.py
Description: Este archivo contiene la implementación de una API RESTful utilizando FastAPI para gestionar un inventario de productos electrónicos. La API permite consultar, agregar y eliminar productos del inventario. Además, se ha configurado CORS para permitir solicitudes desde cualquier origen.
fecha: 2024-06-15
Autor: Juan Emmanuel Sanchez Castañon
"""

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from collections import deque
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

# ==========================================
# 3. MIDDLEWARE DE RATE LIMITING (Límite de peticiones)
# ==========================================
MAX_REQUESTS = 5          # Máximo de peticiones permitidas
TIME_WINDOW = 1.0         # Ventana de tiempo en segundos (1 segundo)

# Cola para almacenar las marcas de tiempo de las peticiones recientes
request_timestamps = deque()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Obtenemos el tiempo actual usando el reloj nativo de asyncio
    loop = asyncio.get_running_loop()
    current_time = loop.time()

    # Limpiar la cola: Eliminamos las marcas de tiempo que ya tienen más de 1 segundo
    while request_timestamps and request_timestamps[0] <= current_time - TIME_WINDOW:
        request_timestamps.popleft()

    # Verificar si se excedió el límite
    if len(request_timestamps) >= MAX_REQUESTS:
        # Si hay 5 o más peticiones en el último segundo, rechazamos la petición
        return JSONResponse(
            status_code=429, # 429 Too Many Requests
            content={
                "error": "Demasiadas peticiones", 
                "detail": "Has excedido el límite de 5 peticiones por segundo. Intenta de nuevo en un momento."
            }
        )

    # Registrar la petición actual
    request_timestamps.append(current_time)

    # Procesar la petición y devolver la respuesta
    response = await call_next(request)
    return response

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

# Modelos de pydantic para validar los datos de entrada y salida de la API
class crearProducto(BaseModel):
    nombre: str = Field(..., min_length=1, description="Nombre del producto")
    precio: float = Field(..., gt=0, description="Precio del producto")
    cantidad: int = Field(..., ge=0, description="Cantidad del producto")

# Modelo pydantic para la respuesta de los productos
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

# ---------------------------------------------------------
# ENDPOINTS CONVERTIDOS A ASYNC
# ---------------------------------------------------------

@app.get("/productos")
async def getProductos():
    """
    Obtiene todos los productos. 
    rápida y no bloqueante.
    """
    return inventario

@app.post("/productos", response_model=respuestaProducto, status_code=status.HTTP_201_CREATED)
async def addProducto(producto: crearProducto):
    """
    Agrega un nuevo producto. 
    Se utiliza 'await asyncio.sleep(0)' para simular una operación 
    asíncrona (como guardar en una BD real) y ceder el control al event loop.
    """
    try:
        # Simulación de operación asíncrona (I/O)
        await asyncio.sleep(0) 
        
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
async def deleteProducto(producto_id: int):
    """
    Elimina un producto por su ID.
    Al igual que en GET, no se usa 'await' porque la búsqueda y 
    eliminación en una lista en memoria es instantánea.
    """
    try:
        for producto in inventario:
            if producto["id"] == producto_id:
                inventario.remove(producto)
                return {"Message": "El producto fue eliminado"}
        return {"Message": "No fue encontrado el producto"}
    except HTTPException as errorHTTP:
        return {str(errorHTTP.status_code): errorHTTP.detail}
    except Exception as error:
        return {"Error": f"Ocurrió un error al eliminar el producto: {str(error)}"}


lock = asyncio.Lock()

@app.post("/productos/{producto_id}/comprar")
async def comprarProducto(producto_id: int):
    """
    Endpoint para simular la compra de un producto por su ID.
    Se busca el producto en el inventario y se reduce su cantidad en 1.
    Si la cantidad llega a 0, se elimina del inventario.
    """
    try:
        async with lock:
            for i, objeto in enumerate(inventario):
                if objeto["id"] == producto_id:
                    if objeto["cantidad"] > 0:
                        await asyncio.sleep(0.05)  # Simulación de operación asíncrona
                        objeto["cantidad"] -= 1
                        
                        # Si la cantidad llega a 0, lo eliminamos del inventario
                        if objeto["cantidad"] == 0:
                            inventario.pop(i)
                            return {"Message": "¡Compra exitosa! (Última unidad vendida, producto eliminado del inventario)"}
                        
                        return {"Message": "Compra realizada con éxito", "cantidad_restante": objeto["cantidad"]}
                    else:
                        raise HTTPException(status_code=400, detail="El producto está agotado")
            
            # Si termina el ciclo y no encontró el producto
            raise HTTPException(status_code=404, detail="Producto no encontrado en el inventario")
                    
    except HTTPException:
        raise  # Deja que FastAPI maneje los errores HTTP correctamente
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Ocurrió un error al procesar la compra: {str(error)}")