# Evidencias de Uso Crítico de Inteligencia Artificial y Auditoría de Seguridad

> **Proyecto:** StockFlow — Sistema de Gestión de Inventario  
> **Estudiante:** Brayan Castillo  
> **Enfoque:** Auditoría técnica de la capa de API RESTful, autenticación stateless con JSON Web Tokens (JWT) e integración resiliente de servicios externos.

---

## 1. Filosofía de Trabajo con la Inteligencia Artificial

Durante el desarrollo de esta etapa, la inteligencia artificial actuó como copiloto técnico para proponer estructuras iniciales de código. Sin embargo, todo el código fue auditado, modificado y validado por el estudiante para garantizar que cumpliera con los estándares de seguridad, consistencia de datos y rendimiento en servidores de producción.

> *"La inteligencia artificial acelera la escritura del código esqueleto, pero es el desarrollador quien audita, corrige las vulnerabilidades y toma las decisiones de arquitectura definitivas."*

A continuación se documentan los riesgos técnicos identificados, las correcciones aplicadas y los prompts reales de desarrollo.

---

## 2. Matriz de Auditoría Crítica: Riesgos de la IA vs Mitigaciones del Estudiante

| Riesgo Técnico Identificado | Comportamiento Típico de la IA | Peligro en Producción | Decisión y Corrección Humana Aplicada |
| :--- | :--- | :--- | :--- |
| **1. Exposición Silenciosa de Datos** | La IA tiende a sugerir `fields = '__all__'` en los serializadores para ahorrar líneas de código. | Cualquier atributo interno futuro (ej. márgenes de ganancia, costos de adquisición de bodega, claves foráneas sensibles) queda expuesto en el JSON público. | **PROHIBICIÓN TAJANTE de `__all__`**. Se definieron listas explícitas de atributos en cada serializador (`CategoriaSerializer`, `ProductoSerializer`, `MovimientoStockSerializer`). |
| **2. Alucinación de Atributos** | La IA inventa campos que suenan lógicos pero no existen en el modelo de Django (ej. `codigo_barra`, `descuento`, `proveedor_id`). | La aplicación arroja excepciones `AttributeError` o `FieldError` en tiempo de ejecución al iniciar o consultar la API. | **Cotejo estricto línea por línea** contra `inventario/models.py`. Cada campo serializado fue contrastado con los modelos ORM preexistentes. |
| **3. Vulnerabilidad de Confidencialidad en JWT** | La IA propone guardar datos personales del usuario o roles dentro del payload del token para "ahorrar consultas a la base de datos". | El payload de un JWT está codificado en **Base64URL, NO CIFRADO**. Cualquier persona que intercepte el token puede leerlo inmediatamente. | **Blindaje del Payload**: solo se autorizó el uso de identificadores técnicos mínimos (`user_id`, `iat`, `exp`), impidiendo el tránsito de correos, contraseñas o datos sensibles. |
| **4. Fuga de Credenciales y Claves Privadas** | La IA escribe claves y contraseñas fijas (`hardcoded`) dentro de `settings.py`. | Si el proyecto se sube a un repositorio público en GitHub, la `SECRET_KEY` queda expuesta, permitiendo forjar tokens falsificados. | **Aislamiento mediante `.env`**: integración con variables de entorno, exclusión obligatoria en `.gitignore` y provisión de `.env.example` sanitizado. |
| **5. Omisión de Límites de Petición (Throttling)** | La IA omite defensas contra ataques de fuerza bruta o saturación de peticiones. | Un atacante puede saturar `/api/token/` probando contraseñas por diccionario o colapsar el servidor con millones de peticiones. | **Configuración de Throttling**: implementación de `AnonRateThrottle` (100 req/día) y `UserRateThrottle` (1000 req/día) en `REST_FRAMEWORK`. |
| **6. Dependencia Frágil de Servicios Externos** | La IA propone llamadas de red sin timeout ni bloques de captura robustos. | Si el servicio externo (ej. `dummyjson.com`) cae o responde lento, todo el hilo de ejecución de Django se bloquea o cae. | **Capa de Servicios Desacoplada**: uso de `urllib.request` con `timeout=3s`, bloques `try/except` y fallback elegante a estado `disponible: false`. |

---

## 3. Registro Detallado de Prompts y Adaptaciones

### Caso 1: Serialización de Datos y Reglas de Negocio en Servidor

* **Prompt suministrado a la IA:**
  > *"Genera los ModelSerializer de Django REST Framework para Categoria, Producto y MovimientoStock. Incluye validaciones para que el precio no sea negativo, que el stock inicial no sea negativo, que el SKU quede normalizado en mayúsculas y que en los movimientos de salida se valide que la cantidad a retirar no supere las existencias físicas en bodega."*

* **Sugerencia inicial de la IA (con riesgos detectados):**
  ```python
  # Sugerencia IA insegura
  class ProductoSerializer(serializers.ModelSerializer):
      class Meta:
          model = Producto
          fields = '__all__'  # <-- RIESGO: Exposición silenciosa y sobreasignación masiva
  ```

