# StockFlow — Sistema de Gestión de Inventario para Comercios (Evaluación 1, 2 y 3: API RESTful)

Bienvenidos a mi proyecto del módulo **"Desarrollo de aplicaciones del lado del servidor"**. Es un sistema de gestión de inventario y bodega llamado **StockFlow**, que nace con datos de prueba generados con Faker y frontend estático (eval 1), evoluciona a una aplicación completa con persistencia relacional en MySQL, operaciones CRUD en el navegador, panel administrativo extendido y autenticación de usuarios con control de acceso por roles (eval 2), y que finalmente incorpora una arquitectura desacoplada mediante una API RESTful profesional con Django REST Framework y Simple JWT (eval 3).

Este README es mi **diario de trabajo**: lo voy actualizando en cada push con los pasos que voy completando.

---

# Unidad 1 / Evaluación 1 — Prototipo y Arquitectura MTV (Diario de trabajo)

### Qué hice con la ayuda de la IA

Le pedí a la IA que me apoyara diseñando el **frontend inicial** (HTML, CSS con Bootstrap 5 y JavaScript) mientras yo comenzaba a construir el backend con Django paso a paso, siguiendo las indicaciones de clase: el agente de IA apoya con el diseño visual y los datos de prueba, y yo estructuro y audito el backend.

**El prototipo inicial quedó así (carpeta `frontend/`):**
- `index.html` — panel principal con métricas generales del inventario.
- `productos.html` — catálogo con tabla y tarjetas de productos.
- `producto.html` — ficha individual para ver el detalle y simular movimientos de stock.
- `formulario.html` — pantalla para agregar nuevos artículos.
- `css/styles.css` — estilos personalizados con Bootstrap 5.
- `js/` — scripts que simulaban los datos en memoria antes de conectar Django.

---

### El backend que fui escribiendo (mi parte)

**Paso 1 — Entorno virtual:**
Creé el entorno virtual para aislar las dependencias del proyecto y que no choquen con librerías globales del sistema:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Paso 2 — Paquetes instalados:**
Instalé `Django`, `django-crispy-forms` junto a `crispy-bootstrap5` (para renderizar formularios limpios con Bootstrap sin escribir HTML repetitivo) y `faker` (para generar datos sintéticos realistas de bodega):
```
asgiref==3.12.1
crispy-bootstrap5==2026.3
Django==5.2.17
django-crispy-forms==2.7
Faker==40.37.0
sqlparse==0.6.0
tzdata==2026.3
```
Y los guardé en `requirements.txt`.

**Paso 3 — Proyecto y aplicación modular:**
Inicialicé el proyecto base `stockflow` y la app de negocio `inventario`:
```powershell
python -m django startproject stockflow .
python manage.py startapp inventario
```
En `stockflow/settings.py` registré la app `inventario`, configuré el idioma en español (`LANGUAGE_CODE = 'es'`) y la zona horaria de Chile (`TIME_ZONE = 'America/Santiago'`).

**Paso 4 — Modelos con reglas de negocio:**
En `inventario/models.py` definí las tres entidades principales del comercio:
- `Categoria`: agrupa los productos (Abarrotes, Bebidas, Limpieza, etc.).
- `Producto`: nombre, código `sku` único (`unique=True`), precio unitario en `DecimalField` (para que los cálculos de plata no pierdan precisión como pasa con Float), stock actual y stock mínimo.
  - **Decisión de integridad clave:** relacioné `Producto` con `Categoria` usando `ForeignKey` con `on_delete=models.PROTECT`. Así evito que alguien borre una categoría que todavía tiene productos adentro, impidiendo registros huérfanos.
  - **Operaciones calculadas:** agregué la propiedad `valor_inventario` (`self.precio * self.stock`) y `necesita_reposicion` (`self.stock <= self.stock_minimo`).
- `MovimientoStock`: historial de entradas y salidas de mercadería, vinculado al producto con `on_delete=models.CASCADE` (si el producto se descataloga, su historial se borra con él).

**Paso 5 — Migraciones iniciales:**
Generé las migraciones con `python manage.py makemigrations inventario` y las apliqué a la base de datos con `python manage.py migrate`.

**Paso 6 — Comando de carga de datos con Faker:**
Para no crear productos uno por uno a mano, construí el comando `inventario/management/commands/seed_datos.py`. Con la ayuda de Faker en español, poblé la base de datos con 5 categorías comerciales y 20 productos con sus movimientos iniciales:
```powershell
python manage.py seed_datos --limpiar
```

