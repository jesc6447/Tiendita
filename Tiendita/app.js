/**
 * Title: app.js
 * Description: Funcionalidad del frontend de la tiendita.
 * Fecha: 14 de octubre de 2026
 * actualización: 18 de noviembre de 2026
 * Autor: Juan Emmanuel Sanchez Castañon
 */

// Dirección de la API
const API_URL = "http://127.0.0.1:8000";

// Selección de elementos del DOM
const formProducto = document.getElementById("formProducto");
const tablaProductos = document.getElementById("tablaProductos");
const totalProductos = document.getElementById("totalProductos");

// ==========================================
// CARGAR PRODUCTOS
// ==========================================

// GET - Consulta y muestra los productos
async function cargarProductos() {
    try {
        // Solicita los productos a la API
        const respuesta = await fetch(`${API_URL}/productos`);

        if (!respuesta.ok) {
            throw new Error("Error al obtener los productos del servidor");
        }

        // Convierte la respuesta a JSON
        const productos = await respuesta.json();

        // Limpia la tabla y actualiza el contador
        tablaProductos.innerHTML = "";
        totalProductos.textContent = `${productos.length} productos`;

        // Comprueba si existen productos
        if (productos.length === 0) {
            tablaProductos.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted py-4">
                        No hay productos registrados en la tiendita.
                    </td>
                </tr>`;
            return;
        }

        // Genera una fila por cada producto
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
        // Muestra errores de consulta
        console.error("Error al cargar productos:", error);
        alert("No se pudo conectar con el servidor para cargar los productos.");
    }
}

// ==========================================
// AGREGAR PRODUCTO
// ==========================================

// POST - Envía un nuevo producto a la API
async function agregarProducto(event) {
    event.preventDefault();

    // Obtiene y convierte los datos del formulario
    const nombre = document.getElementById("nombre").value.trim();
    const precio = parseFloat(document.getElementById("precio").value);
    const cantidad = parseInt(document.getElementById("cantidad").value, 10);

    const nuevoContenido = { nombre, precio, cantidad };

    try {
        // Envía los datos mediante POST
        const respuesta = await fetch(`${API_URL}/productos`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(nuevoContenido)
        });

        if (respuesta.ok) {
            // Limpia el formulario y actualiza la tabla
            formProducto.reset();
            await cargarProductos();
            alert("Producto agregado correctamente");
        } else {
            // Muestra los errores de validación
            const errorData = await respuesta.json();
            console.error("Error al guardar:", errorData);
            alert(`Error al guardar: ${errorData.detail || "Datos inválidos"}`);
        }
    } catch (error) {
        // Maneja errores de conexión
        console.error("Error de red al agregar producto:", error);
        alert("Error de conexión al intentar agregar el producto.");
    }
}

// ==========================================
// ELIMINAR PRODUCTO
// ==========================================

// DELETE - Elimina un producto por su ID
async function eliminarProducto(id_producto) {
    // Solicita confirmación antes de eliminar
    if (!confirm("¿Estás seguro de que deseas eliminar este producto?")) {
        return;
    }

    try {
        // Envía la solicitud de eliminación
        const respuesta = await fetch(`${API_URL}/productos/${id_producto}`, {
            method: "DELETE",
            headers: { "Content-Type": "application/json" }
        });

        if (respuesta.ok) {
            // Actualiza el inventario
            await cargarProductos();
            alert("Producto eliminado correctamente");
        } else {
            // Muestra el error devuelto por la API
            const errorData = await respuesta.json();
            alert(`Error: ${errorData.detail || "No se pudo eliminar el producto"}`);
        }
    } catch (error) {
        // Maneja errores de conexión
        console.error("Error de red al eliminar producto:", error);
        alert("Error de conexión al intentar eliminar el producto.");
    }
}

// ==========================================
// COMPRAR PRODUCTO
// ==========================================

// POST - Registra una compra por ID
async function comprarProducto(id_producto) {
    try {
        // Envía la solicitud de compra
        const respuesta = await fetch(`${API_URL}/productos/${id_producto}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });

        // Intenta leer la respuesta del servidor
        let datos = {};
        try {
            datos = await respuesta.json();
        } catch (e) {
            datos = { detail: "Respuesta no válida del servidor" };
        }

        if (respuesta.ok) {
            // Actualiza los datos después de comprar
            alert(`¡Compra realizada con éxito!\n${datos.mensaje || "Producto comprado"}`);
            await cargarProductos();
            await cargarAnalisis();
            await cargarGraficoTicket();
            await cargarKPIs();
        } else {
            // Obtiene el mensaje de error
            let mensaje = datos.detail || "Error al procesar la compra";

            // Identifica errores según el código HTTP
            if (respuesta.status === 429) {
                mensaje = "¡Demasiadas peticiones! Tu middleware te está protegiendo. Espera un segundo.";
            } else if (respuesta.status === 404) {
                mensaje = "El producto ya no existe en el inventario.";
            } else if (respuesta.status === 400) {
                mensaje = `Sin stock: ${mensaje}`;
            }

            alert(mensaje);
            await cargarProductos();
        }
    } catch (error) {
        // Maneja errores durante la compra
        console.error("Error al comprar:", error);
        alert("Error de conexión al procesar la compra.");
    }
}

