/**
 Title: app.js
 Description: Archivo JavaScript para la funcionalidad del frontend de la tiendita.
 Fecha: 14 de octubre de 2026
 Autor: Juan Emmanuel Sanchez Castañon
 **/

const API_URL = "http://127.0.0.1:8000";

// Selección de Elementos del DOM
const formProducto = document.getElementById("formProducto");
const tablaProductos = document.getElementById("tablaProductos");
const totalProductos = document.getElementById("totalProductos");

// 1. Función para Cargar Productos (GET)
async function cargarProductos() {
    try {
        const respuesta = await fetch(`${API_URL}/productos`);
        
        if (!respuesta.ok) {
            throw new Error("Error al obtener los productos del servidor");
        }

        const productos = await respuesta.json();

        tablaProductos.innerHTML = "";
        totalProductos.textContent = `${productos.length} productos`;

        if (productos.length === 0) {
            tablaProductos.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted py-4">
                        No hay productos registrados en la tiendita.
                    </td>
                </tr>`;
            return;
        }

        productos.forEach(p => {
            const fila = document.createElement("tr");
            fila.innerHTML = `
                <td class="fw-bold text-secondary">#${p.id}</td>
                <td>${p.nombre}</td>
                <td class="text-success fw-bold">$${p.precio.toFixed(2)}</td>
                <td>
                    <span class="badge ${p.cantidad < 10 ? 'bg-danger' : 'bg-success'}">
                        ${p.cantidad} unidades
                    </span>
                </td>
                <td class="text-end">
                    <button class="btn btn-outline-primary btn-sm me-2" onclick="comprarProducto(${p.id})">
                        <i class="bi bi-cart-check"></i> Comprar
                    </button>
                    <button class="btn btn-outline-danger btn-sm" onclick="eliminarProducto(${p.id})">
                        <i class="bi bi-trash"></i> Eliminar
                    </button>
                </td>
            `;
            tablaProductos.appendChild(fila);
        });

    } catch (error) {
        console.error("Error al cargar productos:", error);
        alert("No se pudo conectar con el servidor para cargar los productos.");
    }
}

// 2. Función para Agregar Producto (POST)
async function agregarProducto(event) {
    event.preventDefault();
    const nombre = document.getElementById("nombre").value.trim();
    const precio = parseFloat(document.getElementById("precio").value);
    const cantidad = parseInt(document.getElementById("cantidad").value, 10);

    const nuevoContenido = { nombre, precio, cantidad };

    try {
        const respuesta = await fetch(`${API_URL}/productos`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(nuevoContenido)
        });

        if (respuesta.ok) {
            formProducto.reset();
            await cargarProductos();
            alert("Producto agregado correctamente");
        } else {
            const errorData = await respuesta.json();
            console.error("Error al guardar:", errorData);
            alert(`Error al guardar: ${errorData.detail || "Datos inválidos"}`);
        }
    } catch (error) {
        console.error("Error de red al agregar producto:", error);
        alert("Error de conexión al intentar agregar el producto.");
    }
}

// 3. Función para Eliminar Producto (DELETE)
async function eliminarProducto(id_producto) {
    if (!confirm("¿Estás seguro de que deseas eliminar este producto?")) {
        return; // Cancelar si el usuario dice que no
    }

    try {
        const respuesta = await fetch(`${API_URL}/productos/${id_producto}`, {
            method: "DELETE",
            headers: { "Content-Type": "application/json" }
        });

        if (respuesta.ok) {
            await cargarProductos();
            alert("🗑️ Producto eliminado correctamente");
        } else {
            const errorData = await respuesta.json();
            alert(`❌ Error: ${errorData.detail || "No se pudo eliminar el producto"}`);
        }
    } catch (error) {
        console.error("Error de red al eliminar producto:", error);
        alert("Error de conexión al intentar eliminar el producto.");
    }
}

// 4. Función para Comprar Producto (POST /productos/{id})
async function comprarProducto(id_producto) {
    try {
        const respuesta = await fetch(`${API_URL}/productos/${id_producto}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });

        let datos = {};
        try {
            datos = await respuesta.json();
        } catch (e) {
            datos = { detail: "Respuesta no válida del servidor" };
        }

        if (respuesta.ok) {
            alert(`¡Compra realizada con éxito!\n${datos.mensaje || "Producto comprado"}`);
            await cargarProductos(); // Recargar para ver el nuevo stock
        } else {
            let mensaje = datos.detail || "Error al procesar la compra";
            
            if (respuesta.status === 429) {
                mensaje = "¡Demasiadas peticiones! Tu middleware te está protegiendo. Espera un segundo.";
            } else if (respuesta.status === 404) {
                mensaje = "El producto ya no existe en el inventario.";
            } else if (respuesta.status === 400) {
                mensaje = `Sin stock: ${mensaje}`;
            }
            
            alert(mensaje);
            await cargarProductos(); // Recargar por si acaso
        }
    } catch (error) {
        console.error("Error al comprar:", error);
        alert("Error de conexión al procesar la compra.");
    }
}

// 5. Función para Cargar Análisis (GET /api/analisis/mas-vendidos)
async function cargarAnalisis() {
    try {
        
        const respuesta = await fetch(`${API_URL}/api/analisis/mas-vendidos`);
        
        if (!respuesta.ok) {
            throw new Error(`Error HTTP: ${respuesta.status}`);
        }

        const datos = await respuesta.json();
        
        // 1. Extraemos etiquetas y valores
        const labels = datos.map(item => item.producto);
        const valores = datos.map(item => item.monto_total);

        // 2. Generamos los colores dinámicamente
        const colores = datos.map((_, i) => {
            const coloresBase = [
                [255, 99, 132], [255, 159, 64], [255, 205, 86],
                [75, 192, 192], [54, 162, 235], [153, 102, 255],
                [201, 203, 207], [255, 99, 71], [0, 206, 209]
            ];
            const color = coloresBase[i % coloresBase.length];
            return `rgba(${color[0]}, ${color[1]}, ${color[2]}, 0.7)`; // Opacidad 0.7 para buen contraste
        });

        const canvas = document.getElementById("myChart");

        // 3. Evitamos el error "Canvas is already in use" si se recarga el gráfico
        if (window.miGrafico) {
            window.miGrafico.destroy();
        }
        Chart.register(ChartDataLabels);
        // 4. Creamos el gráfico usando la variable 'colores'
        window.miGrafico = new Chart(canvas, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Ingresos ($)",
                        data: valores,
                        backgroundColor: colores,
                        borderWidth: 1
                    }
                ]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

    } catch (error) {
        console.error("Error al cargar el análisis de ventas:", error);
    }
}

// Cargar catálogo y análisis al abrir la página
document.addEventListener("DOMContentLoaded", () => {
    cargarProductos();
    cargarAnalisis();
});

// Evento para que se ejecute la función al dar clic en guardar producto
if (formProducto) {
    formProducto.addEventListener("submit", agregarProducto);
}