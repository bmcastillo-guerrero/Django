# Guía de Defensa — StockFlow según Escala de Apreciación

> Mapeo de los 12 indicadores de la rúbrica con evidencia concreta en el proyecto,
> más el guion para demostrar cada uno en vivo.

## Nivel objetivo: 4 - Destacado

Para alcanzar "Destacado" cada indicador exige **autonomía, justificación y buenas
prácticas**, no solo que funcione. Esta guía señala qué decir y qué mostrar.

---

## Indicadores 1 a 4 — Lenguaje y desarrollo

### Ind. 1 · Variables y operaciones (1.1.1)
**Evidencia:** `inventario/models.py`
- Variables: atributos de clase (`nombre`, `sku`, `precio`, `stock`...).
- Operaciones aritméticas: `valor_inventario` → `self.precio * self.stock`.
- Operaciones de comparación: `necesita_reposicion` → `self.stock <= self.stock_minimo`.
**Demo:** abrir `models.py:60-70` y explicar por qué se usó `DecimalField`
(precisión monetaria) y no `Float`.

### Ind. 2 · Instrucciones, estructuras y operadores (1.1.2)
**Evidencia:** `inventario/views.py` y `inventario/tests.py`
- Condicional doble en `detalle_producto`: `if movimiento.tipo == 'ENTRADA': ... else: ...`
- Estructura de control en `lista_productos`: filtros acumulativos con `Q`.
- Operadores lógicos OR: `Q(nombre__icontains=query) | Q(sku__icontains=query)`.
**Demo:** ejecutar `python manage.py test` → 15 pruebas OK demuestran dominio.

### Ind. 3 · Paquetes externos (1.1.3)
**Evidencia:** `requirements.txt`
| Paquete | Justificación |
|---|---|
| `faker` | Generar datos de prueba realistas sin inventarlos a mano |
| `django-crispy-forms` + `crispy-bootstrap5` | Formularios con estilos Bootstrap sin CSS manual |
**Frase clave:** *"Seleccioné Faker porque permite generar volúmenes de datos
variados y representativos, requisito para probar filtros y alertas."*

### Ind. 4 · Aplicación sencilla en Django + recomendaciones IA (1.1.4)
**Evidencia:** app completa funcional; las recomendaciones de IA aplicadas están
documentadas en README (sección "Uso de IA").

---

## Indicadores 5 a 9 — Arquitectura Django

### Ind. 5 · Modelo MVC (MTV) 
**Evidencia:** separación real en carpetas:
```
Modelo       → inventario/models.py   (datos + reglas de negocio)
Vista        → templates/             (presentación HTML)
Controlador  → inventario/views.py    (recibe petición, orquesta) + urls.py
```
**Demo:** seguir una petición completa: usuario envía movimiento →
`urls.py` enruta a `views.detalle_producto` → valida `MovimientoForm` →
actualiza `Producto.stock` → redirige al template con mensaje.
**Frase clave:** *"Django lo llama MTV pero es MVC: el Template hace de Vista
y la View hace de Controlador."*

### Ind. 6 · Configuración del entorno
**Evidencia:** `venv/`, `settings.py`, `requirements.txt`, pasos en README.
**Puntos a mencionar:**
- Entorno virtual aísla dependencias del sistema.
- `LANGUAGE_CODE = 'es'` y `TIME_ZONE = 'America/Santiago'`.
- `MESSAGE_TAGS` mapea errores de Django a clases Bootstrap.
**Demo:** replicar instalación desde cero con los 6 comandos del README.

### Ind. 7 · Models según requerimientos
**Evidencia:** `inventario/models.py` — 3 modelos relacionados:
- `Categoria 1—N Producto` (ForeignKey PROTECT: impide borrar categoría con productos).
- `Producto 1—N MovimientoStock` (CASCADE: el historial muere con el producto).
- Reglas: `unique=True` en SKU, `MinValueValidator` en precios/cantidades,
  `choices` para unidades y tipo de movimiento.
**Frase clave:** *"PROTECT en categoría es decisión de diseño: nunca debe quedar
un producto huérfano sin categoría."*

