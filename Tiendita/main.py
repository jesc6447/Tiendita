from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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

@app.get("/")
def home():
    return {"Message": "Hola bienvenido"}

@app.get("/productos")
def getProductos():
    return inventario

@app.post("/productos")
def addProducto(producto: dict):

    nuevo_id = len(inventario) + 1
    nuevo_producto = {
        "id": nuevo_id,    
        "nombre": producto["nombre"],
        "precio": producto["precio"],
        "cantidad": producto["cantidad"]
    }

    inventario.append(nuevo_producto)

    return inventario

@app.delete("/productos/{producto_id}")
def deleteProducto(producto_id: int):
    for producto in inventario:
        if producto["id"] == producto_id:
            inventario.remove(producto)
            return {"Message": "El producto fue eliminado"}
    return {"Message": "No fue encontrado el producto"}