* **Auditoría y corrección humana aplicada (`inventario/serializers.py`):**
  1. Se reemplazó `fields = '__all__'` por una lista explícita de los campos requeridos por el negocio.
  2. Se configuró `read_only_fields = ['fecha_registro', 'actualizado_en']` para que el cliente no pueda manipular fechas arbitrarias.
  3. Se añadieron campos calculados `ReadOnlyField` (`categoria_nombre`, `necesita_reposicion`, `valor_inventario`, `porcentaje_stock`), entregando datos procesados en el JSON sin obligar al frontend a hacer peticiones adicionales.
  4. Se codificaron los métodos `validate_precio`, `validate_stock`, `validate_stock_minimo` y `validate_sku` para garantizar validación en el servidor antes de tocar la base de datos.
  5. En `MovimientoStockSerializer`, se vinculó el método `create()` directamente con el servicio transaccional atómico `registrar_movimiento` de `inventario/servicios.py`, asegurando que cada movimiento registrado por API descuente o sume existencias físicas de forma indivisible.

---

### Caso 2: Autenticación Stateless y Ciclo de Vida de Tokens (JWT)

* **Prompt suministrado a la IA:**
  > *"Configura en Django REST Framework la autenticación stateless mediante JWT con djangorestframework-simplejwt. Establece permisos para que cualquier visitante pueda leer productos pero solo usuarios con token puedan crear, modificar o eliminar. Define tiempos de expiración seguros y endpoints para login y refresh."*

* **Sugerencia inicial de la IA (con riesgos detectados):**
  ```python
  # Sugerencia IA sin aislamiento de credenciales
  SECRET_KEY = 'django-insecure-clave-fija-en-el-codigo'  # <-- RIESGO: Clave privada expuesta
  SIMPLE_JWT = {
      'ACCESS_TOKEN_LIFETIME': timedelta(days=30),  # <-- RIESGO: Token de acceso eterno
  }
  ```

* **Auditoría y corrección humana aplicada (`stockflow/settings.py` y `stockflow/urls.py`):**
  1. Se mantuvo la `SECRET_KEY` aislada hacia el archivo `.env`.
  2. Se corrigió el tiempo de vida del **Access Token a solo 15 minutos** (vida corta), reduciendo drásticamente la ventana de vulnerabilidad en caso de interceptación de tráfico.
  3. Se configuró el **Refresh Token en 1 día** (vida media) únicamente para solicitar nuevos tokens de acceso vía `POST /api/token/refresh/`.
  4. Se estableció el algoritmo estándar `HS256` y el prefijo canónico `Authorization: Bearer <Token>`.
  5. Se definió `DEFAULT_PERMISSION_CLASSES = ('rest_framework.permissions.IsAuthenticatedOrReadOnly',)` para que el catálogo sea de libre lectura pública pero la mutación de datos requiera credenciales válidas.

---

### Caso 3: Enrutamiento RESTful y Limitación de Tasa (Throttling)

* **Prompt suministrado a la IA:**
  > *"Crea los ViewSets para los modelos de inventario y regístralos en un router de DRF siguiendo las mejores prácticas RESTful. Añade filtros de búsqueda, ordenamiento y medidas contra ataques de fuerza bruta."*

* **Sugerencia inicial de la IA:**
  La IA propuso rutas singulares (`router.register('producto', ProductoViewSet)`) y omitió la optimización de consultas SQL y el rate limiting.

* **Auditoría y corrección humana aplicada (`inventario/api_views.py` y `stockflow/settings.py`):**
  1. **Nombres canónicos en plural**: se configuraron `productos`, `categorias` y `movimientos` respetando las directrices de la arquitectura RESTful.
  2. **Optimización de consultas ORM**: se incorporó `select_related('categoria')` en `ProductoViewSet` y `select_related('producto', 'registrado_por')` en `MovimientoStockViewSet`, resolviendo el problema de consulta N+1.
  3. **Throttling activo**: se agregaron `AnonRateThrottle` y `UserRateThrottle` en `REST_FRAMEWORK` para salvaguardar la API de saturación y ataques de fuerza bruta.

---

### Caso 4: Integración Externa Resiliente con la API de Proveedores (DummyJSON)

* **Prompt suministrado a la IA:**
  > *"Escribe una función en Python para consultar el catálogo de productos mayoristas desde la API de DummyJSON para abastecimiento de bodega y benchmarking de precios en dólares."*

* **Sugerencia inicial de la IA (con riesgos detectados):**
  ```python
  # Sugerencia IA sin timeout ni manejo de errores
  def consultar_proveedor():
      res = urllib.request.urlopen("https://dummyjson.com/products")
      return json.loads(res.read())  # <-- RIESGO: Si el servicio cae, bloquea el servidor
  ```

* **Auditoría y corrección humana aplicada (`inventario/servicios_api.py`):**
  1. Se implementó un tiempo de espera estricto `timeout=3` segundos para evitar hilos zombis o bloqueos del servidor web.
  2. Se añadieron cabeceras de identificación `User-Agent`.
  3. Se encapsuló la llamada dentro de un bloque `try/except Exception` que retorna una estructura predecible con `'disponible': False` y el mensaje de error capturado.
  4. En la interfaz web (`catalogo_api.html`), se programó un aviso visual amarillo de degradación suave (Graceful Degradation): si el proveedor externo no responde, la bodega local continúa operando sin caídas.