**Paso 7 — Panel de Administración inicial:**
En `inventario/admin.py` registré los modelos usando `@admin.register`, configuré las columnas visibles (`list_display`), agregué búsqueda por SKU y nombre (`search_fields`) y creé el superusuario inicial para entrar a `/admin/`.

**Paso 8 — Templates y vistas MVT:**
- Creé `templates/base.html` con la barra de navegación, bloques de contenido y mensajes de alerta.
- Creé las vistas en `inventario/views.py`: `dashboard` (métricas de existencias y valor del inventario), `lista_productos` (con filtros `Q` acumulativos por texto y categoría) y `detalle_producto` (para ver el stock y registrar movimientos con formulario POST).
- Conecté las rutas en `inventario/urls.py` e incluí la app en `stockflow/urls.py`.

**Paso 9 — Pruebas unitarias de la primera etapa:**
Creé una suite de pruebas en `inventario/tests.py` para asegurar que las operaciones matemáticas de los modelos y las validaciones no fallaran al correr `python manage.py test`.

---

### Evidencias del proceso con IA (Eval 1)

#### 1. Estado inicial — Catálogo en formato tabla simple
Al comienzo el catálogo mostraba una tabla básica de productos sin mayor jerarquía visual:
![Catálogo inicial en tabla](evidencias/estado-inicial-tabla.jpg)

#### 2. Prompt entregado a la IA
Instrucción proporcionada al modelo de IA para rediseñar la interfaz visual y hacerla moderna, limpia y responsiva:
![Prompt entregado a la IA](evidencias/prompt-ia.jpg)

#### 3. Resultado final — Interfaz moderna y adaptada
Así quedó el catálogo optimizado con tarjetas, estados de stock con colores y diseño responsivo para PC y celulares:
![Interfaz final optimizada](evidencias/estado-final-interfaz.jpg)

---

# Unidad 2 / Evaluación 2 — Framework Back End (Diario de trabajo)

> Acá registro la evolución de mi proyecto durante la **Unidad 2**, transformando el prototipo inicial en una aplicación web completa con persistencia relacional en **MySQL (Docker)**, operaciones CRUD completas en el navegador (Crear, Modificar, Eliminar con confirmación), Django Admin profesional extendido, sistema de autenticación con roles de usuario (RBAC) y políticas avanzadas de sesión.

### Comparativa: ¿Qué teníamos en la Unidad 1 vs qué incorporamos en la Unidad 2?

| Característica | Unidad 1 (Evaluación 1) | Unidad 2 (Evaluación 2) |
| :--- | :--- | :--- |
| **Base de Datos** | SQLite local básico | **MySQL 8.0 en contenedor Docker** (compatible con WampServer en puerto 3306) con driver `mysqlclient` |
| **Persistencia** | Datos cargados mediante script | Persistencia activa con transacciones atómicas (`@transaction.atomic`) en capa de servicios |
| **Operaciones** | Solo lectura (`Read`) y registro básico de movimientos | **CRUD completo** en la web: Crear, Listar, Detalle, Modificar y Eliminar productos y categorías |
| **Formularios** | Formularios simples | `ModelForm` avanzados con validación en servidor (bloqueo estricto de salidas con stock insuficiente) |
| **Django Admin** | Configuración básica de columnas | **Admin profesional extendido** con filtros personalizados (`SimpleListFilter`), inlines de historial y acciones masivas |
| **Autenticación y Roles** | Solo superusuario para entrar a `/admin/` | App `cuentas` con **3 roles (Administrador, Bodeguero, Vendedor)**, permisos por grupo y mixins de control de acceso |
| **Sesiones y Seguridad** | Navegación estándar | Middleware de inactividad (expira la sesión tras 30 min sin peticiones) y protección CSRF obligatoria |

---

### Para recordar: Cómo tengo corriendo MySQL en Docker (o WampServer)

Para cumplir con la persistencia en base de datos relacional de la Unidad 2, dejé la base de datos conectada a **MySQL 8.0**:

