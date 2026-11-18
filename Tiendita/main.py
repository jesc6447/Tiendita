
"""
Title: main.py
Description: API REST para gestionar un inventario de productos electrónicos.
Fecha: 15 de octubre de 2026
actualización: 18 de noviembre de 2026
Autor: Juan Emmanuel Sanchez Castañon
"""

# Importación de librerías
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

# Inicialización de la API
app = FastAPI()

# Configuración de acceso CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ==========================================
# MIDDLEWARE DE RATE LIMITING
# ==========================================
MAX_REQUESTS = 1000  # Máximo de peticiones permitidas
TIME_WINDOW = 1.0    # Intervalo de tiempo en segundos

# Almacena las peticiones recientes
request_timestamps = deque()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Obtiene el tiempo actual
    loop = asyncio.get_running_loop()
    current_time = loop.time()

    # Elimina las peticiones fuera del intervalo
    while request_timestamps and request_timestamps[0] <= current_time - TIME_WINDOW:
        request_timestamps.popleft()

    # Comprueba si se superó el límite
    if len(request_timestamps) >= MAX_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Demasiadas peticiones",
                "detail": "Has excedido el límite de 1000 peticiones por segundo. Intenta de nuevo en un momento."
            }
        )

    # Registra y procesa la petición
    request_timestamps.append(current_time)
    response = await call_next(request)
    return response


# ==========================================
# MODELOS PYDANTIC
# ==========================================

# Define los datos necesarios para crear un producto
class crearProducto(BaseModel):
    nombre: str = Field(..., min_length=1, description="Nombre del producto")
    precio: float = Field(..., gt=0, description="Precio del producto")
    cantidad: int = Field(..., ge=0, description="Cantidad del producto")

# Define la estructura de respuesta de un producto
class respuestaProducto(BaseModel):
    id: int
    nombre: str
    precio: float
    cantidad: int

# Define la respuesta de una compra
class respuestaCompra(BaseModel):
    mensaje: str


# ==========================================
# FUNCIONES AUXILIARES CSV
# ==========================================

# Carga los productos desde el archivo CSV
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

# Guarda el inventario actualizado en el CSV
def guardar_inventario_csv(productos):
    with open("productos.csv", mode="w", newline="", encoding="utf-8") as f:
        fieldnames = ["id", "nombre", "precio", "cantidad"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(productos)

# Registra una venta en el archivo CSV
def registrar_venta_csv(producto_nombre: str, precio: float, cantidad: int = 1):
    file_exists = os.path.isfile("ventas.csv")
    with open("ventas.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            # Crea los encabezados de las ventas
            writer.writerow(["id_venta", "fecha", "producto", "precio", "cantidad", "monto_total"])
            nuevo_id = 1
        else:
            # Calcula el siguiente ID disponible
            with open("ventas.csv", "r", encoding="utf-8") as f:
                nuevo_id = sum(1 for line in f)

        # Calcula y guarda los datos de la venta
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
        monto_total = precio * cantidad
        writer.writerow([nuevo_id, fecha_actual, producto_nombre, precio, cantidad, monto_total])


# ==========================================
# ENDPOINTS
# ==========================================

# Endpoint principal
@app.get("/")
def home():
    return {"Message": "Hola bienvenido"}


# GET - Obtener lista de productos
@app.get("/productos")
def getProductos():
    try:
        # Consulta el inventario
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
        # Obtiene el inventario y genera un ID
        inventario = cargar_inventario_csv()
        nuevo_id = max([p["id"] for p in inventario], default=0) + 1

        # Construye el nuevo producto
        nuevo_producto = {
            "id": nuevo_id,
            "nombre": producto.nombre,
            "precio": producto.precio,
            "cantidad": producto.cantidad
        }

        # Guarda el producto en el inventario
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
        # Busca el producto por su ID
        inventario = cargar_inventario_csv()
        for producto in inventario:
            if producto["id"] == producto_id:
                # Elimina y guarda los cambios
                inventario.remove(producto)
                guardar_inventario_csv(inventario)
                return {"Message": "El producto fue eliminado"}

        # Informa si el producto no existe
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


# POST - Comprar producto
# Bloquea las compras simultáneas
lock = asyncio.Lock()

@app.post('/productos/{producto_id}', response_model=respuestaCompra)
async def comprarProducto(producto_id: int):
    try:
        async with lock:
            # Carga el inventario y busca el producto
            inventario = cargar_inventario_csv()
            objeto_aux = {}
            producto_encontrado = False

            for objeto in inventario:
                if objeto["id"] == producto_id:
                    producto_encontrado = True

                    # Comprueba que exista stock
                    if objeto["cantidad"] > 0:
                        objeto_aux = objeto
                        await asyncio.sleep(0.05)  # Simula el proceso de compra
                        objeto["cantidad"] = objeto["cantidad"] - 1

                        # Actualiza el inventario
                        guardar_inventario_csv(inventario)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No hay stock de ese producto"
                        )
                    break

            # Comprueba si se encontró el producto
            if not producto_encontrado:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No existe el ID de ese producto"
                )

        # Registra la venta después de liberar el bloqueo
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


# ==========================================
# ENDPOINTS DE ANÁLISIS
# ==========================================

# GET - Obtener productos más vendidos por ingresos
@app.get("/api/analisis/mas-vendidos")
def obtener_mas_vendidos():
    # Comprueba si existen ventas registradas
    if not os.path.isfile("ventas.csv"):
        return []

    # Lee el historial de ventas
    df = pd.read_csv("ventas.csv")
    if df.empty:
        return []

    # Agrupa los ingresos por producto
    df_agrupado = (
        df.groupby("producto")["monto_total"]
        .sum()
        .reset_index()
        .sort_values(by="monto_total", ascending=False)
    )

    return df_agrupado.to_dict(orient="records")


# GET - Calcular el ticket promedio
@app.get("/api/analisis/ticket-promedio")
def obtener_ticket_promedio():
    # Comprueba si existen ventas
    if not os.path.isfile("ventas.csv"):
        return {"total_ventas": 0, "ticket_promedio": 0.0}

    df = pd.read_csv("ventas.csv")
    if df.empty:
        return {"total_ventas": 0, "ticket_promedio": 0.0}

    # Calcula el total de ventas y su promedio
    total_ventas = len(df)
    ticket_promedio = float(df["monto_total"].mean())

    return {
        "total_ventas": total_ventas,
        "ticket_promedio": round(ticket_promedio, 2)
    }


# GET - Obtener indicadores generales de ventas
@app.get("/api/analisis/kpis")
def obtener_kpis():
    # Comprueba si existen ventas registradas
    if not os.path.isfile("ventas.csv"):
        return {"ingresos_totales": 0, "producto_estrella": "N/A", "ticket_promedio": 0}

    df = pd.read_csv("ventas.csv")
    if df.empty:
        return {"ingresos_totales": 0, "producto_estrella": "N/A", "ticket_promedio": 0}

    # Calcula los ingresos y el ticket promedio
    ingresos_totales = float(df["monto_total"].sum())
    ticket_promedio = float(df["monto_total"].mean())

    # Identifica el producto con mayores ingresos
    producto_estrella_df = df.groupby("producto")["monto_total"].sum().reset_index()
    producto_estrella = producto_estrella_df.sort_values(by="monto_total", ascending=False).iloc[0]["producto"]

    return {
        "ingresos_totales": round(ingresos_totales, 2),
        "producto_estrella": producto_estrella,
        "ticket_promedio": round(ticket_promedio, 2)
    }
