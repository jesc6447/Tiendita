"""
Title: main.py
Description: Este archivo contiene la implementación de una API RESTful utilizando FastAPI para gestionar un inventario de productos electrónicos. La API permite consultar, agregar, eliminar y comprar productos del inventario. Además, se ha configurado CORS para permitir solicitudes desde cualquier origen.
Fecha: 2026-06-15
Autor: Juan Emmanuel Sanchez Castañon
"""

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from collections import deque
from pydantic import BaseModel, Field
from typing import List
import os
import csv
from datetime import datetime
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ==========================================
# MIDDLEWARE DE RATE LIMITING (Límite de peticiones)
# ==========================================
MAX_REQUESTS = 1000          # Máximo de peticiones permitidas
TIME_WINDOW = 1.0         # Ventana de tiempo en segundos (1 segundo)

# Cola para almacenar las marcas de tiempo de las peticiones recientes
request_timestamps = deque()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    loop = asyncio.get_running_loop()
    current_time = loop.time()

    # Limpiar la cola: Eliminamos las marcas de tiempo que ya tienen más de 1 segundo
    while request_timestamps and request_timestamps[0] <= current_time - TIME_WINDOW:
        request_timestamps.popleft()

    # Verificar si se excedió el límite
    if len(request_timestamps) >= MAX_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Demasiadas peticiones",
                "detail": "Has excedido el límite de 5 peticiones por segundo. Intenta de nuevo en un momento."
            }
        )

    request_timestamps.append(current_time)
    response = await call_next(request)
    return response


# ==========================================
# MODELOS PYDANTIC
# ==========================================
class crearProducto(BaseModel):
    nombre: str = Field(..., min_length=1, description="Nombre del producto")
    precio: float = Field(..., gt=0, description="Precio del producto")
    cantidad: int = Field(..., ge=0, description="Cantidad del producto")

class respuestaProducto(BaseModel):
    id: int
    nombre: str
    precio: float
    cantidad: int

class respuestaCompra(BaseModel):  
    mensaje: str


# ==========================================
# FUNCIONES AUXILIARES CSV
# ==========================================
def cargar_inventario_csv():
    productos = []
    if not os.path.exists("productos.csv"):
        return productos
    with open("productos.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            productos.append({
                "id": int(row["id"]),
                "nombre": row["nombre"],
                "precio": float(row["precio"]),
                "cantidad": int(row["cantidad"])
            })
    return productos

def guardar_inventario_csv(productos):
    with open("productos.csv", mode="w", newline="", encoding="utf-8") as f:
        fieldnames = ["id", "nombre", "precio", "cantidad"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(productos)

def registrar_venta_csv(producto_nombre: str, precio: float, cantidad: int = 1):
    file_exists = os.path.isfile("ventas.csv")
    with open("ventas.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["id_venta", "fecha", "producto", "precio", "cantidad", "monto_total"])
            nuevo_id = 1
        else:
            # Si el archivo ya existe, calculamos el siguiente ID libre
            with open("ventas.csv", "r", encoding="utf-8") as f:
                nuevo_id = sum(1 for line in f)  # cuenta header + datos
            # El ID será el número de líneas (header incluido), que coincide con el siguiente ID libre

        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
        monto_total = precio * cantidad
        writer.writerow([nuevo_id, fecha_actual, producto_nombre, precio, cantidad, monto_total])


# ==========================================
# ENDPOINTS
# ==========================================
@app.get("/")
def home():
    return {"Message": "Hola bienvenido"}


# GET - Obtener lista de productos
@app.get("/productos")
def getProductos():
    try:
        inventario = cargar_inventario_csv()
        return inventario
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )


# POST - Agregar producto
@app.post("/productos", response_model=respuestaProducto, status_code=status.HTTP_201_CREATED)
def addProducto(producto: crearProducto):
    try:
        inventario = cargar_inventario_csv()
        nuevo_id = max([p["id"] for p in inventario], default=0) + 1
        nuevo_producto = {
            "id": nuevo_id,
            "nombre": producto.nombre,
            "precio": producto.precio,
            "cantidad": producto.cantidad
        }
        inventario.append(nuevo_producto)
        guardar_inventario_csv(inventario)  
        return nuevo_producto
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al agregar el producto: {str(error)}"
        )


# DELETE - Eliminar producto
@app.delete("/productos/{producto_id}")
def deleteProducto(producto_id: int):
    try:
        inventario = cargar_inventario_csv()
        for producto in inventario:
            if producto["id"] == producto_id:
                inventario.remove(producto)
                guardar_inventario_csv(inventario)  
                return {"Message": "El producto fue eliminado"}
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No fue encontrado el producto"
        )
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )


# POST - Comprar producto (con lock para concurrencia)
lock = asyncio.Lock()

@app.post('/productos/{producto_id}', response_model=respuestaCompra)
async def comprarProducto(producto_id: int):
    try:
        async with lock:
            inventario = cargar_inventario_csv()
            objeto_aux = {}
            producto_encontrado = False

            for objeto in inventario:
                if objeto["id"] == producto_id:
                    producto_encontrado = True
                    if objeto["cantidad"] > 0:
                        objeto_aux = objeto
                        await asyncio.sleep(0.05)  # Simulación de proceso
                        objeto["cantidad"] = objeto["cantidad"] - 1
                        guardar_inventario_csv(inventario)  
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No hay stock de ese producto"
                        )
                    break  
            if not producto_encontrado:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No existe el ID de ese producto"
                )

        # Fuera del lock: registrar la venta
        registrar_venta_csv(
            producto_nombre=str.strip(objeto_aux["nombre"]),
            precio=objeto_aux["precio"],
            cantidad=1
        )

        return respuestaCompra(mensaje="Producto comprado")

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al comprar producto: {str(error)}"
        )

@app.get("/api/analisis/mas-vendidos")
def obtener_mas_vendidos():
    if not os.path.isfile("ventas.csv"):
        return []
    
    df = pd.read_csv("ventas.csv")
    if df.empty:
        return []

    df_agrupado = (
        df.groupby("producto")["monto_total"]
        .sum()
        .reset_index()
        .sort_values(by="monto_total", ascending=False)
    )

    return df_agrupado.to_dict(orient="records")

@app.get("/api/analisis/ticket-promedio")
def obtener_ticket_promedio():
    if not os.path.isfile("ventas.csv"):
        return {"total_ventas": 0, "ticket_promedio": 0.0}
    df = pd.read_csv("ventas.csv")
    if df.empty:
        return {"total_ventas": 0, "ticket_promedio": 0.0}
    total_ventas = len(df)
    ticket_promedio = float(df["monto_total"].mean())
    return {
        "total_ventas": total_ventas,
        "ticket_promedio": round(ticket_promedio, 2)
    }

@app.get("/api/analisis/kpis")
def obtener_kpis():
    if not os.path.isfile("ventas.csv"):
        return {"ingresos_totales": 0, "producto_estrella": "N/A", "ticket_promedio": 0}
    
    df = pd.read_csv("ventas.csv")
    if df.empty:
        return {"ingresos_totales": 0, "producto_estrella": "N/A", "ticket_promedio": 0}
        
    ingresos_totales = float(df["monto_total"].sum())
    ticket_promedio = float(df["monto_total"].mean())
    
    producto_estrella_df = df.groupby("producto")["monto_total"].sum().reset_index()
    producto_estrella = producto_estrella_df.sort_values(by="monto_total", ascending=False).iloc[0]["producto"]
    
    return {
        "ingresos_totales": round(ingresos_totales, 2),
        "producto_estrella": producto_estrella,
        "ticket_promedio": round(ticket_promedio, 2)
    }