#### 1. Contenedor Docker de MySQL
Tengo corriendo el contenedor en el puerto local `3306`:
```powershell
docker ps
```
El contenedor se llama `cursos_mysql` y tiene la base de datos `stockflow_db` creada con juego de caracteres `utf8mb4`:
```sql
CREATE DATABASE IF NOT EXISTS stockflow_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

*(Nota: si en vez de Docker se usa WampServer o XAMPP, funciona de forma idéntica porque ambos atienden en el puerto 3306 con usuario root).*

#### 2. Conector oficial de MySQL
Instalé el driver nativo de alto rendimiento `mysqlclient` en el entorno virtual y lo agregué a `requirements.txt`:
```powershell
.\venv\Scripts\pip.exe install mysqlclient
```

#### 3. Variables de entorno desacopladas (`.env`)
En la raíz del proyecto creé el archivo `.env` para no dejar contraseñas quemadas en el código (`stockflow/entorno.py` las lee automáticamente):
```ini
DJANGO_SECRET_KEY=clave_secreta_super_segura_stockflow_brayan_inacap_2026
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

DJANGO_DB_ENGINE=django.db.backends.mysql
DJANGO_DB_NAME=stockflow_db
DJANGO_DB_HOST=127.0.0.1
DJANGO_DB_PORT=3306
DJANGO_DB_USER=root
DJANGO_DB_PASSWORD=root
```
*(Si en algún momento quiero volver a SQLite para una prueba rápida, basta con cambiar `DJANGO_DB_ENGINE=django.db.backends.sqlite3` en el `.env` y el código no se rompe).*

---

### Registro de avances paso a paso — Unidad 2

A continuación detallo todo lo que fui programando para completar la Unidad 2:

#### Paso 1 — Migraciones a MySQL
Con el archivo `.env` apuntando a MySQL, ejecuté las migraciones para crear todas las tablas en `stockflow_db`:
```powershell
python manage.py migrate
```
Django creó las tablas nativas de autenticación, sesiones y las tablas de nuestras dos apps (`inventario` y `cuentas`).

#### Paso 2 — Creación de la app `cuentas` y sistema de roles (RBAC)
Para no mezclar la autenticación con el inventario, creé una app dedicada:
```powershell
python manage.py startapp cuentas
```
- **Modelo de Perfil (`cuentas/models.py`):** creé `PerfilUsuario` conectado uno a uno (`OneToOneField`) con el modelo `User` de Django. Define tres roles:
  - `ADMINISTRADOR`: control total del catálogo, usuarios y borrado.
  - `BODEGUERO`: puede crear, editar productos y registrar entradas o ajustes de stock.
  - `VENDEDOR`: solo puede ver productos y registrar salidas por ventas.
- **Permisos y mixins (`cuentas/permisos.py`):** creé `RolRequeridoMixin` para proteger las vistas de clase. Si un usuario sin el rol requerido intenta entrar por la URL, Django le deniega el acceso (403 Forbidden).

#### Paso 3 — Comando de creación de roles y usuarios demo
Construí el comando `cuentas/management/commands/crear_roles.py`. Este script crea automáticamente los grupos de Django con sus permisos exactos y genera tres cuentas de prueba para evaluar los accesos:
```powershell
python manage.py crear_roles --limpiar
```
Las cuentas listas para usar son:
- **`admin.demo`** (clave: `Stockflow2026`) — Rol: Administrador.
- **`bodega.demo`** (clave: `Stockflow2026`) — Rol: Bodeguero.
- **`ventas.demo`** (clave: `Stockflow2026`) — Rol: Vendedora.
- Además creé mi superusuario personal: **`brayan`** (clave: `admin1234`).

#### Paso 4 — Django Admin Profesional Extendido
Personalicé a fondo `inventario/admin.py` para ir más allá de un admin básico:
- **Filtros personalizados con expresiones `F`:** creé la clase `StockBajoFilter` (hereda de `SimpleListFilter`). Compara a nivel de base de datos SQL si `stock <= F('stock_minimo')`, mostrando un filtro lateral *"Necesitan reposición"* muy útil para el bodeguero.
- **Edición en línea con `TabularInline`:** con `MovimientoStockInline` incrusté el historial de entradas y salidas dentro de la misma pantalla de edición del producto.
- **Acciones masivas:** agregué acciones en lote para activar o desactivar productos seleccionados con un solo clic.
- **Auditoría con logging:** configuré `logging.getLogger('stockflow.admin')` para dejar registro en consola de las operaciones administrativas.

#### Paso 5 — Vistas CRUD completas en el frontend
En `inventario/views.py` implementé las 4 operaciones CRUD usando Vistas Basadas en Clases (CBV) protegidas por rol y sesión:
- **Create:** `ProductoCrearView` (`CreateView`) y `CategoriaCrearView`.
- **Read:** `ProductoListView` (`ListView`) con paginación, `ProductoDetalleView` (`DetailView`) e `HistorialMovimientosView`.
- **Update:** `ProductoEditarView` (`UpdateView`), `CategoriaEditarView` y `AjusteStockView`.
- **Delete:** `ProductoEliminarView` (`DeleteView`) y `CategoriaEliminarView`.
  - **Manejo de excepciones:** capturé el error `ProtectedError` para que si alguien intenta borrar una categoría con productos asignados, el sistema no se caiga con error 500, sino que muestre una alerta amigable avisando que no se puede borrar.

#### Paso 6 — Capa de servicios y transacciones atómicas
Para mantener el código ordenado y evitar vistas gigantes:
- **`inventario/servicios.py`:** acá encapsulé las mutaciones del inventario (`registrar_movimiento`, `ajustar_stock`, `activar_productos`). Usé el decorador `@transaction.atomic` para garantizar que la actualización del stock y la creación del movimiento ocurran en un solo bloque atómico. Si algo falla, se cancela todo (Rollback).
- **`inventario/selectores.py`:** acá agrupé las consultas de lectura optimizadas (`metricas_dashboard`, `productos_filtrados`).
- **`inventario/forms.py`:** en `MovimientoForm.clean()` validé en el servidor que si la operación es de salida (`SALIDA`), la cantidad no supere el stock actual. Si lo supera, arroja un `ValidationError` impidiendo existencias negativas.

#### Paso 7 — Sesiones y blindaje de seguridad
- **Middleware de inactividad (`cuentas/middleware.py`):** creé `SesionInactivaMiddleware` y lo registré en `settings.py`. Guarda la marca de tiempo de la última petición en `request.session['ultima_actividad']`. Si transcurren más de 30 minutos sin actividad, destruye la sesión y redirige al login con un mensaje explicativo.
- **Protección CSRF:** aseguré que el 100% de los formularios de login, creación, edición y borrado lleven el token `{% csrf_token %}`.
- **Protección de rutas:** todas las vistas de administración heredan de `LoginRequiredMixin` y `RolRequeridoMixin`.

#### Paso 8 — Suite de 89 Pruebas Automatizadas
Para verificar que todo funcione perfecto y nada se rompa, amplié la suite de pruebas unitarias en `inventario/tests.py` y `cuentas/tests.py`:
- Pruebas de modelos, cálculos de stock y propiedades.
- Pruebas de validación de formularios y rechazo de stock negativo.
- Pruebas de permisos: que un Vendedor no pueda entrar a borrar productos ni a cambiar precios.
- Pruebas de transacciones atómicas y rollback.

Al ejecutar `python manage.py test`, las **89 pruebas pasan con resultado OK**.

---

# Unidad 3 / Evaluación 3 — API RESTful con Django REST Framework y JWT (Diario de trabajo)

> Acá registro la evolución de mi proyecto durante la **Unidad 3**, transformando StockFlow en una plataforma con arquitectura desacoplada mediante una **API RESTful profesional construida con Django REST Framework (DRF)**, protegida con autenticación stateless mediante **JSON Web Tokens (Simple JWT)**, enriquecida con validaciones de negocio en el servidor, blindada contra ataques de saturación mediante Throttling, integrada con una API externa de proveedores mayoristas para benchmarking de mercado y consumida de forma reactiva desde el navegador con JavaScript `fetch()`.

### Comparativa: ¿Qué teníamos en la Unidad 2 vs qué incorporamos en la Unidad 3?

| Característica | Unidad 2 (Evaluación 2) | Unidad 3 (Evaluación 3) |
| :--- | :--- | :--- |
| **Arquitectura** | Monolito tradicional SSR (HTML acoplado al servidor) | **Arquitectura desacoplada cliente-servidor** exponiendo recursos JSON |
| **Protocolo de Entrega** | Vistas basadas en clases renderizando plantillas | **API RESTful modular con ViewSets y DefaultRouter** en `/api/v1/` |
| **Autenticación** | Sesiones de navegador tradicionales con cookies en BD | **Autenticación stateless con JSON Web Tokens (Simple JWT)** |
| **Serialización** | Formularios Django ModelForm para formularios HTML | **ModelSerializer explícitos** sin `__all__`, con campos calculados y validaciones |
| **Seguridad de Acceso** | Mixin de roles (`RolRequeridoMixin`) en vistas HTML | **Permisos `IsAuthenticatedOrReadOnly`** (lectura libre, mutación con Bearer token) |
| **Defensa contra Ataques** | Timeout de inactividad de sesión de 30 minutos | **Rate Limiting / Throttling activo** (`100/día` anónimos, `1000/día` autenticados) |
| **Integración Externa** | No contaba con conexión a servicios de terceros | **Servicio de proveedores mayoristas** consumiendo la API externa de DummyJSON |
| **Frontend Reactivo** | Recarga completa de página en cada navegación | **Interfaz reactiva con JavaScript `fetch()`** con búsqueda en vivo sin recargas |
| **Pruebas de la API** | 89 pruebas unitarias de modelos y vistas HTML | **Suite automatizada con `APITestCase`**, colección Postman y archivo `.http` |

---

### Registro de avances paso a paso — Unidad 3

A continuación detallo todo lo que fui programando para completar la Unidad 3:

#### Paso 1 — Instalación de dependencias de la API
Agregué al archivo `requirements.txt` e instalé en el entorno virtual los paquetes necesarios:
- `djangorestframework`: framework profesional para construir la API RESTful.
- `djangorestframework-simplejwt`: proveedor de autenticación stateless con tokens JWT.
- `django-filter`: motor de filtrado acumulativo sobre los querysets del ORM.
- `python-dotenv`: gestión desacoplada de variables de entorno.

#### Paso 2 — Configuración en `stockflow/settings.py`
Registré las aplicaciones en `INSTALLED_APPS` y configuré las directrices globales:
- **Autenticación:** configuré `DEFAULT_AUTHENTICATION_CLASSES` con `JWTAuthentication`.
- **Permisos globales:** establecí `IsAuthenticatedOrReadOnly` para permitir lectura pública del catálogo y exigir token Bearer para mutaciones (crear, editar, eliminar).
- **Paginación:** configuré `PageNumberPagination` con un tamaño estándar de 10 elementos por página.
- **Throttling (Rate Limiting):** activé `AnonRateThrottle` (`100/día`) y `UserRateThrottle` (`1000/día`) para frenar ataques de fuerza bruta y denegación de servicio (DoS).
- **Ciclo de vida Simple JWT:** definí un tiempo de vida corto de **15 minutos** para el `ACCESS_TOKEN_LIFETIME` y **1 día** para el `REFRESH_TOKEN_LIFETIME`, firmado criptográficamente con algoritmo `HS256` y la `SECRET_KEY` del archivo `.env`.

#### Paso 3 — Serializadores explícitos (`inventario/serializers.py`)
Construí serializadores dedicados para los tres modelos de inventario, aplicando una estricta regla de diseño:
- **Prohibición de `fields = '__all__' `:** listé cada campo de forma explícita para evitar vulnerabilidades de asignación masiva (Mass Assignment) y exposición accidental de datos internos.
- **Campos calculados `ReadOnlyField`:** enriquecí la respuesta JSON con `categoria_nombre`, `necesita_reposicion`, `valor_inventario` y `porcentaje_stock`, permitiendo que el cliente reciba datos procesados sin hacer consultas SQL adicionales.
- **Validaciones en el servidor:** programé validaciones en `validate_precio` (>= 0), `validate_stock` (>= 0) y normalización de mayúsculas en `validate_sku`.
- **Integración con la capa de servicios:** en `MovimientoStockSerializer.create()`, delegué la escritura al servicio transaccional atómico `registrar_movimiento` (`inventario/servicios.py`), asegurando que las salidas verifiquen stock suficiente antes de guardar.

#### Paso 4 — ViewSets y rutas RESTful (`inventario/api_views.py` y `api_urls.py`)
- Implementé `CategoriaViewSet`, `ProductoViewSet` y `MovimientoStockViewSet` heredando de `viewsets.ModelViewSet`.
- Apliqué optimización de consultas ORM con `select_related('categoria')` para resolver el problema de consulta N+1.
- Conecté `DjangoFilterBackend`, `SearchFilter` y `OrderingFilter` para habilitar búsquedas por texto y ordenamiento por precio o stock.
- Registré los recursos en el `DefaultRouter` generando rutas canónicas con sustantivos en plural:
  - `/api/v1/categorias/`
  - `/api/v1/productos/`
  - `/api/v1/movimientos/`

#### Paso 5 — Endpoints de Autenticación JWT (`stockflow/urls.py`)
Conecté las vistas nativas de Simple JWT:
- `POST /api/token/` (`TokenObtainPairView`): recibe credenciales y entrega el par de tokens (`access` y `refresh`).
- `POST /api/token/refresh/` (`TokenRefreshView`): permite renovar el token de acceso vencido.

#### Paso 6 — Servicio de Proveedores Mayoristas con API Externa (`inventario/servicios_api.py`)
Para incorporar una funcionalidad realista y única para la gestión de bodega:
- Desarrollé una capa de servicio que consulta en vivo la API externa de **DummyJSON Products** (`https://dummyjson.com/products`).
- Permite al encargado de compras consultar artículos de proveedores mayoristas para benchmarking de precios internacionales en dólares y disponibilidad de stock.
- Expuse la funcionalidad en el endpoint propio `GET /api/v1/proveedores/`.
- **Blindaje de red:** implementé un tiempo de espera estricto `timeout=3` segundos con `urllib.request` y captura de excepciones para que una falla en internet nunca bloquee el servidor local.