// ==========================================
// GRÁFICA DE BARRAS
// ==========================================

// GET - Consulta los ingresos por producto
async function cargarAnalisis() {
    try {
        // Solicita los datos de ventas
        const respuesta = await fetch(`${API_URL}/api/analisis/mas-vendidos`);

        if (!respuesta.ok) {
            throw new Error(`Error HTTP: ${respuesta.status}`);
        }

        const datos = await respuesta.json();

        // Obtiene las etiquetas y los valores
        const labels = datos.map(item => item.producto);
        const valores = datos.map(item => item.monto_total);

        // Genera colores para cada producto
        const colores = datos.map((_, i) => {
            const coloresBase = [
                [255, 99, 132], [255, 159, 64], [255, 205, 86],
                [75, 192, 192], [54, 162, 235], [153, 102, 255],
                [201, 203, 207], [255, 99, 71], [0, 206, 209]
            ];
            const color = coloresBase[i % coloresBase.length];
            return `rgba(${color[0]}, ${color[1]}, ${color[2]}, 0.7)`;
        });

        const canvas = document.getElementById("myChart");

        // Destruye la gráfica anterior si existe
        if (window.miGrafico) {
            window.miGrafico.destroy();
        }

        // Registra el complemento de etiquetas
        Chart.register(ChartDataLabels);

        // Crea la gráfica de barras
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
        // Muestra errores al cargar el análisis
        console.error("Error al cargar el análisis de ventas:", error);
    }
}

// ==========================================
// INDICADORES KPI
// ==========================================

// GET - Consulta los indicadores de ventas
async function cargarKPIs() {
    try {
        const res = await fetch(`${API_URL}/api/analisis/kpis`);
        if (!res.ok) return;

        // Obtiene los indicadores
        const data = await res.json();

        // Actualiza los valores en pantalla
        document.getElementById("kpi-ingresos").textContent =
            `$${data.ingresos_totales.toLocaleString('es-MX', {minimumFractionDigits: 2})}`;

        document.getElementById("kpi-estrella").textContent = data.producto_estrella;

        document.getElementById("kpi-ticket").textContent =
            `$${data.ticket_promedio.toLocaleString('es-MX', {minimumFractionDigits: 2})}`;
    } catch (error) {
        // Muestra errores de consulta
        console.error("Error cargando KPIs:", error);
    }
}

// ==========================================
// GRÁFICA DE DONA
// ==========================================

// GET - Consulta los datos para la gráfica de dona
async function cargarGraficoTicket() {
    const canvas = document.getElementById("graficoTicket");
    if (!canvas) return;

    try {
        // Solicita los datos de ventas
        const res = await fetch(`${API_URL}/api/analisis/mas-vendidos`);

        if (!res.ok) {
            throw new Error(`Error HTTP: ${res.status}`);
        }

        const datos = await res.json();

        // Destruye la gráfica anterior si existe
        const graficaAnterior = Chart.getChart(canvas);

        if (graficaAnterior) {
            graficaAnterior.destroy();
        }

        // Comprueba si existen ventas
        if (!datos || datos.length === 0) {
            console.warn("No hay ventas registradas para mostrar en la gráfica.");

            const ctx = canvas.getContext("2d");
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            return;
        }

        // Crea la gráfica de dona
        window.graficoTicket = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: datos.map(d => d.producto),
                datasets: [{
                    data: datos.map(d => Number(d.monto_total)),
                    backgroundColor: [
                        "#2563eb",
                        "#0891b2",
                        "#059669",
                        "#7c3aed",
                        "#ea5800"
                    ],
                    borderWidth: 2,
                    borderColor: "#ffffff"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom"
                    }
                }
            }
        });

    } catch (error) {
        // Muestra errores al cargar la gráfica
        console.error("Error cargando gráfica ticket:", error);
    }
}

// ==========================================
// INICIALIZACIÓN
// ==========================================

// Carga los datos al abrir la página
document.addEventListener("DOMContentLoaded", () => {
    cargarProductos();
    cargarAnalisis();
    cargarGraficoTicket();
    cargarKPIs();
});

// Registra el evento para enviar el formulario
if (formProducto) {
    formProducto.addEventListener("submit", agregarProducto);
}
