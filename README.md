# StockFlow

Sistema de inventario para tiendas, desarrollado con **Django** (framework del lado del servidor) como evidencia para la evaluación: *Desarrollo de aplicaciones del lado del servidor con Django e Inteligencia Artificial*.

## ¿Por qué es escalable?

- **Modelos relacionales**: `Categoria`, `Producto` y `MovimientoStock` permiten crecer a multi-bodega o multi-sucursal agregando modelos sin reescribir los existentes.
- **Separación MTV/MVC**: lógica de negocio, datos y presentación desacoplados; se puede agregar una API REST (`django-rest-framework`) o app móvil reutilizando models y views.
- **SQLite → PostgreSQL**: cambiar de motor solo requiere modificar `settings.py`.
- **Despliegue estándar WSGI**: compatible con servicios como PythonAnywhere, Railway, Render o VPS con Nginx + Gunicorn.

## Tecnologías utilizadas

| Tecnología | Uso |
|---|---|
| Python 3.11 | Lenguaje del lado del servidor |
| Django 5.2 | Framework web MVT |
| SQLite | Base de datos (por configuración) |
| Faker *(paquete externo)* | Generación de datos de prueba |
| django-crispy-forms + crispy-bootstrap5 *(paquetes externos)* | Renderizado de formularios |
| Bootstrap 5 (CDN) | Estilos de interfaz |

## Cómo ejecutar el proyecto

```powershell
# 1. Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Aplicar migraciones
python manage.py migrate

# 4. (Opcional) Generar datos de prueba
python manage.py seed_datos --limpiar

# 5. Crear superusuario
python manage.py createsuperuser

# 6. Levantar el servidor
python manage.py runserver
```

Luego abrir `http://127.0.0.1:8000/`

**Superusuario de prueba:** usuario `admin` / contraseña `admin1234`

## Funcionalidades

- Panel con métricas: total de productos, unidades, valor del inventario y alertas de reposición.
- CRUD completo de productos (crear, listar, buscar por nombre/SKU, filtrar por categoría).
- Detalle de producto con registro de movimientos de stock (entradas/salidas) validados en el servidor.
- Alerta automática cuando el stock baja del mínimo (property `necesita_reposicion`).
- Panel de administración de Django configurado.

## Aplicación del patrón MVC (MTV en Django)

| Rol MVC | Componente Django | Archivo |
|---|---|---|
| Modelo | Models (datos y lógica de negocio) | `inventario/models.py` |
| Vista | Templates (presentación) | `templates/inventario/*.html` |
| Controlador | Views + URLs (flujo de la solicitud) | `inventario/views.py`, `inventario/urls.py` |

## Uso de IA como apoyo al desarrollo

1. **Diseño de interfaces**: Bootstrap 5 fue seleccionado con recomendaciones de IA para lograr una UI responsiva sin escribir CSS propio.
2. **Generación de datos de prueba**: la IA recomendó la librería **Faker** y ayudó a diseñar el set de datos coherente con el dominio (comando `seed_datos`). Los datos fueron validados revisando consistencia entre stock y movimientos.
3. **Verificación**: todas las sugerencias de la IA fueron probadas ejecutando `manage.py check`, migraciones y pruebas HTTP sobre las rutas principales.

## Protocolos, hosting y dominios (indicador 12)

- **Protocolo HTTP/HTTPS**: el navegador envía peticiones GET/POST al servidor Django (WSGI); en producción se sirve bajo HTTPS (TLS) mediante Nginx o el proxy del proveedor.
- **Servidor de desarrollo vs producción**: `runserver` es solo desarrollo; en producción se usa **Gunicorn/uWSGI** detrás de un servidor web inverso.
- **Hosting**: opciones compatibles con Django: PythonAnywhere, Railway, Render, Vercel (con adaptador), o un VPS (DigitalOcean, AWS EC2).
- **Dominio**: se registra un dominio (ej. `stockflow.cl`) en un registrador (NIC Chile, Namecheap) y se apunta vía DNS (registros A/CNAME) a la IP/dominio del hosting.

## Versión Frontend (prototipo sin servidor)

La carpeta `frontend/` contiene la misma aplicación como **frontend puro** (HTML + CSS + JavaScript), pensada para conectarse después con Django:

```
frontend/
├── index.html        # Panel con métricas y alertas
├── productos.html    # Listado + búsqueda + filtro por categoría
├── producto.html     # Detalle + registro de movimientos (?id=)
├── formulario.html   # Crear / editar producto (?id=)
├── css/styles.css
└── js/
    ├── datos.js       # Capa de datos (localStorage, replica los modelos Django)
    ├── dashboard.js
    ├── productos.js
    ├── producto.js
    └── formulario.js
```

- Los datos se simulan en `localStorage` (`StockFlow` en `js/datos.js`) usando la **misma estructura de los modelos Django**, por lo que la migración a backend es directa.
- Las validaciones replican la lógica del servidor (SKU único, salida no puede dejar stock negativo).
- Para verlo: abrir `frontend/index.html` en el navegador, o servirlo con `python -m http.server 8080 --directory frontend`.
- Para conectar con Django luego hay dos caminos: convertir las páginas a **templates** de Django, o mantener el frontend y consumir una **API REST** reemplazando `datos.js` por llamadas `fetch()`.

## Estructura del proyecto

```
web-basica/
├── manage.py
├── requirements.txt
├── db.sqlite3
├── stockflow/            # Configuración del proyecto
│   ├── settings.py       # Apps, BD, zona horaria, paquetes externos
│   ├── urls.py           # Rutas raíz
│   └── wsgi.py           # Punto de entrada WSGI (despliegue)
├── inventario/           # App principal
│   ├── models.py         # Categoria, Producto, MovimientoStock
│   ├── views.py          # Dashboard + CRUD
│   ├── forms.py          # Formularios con validación de servidor
│   ├── admin.py          # Registro en panel admin
│   └── management/commands/seed_datos.py   # Datos de prueba (Faker)
└── templates/            # Templates (Vista en MTV)
    ├── base.html
    └── inventario/*.html
```