#### Paso 7 — Frontend Desacoplado con JavaScript `fetch()` (`templates/inventario/catalogo_api.html`)
- Diseñé una vista web interactiva accesible desde el menú principal en `/catalogo-api/` (**⚡ API En Vivo**).
- Consume de manera asíncrona los endpoints `/api/v1/productos/` y `/api/v1/proveedores/` mediante `fetch()`.
- Incorpora buscador instantáneo con debounce y filtros de orden sin recargar la página web.

#### Paso 8 — Suite de Pruebas Automatizadas para la API (`inventario/tests_api.py`)
Escribí 8 pruebas automatizadas utilizando `rest_framework.test.APITestCase`:
1. `test_listado_productos_publico`: valida lectura pública paginada con código 200.
2. `test_detalle_producto_y_propiedades_calculadas`: valida campos calculados en la ficha individual.
3. `test_creacion_sin_token_rechazada`: valida que peticiones de escritura anónimas devuelvan 401 Unauthorized.
4. `test_creacion_con_token_jwt`: valida login contra `/api/token/`, cabecera `Bearer` y respuesta 201 Created.
5. `test_validacion_precio_negativo`: valida que precios menores a cero retornen 400 Bad Request.
6. `test_validacion_salida_mayor_a_stock`: valida que salidas superiores a existencias retornen 400 Bad Request.
7. `test_recurso_inexistente_retorna_404_json`: valida respuesta consistente en JSON con clave `detail`.
8. `test_endpoint_proveedores_externos`: valida integración con el servicio externo usando `@patch` para aislamiento.

