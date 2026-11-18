# ElectroShop | Sistema de Inventario Full-Stack

**Proyecto Integrador - Programación IV**  
**Autor:** Juan Emmanuel Sanchez Castañon  
**Fecha:** 18 Noviembre 2026

Sistema web de gestión de inventario para componentes electrónicos desarrollado con **FastAPI**, **Pandas** y **Chart.js**. Implementa persistencia real mediante archivos CSV, análisis de datos en tiempo real y un dashboard interactivo sin recargas de página.

---

##  Características Principales

-   **Persistencia CSV:** Todas las operaciones (CRUD + Ventas) se guardan directamente en `productos.csv` y `ventas.csv`.
-   **Análisis con Pandas:** Endpoints analíticos que procesan historial de ventas para generar KPIs y series de datos.
-   **Dashboard Interactivo:** Visualización dinámica con Chart.js (Barras horizontales + Doughnut) y tarjetas de métricas clave.
-   **Concurrencia Segura:** Manejo de compras simultáneas mediante `asyncio.Lock`.
-   **Rate Limiting:** Middleware de protección contra abuso de peticiones.
-   **Diseño Personalizado:** Interfaz moderna "ElectroShop" con Bootstrap 5 e identidad visual propia.

---

##  Stack Tecnológico

| Capa | Tecnología |
| :--- | :--- |
| **Backend** | FastAPI, Uvicorn, Pandas, Python 3.14 |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3 |
| **Visualización** | Chart.js 4.x + Plugin DataLabels |
| **Almacenamiento** | Archivos planos CSV (Sin base de datos externa) |

---

##  Instalación y Ejecución

### 1. Requisitos Previos
-   Python 3.10 o superior
-   Git

### 2. Clonar Repositorio
```bash
git clone https://github.com/TU_USUARIO/ElectroShop.git
cd ElectroShop

## Estructura del Proyecto

ElectroShop/
├── main.py              # Backend FastAPI + Lógica Pandas
├── app.js               # Lógica Frontend + Chart.js
├── index.html           # Interfaz de usuario + Estilos
├── productos.csv        # Persistencia de catálogo
├── ventas.csv           # Historial de transacciones
├── README.md            # Documentación del proyecto
└── imagenes/            # Assets visuales y capturas