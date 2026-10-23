const API_URL = "http://127.0.0.1:8000/productos";

// Selección de Elementos del DOM
const formProducto = document.getElementById("formProducto");
const tablaProductos = document.getElementById("tablaProductos");
const totalProductos = document.getElementById("totalProductos");


// 1. Función para Cargar Productos (GET)
async function cargarProductos() {
    try {
        const respuesta = await fetch(API_URL);
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
                <td class="text-success fw-bold">$${p.precio}</td>
                <td>
                    <span class="badge ${p.cantidad < 10 ? 'bg-danger' : 'bg-success'}">
                        ${p.cantidad} unidades
                    </span>
                </td>
                <td class="text-end">
                    <button class="btn btn-outline-danger btn-sm" onclick="eliminarProducto(${p.id})">
                        <i class="bi bi-trash"></i> Eliminar
                    </button>
                </td>
            `;
            tablaProductos.appendChild(fila);
        });

    } catch (error) {
        console.error("Error al cargar productos:", error);
    }
}

async function agregarProducto(event){
    event.preventDefault();

    var nombre = document.getElementById("nombre").value
    var precio = document.getElementById("precio").value
    var cantidad = document.getElementById("cantidad").value

    const nuevoContenido = {nombre, precio, cantidad}
    try {
        const respuesta = await fetch(API_URL, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(nuevoContenido)});

        if(respuesta){
            formProducto.reset();
            await cargarProductos();
        }else{
            console.error("Hubo algo malo al guardar")
        }
    } catch (error) {
        console.log(error)
    }
}

async function eliminarProducto(id_producto){
    event.preventDefault();

    try {
        const respuesta = await fetch("http://127.0.0.1:8000/productos/"+id_producto, {method: "DELETE", headers: {"Content-Type": "application/json"}});

        if(respuesta){
            await cargarProductos();
        }else{
            console.error("Hubo algo malo al eliminar")
        }
    } catch (error) {
        console.log(error)
    }
}
// ==========================================
// 3. Comprar Producto (POST /comprar)
// ==========================================
async function comprarProducto(id_producto) {
    try {
        const respuesta = await fetch(`${API_URL}/productos/${id_producto}/comprar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });

        const datos = await respuesta.json();

        if (respuesta.ok) {
            // Compra exitosa
            alert(datos.Message || "¡Compra realizada con éxito!");
            await cargarProductos(); // Recargar para ver el nuevo stock
        } else {
            // Manejo de errores específicos del backend
            let mensaje = datos.detail || datos.Message || "Error al procesar la compra";
            
            if (respuesta.status === 429) {
                mensaje = "¡Demasiadas peticiones! Tu middleware te está protegiendo. Espera un momento.";
            } else if (respuesta.status === 404) {
                mensaje = "El producto ya no existe en el inventario.";
            }
            
            alert(mensaje);
            await cargarProductos(); // Recargar por si el producto se eliminó al llegar a 0
        }
    } catch (error) {
        console.error("Error al comprar:", error);
        alert("Error de conexión al procesar la compra.");
    }
}


// Cargar catálogo al abrir la página
document.addEventListener("DOMContentLoaded", cargarProductos);


// Agregamos el evento para que se abre la función al dar clic en guardar producto
formProducto.addEventListener("submit", agregarProducto);