Todas las pruebas pasan con resultado exitoso al correr `python manage.py test inventario.tests_api`.

#### Paso 9 — Colección de Postman y Documentación de Pruebas
- Generé la colección oficial `docs/unidad 3/StockFlow_API.postman_collection.json` con pruebas automáticas que guardan el token JWT en variables de entorno.
- Creé el archivo `docs/unidad 3/pruebas_api.http` para pruebas directas en el editor.
- Documenté en `docs/unidad 3/EVIDENCIAS_IA_Y_SEGURIDAD.md` la matriz de riesgos técnicos detectados al usar IA y las mitigaciones de seguridad aplicadas.
- Elaboré la guía de defensa oral en `GUIA_DEFENSA_EVA3.md`.

---

### Uso de IA como Copiloto y Auditoría Crítica Humana (Unidad 3)

Durante el desarrollo de esta unidad, apliqué un control riguroso sobre las propuestas de la IA, mitigando los riesgos técnicos de la materia:
1. **Riesgo de exposición silenciosa:** La IA suele sugerir `fields = '__all__'` en los serializadores para ahorrar código. Rechacé tajantemente esta sugerencia, exigiendo listas explícitas de atributos para garantizar el principio de mínimo privilegio.
2. **Riesgo de alucinación de campos:** Cotejé cada campo declarado en los serializadores con la estructura real de los modelos en `inventario/models.py`.
3. **Riesgo de confidencialidad en JWT:** Comprobé que el payload Base64 del token solo contenga identificadores y marcas de tiempo (`user_id`, `exp`, `iat`), asegurando que jamás viajen contraseñas, correos ni datos sensibles que puedan ser leídos por terceros.
4. **Resiliencia en llamadas de red:** Corregí las peticiones HTTP hacia servicios externos añadiendo tiempos de espera (`timeout=3s`) y captura de errores para que la aplicación nunca se caiga si internet falla.