### Ind. 8 · Vistas y templates integrados
**Evidencia:** flujo frontend → Django:
1. Se prototipó la UI como HTML estático (`frontend/`).
2. Cada página se convirtió a template Django heredando de `base.html`
   (`{% extends %}` / `{% block %}`).
3. El JS que simulaba datos (`localStorage`) se reemplazó por contexto
   renderizado del servidor (`{{ total_productos }}`, `{% for %}`).
4. Los formularios hacen POST real con `{% csrf_token %}` y validación servidor.
**Demo:** comparar `frontend/index.html` (JS) vs `templates/inventario/dashboard.html` (servidor).

### Ind. 9 · Tecnologías del lado del servidor
**Evidencia:** todo lo que ocurre en Python/Django, no en el navegador:
- Validaciones de negocio (`forms.clean()`: salida nunca deja stock negativo).
- Cálculo de métricas del panel (suma del valor de inventario).
- Búsqueda y filtrado con ORM (SQL generado por Django sobre SQLite).
- Sesiones y CSRF habilitados por middleware.
**Frase clave:** *"Aunque desactiven JavaScript, la app sigue validando todo:
la lógica vive en el servidor."*

---

## Indicadores 10 a 12 — IA y despliegue

### Ind. 10 · IA como apoyo al desarrollo
**Narrativa (3 usos concretos):**
1. **Diseño de interfaz**: Bootstrap 5 elegido con asistencia de IA → UI responsiva.
2. **Arquitectura**: la IA recomendó el patrón prototipo estático → template Django,
   manteniendo un solo diseño (menos retrabajo).
3. **Verificación**: cada sugerencia se probó (`manage.py check`, 15 tests, HTTP 200).
**Punto crítico (nivel Destacado):** *no se copió ciegamente* — se adaptó el
código generado a español, zona horaria chilena y reglas del negocio.

### Ind. 11 · Datos de prueba generados con apoyo de IA
**Evidencia:** `inventario/management/commands/seed_datos.py`
- La IA recomendó Faker y ayudó a diseñar la coherencia del set:
  movimientos proporcionados al stock, SKUs únicos, categorías reales del rubro.
**Demo:** `python manage.py seed_datos --limpiar` → muestra 5 categorías,
20 productos y movimientos; luego verificar las alertas del panel.

### Ind. 12 · Protocolos, hosting y dominios
**Explicación conectada al proyecto (no teórica):**
| Concepto | En StockFlow |
|---|---|
| HTTP/HTTPS | `runserver` habla HTTP; en producción TLS termina en Nginx/proxy |
| WSGI | `stockflow/wsgi.py` es el punto de entrada que Gunicorn ejecuta |
| Hosting | PythonAnywhere/Railway (PaaS) o VPS con Nginx + Gunicorn |
| Dominio | comprar `stockflow.cl` en NIC Chile → DNS A/CNAME → IP del hosting |
| DEBUG=False | obligatorio en producción + ALLOWED_HOSTS con el dominio |
**Frase clave:** *"Al subir a hosting cambio SQLite por PostgreSQL solo tocando
DATABASES en settings.py — eso demuestra que la app es portable."*

---

## Guion de demostración en vivo (8 min)

1. `runserver` → recorrer Panel, Productos, Detalle (2 min)
2. Registrar ENTRADA y una SALIDA mayor al stock → mostrar validación servidor (2 min)
3. Crear producto con SKU duplicado → mostrar error de unicidad (1 min)
4. `manage.py test` → 15 OK (1 min)
5. `seed_datos --limpiar` → repoblar y ver alertas (1 min)
6. Cerrar mostrando README (MVC + despliegue) (1 min)

## Posibles preguntas del evaluador

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué PROTECT y no CASCADE en Categoria? | Evita productos huérfanos; CASCADE solo para historial dependiente |
| ¿Dónde está la V en MVC? | Templates; la View de Django actúa como Controlador |
| ¿Cómo evitas stock negativo? | `MovimientoForm.clean()` rechaza salidas > stock |
| ¿Qué pasa si falla el POST? | La vista re-renderiza con errores; nada se persiste (`form.is_valid()` gate) |
| ¿Cómo escalarías? | API REST (DRF), PostgreSQL, multi-bodega (nueva FK Bodega), caché Redis |