El desglose completo de prompts, sugerencias preliminares de la IA y adaptaciones finales se encuentra documentado en [`docs/unidad 3/EVIDENCIAS_IA_Y_SEGURIDAD.md`](docs/unidad%203/EVIDENCIAS_IA_Y_SEGURIDAD.md).

---

### Evidencias de la Unidad 3 (API RESTful y Consumo Desacoplado)

1. **Browsable API oficial de Django REST Framework (`/api/v1/productos/`):**
   Respuesta estructurada en formato JSON puro con código HTTP 200 OK, cabeceras de servidor, paginación integrada y soporte para filtros.
2. **Catálogo dinámico desacoplado consumiendo la API con JavaScript `fetch()` (`/catalogo-api/`):**
   Interfaz cliente que consume los datos de los endpoints en tiempo real, permitiendo filtrar por categorías y buscar artículos de bodega instantáneamente sin recargar la página.
3. **Autenticación Stateless con Tokens JWT (`/api/token/`):**
   Endpoint que emite credenciales temporales firmadas criptográficamente con HS256 para autorizar operaciones protegidas.
4. **Endpoint de Categorías con Conteo Calculado (`/api/v1/categorias/`):**
   Listado de recursos relacionales serializado explícitamente sin exponer atributos internos.
5. **Endpoint de Movimientos de Stock Transaccional (`/api/v1/movimientos/`):**
   Registro atómico de entradas y salidas de bodega con validación estricta de existencias físicas.
6. **Consumo de API REST Externa (`DummyJSON Products`) para Proveedores Mayoristas:**
   Servicio de benchmarking de precios internacionales y catálogo de compras para abastecimiento de bodega.
7. **Endpoint de Proveedores en nuestra Browsable API (`/api/v1/proveedores/`):**
   Endpoint propio que expone la integración y catálogo mayorista para clientes REST.

---

## Cómo correr el proyecto

### 1. Iniciar MySQL (Docker)
Verificar que el contenedor de MySQL esté activo en el puerto `3306`:
```powershell
docker ps
```
*(Si no tienes Docker encendido, puedes probar con SQLite configurando temporalmente `DJANGO_DB_ENGINE=django.db.backends.sqlite3` en el archivo `.env`).*

### 2. Entorno virtual y dependencias
```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Instalar dependencias completas (incluye DRF y Simple JWT)
pip install -r requirements.txt
```

### 3. Migrar y poblar la base de datos
```powershell
# Aplicar migraciones
python manage.py migrate

# Crear roles y usuarios de prueba
python manage.py crear_roles --limpiar

# Poblar con datos de prueba realistas
python manage.py seed_datos --limpiar
```

### 4. Correr las pruebas automatizadas
```powershell
# Correr pruebas de la API RESTful (Evaluación 3)
python manage.py test inventario.tests_api

# Correr la suite completa de inventario
python manage.py test inventario
```

### 5. Iniciar el servidor local
```powershell
python manage.py runserver
```

### Enlaces útiles de la plataforma:
- **Panel Principal:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Catálogo Reactivo con fetch() (Evaluación 3):** [http://127.0.0.1:8000/catalogo-api/](http://127.0.0.1:8000/catalogo-api/)
- **Explorador Interactivo DRF (Evaluación 3):** [http://127.0.0.1:8000/api/v1/](http://127.0.0.1:8000/api/v1/)
- **Endpoint Proveedores Mayoristas (Evaluación 3):** [http://127.0.0.1:8000/api/v1/proveedores/](http://127.0.0.1:8000/api/v1/proveedores/)
- **Obtención de Tokens JWT (POST):** [http://127.0.0.1:8000/api/token/](http://127.0.0.1:8000/api/token/)
- **Catálogo de Productos Tradicional (CRUD):** [http://127.0.0.1:8000/productos/](http://127.0.0.1:8000/productos/)
- **Iniciar Sesión:** [http://127.0.0.1:8000/cuentas/ingresar/](http://127.0.0.1:8000/cuentas/ingresar/)
- **Panel de Administración Django:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
