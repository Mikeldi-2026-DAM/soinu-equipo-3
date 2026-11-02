# SOINU · Web de venta de entradas

Proyecto semanal de 2.º DAM. Parte del muro de clase (FastAPI + Jinja2, bloque 4) y lo convierte en la web donde se compran las entradas del festival SOINU. Los datos están en memoria, así que se pierden al reiniciar el servidor.

## Cómo se arranca

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

- Web: <http://127.0.0.1:8000/>
- API (probar en Swagger): <http://127.0.0.1:8000/docs>

## Entradas

### Tipos de entrada

| id | Nombre | Precio | Plazas | Máx. por compra | Qué incluye |
|----|--------|-------:|-------:|----------------:|-------------|
| 1 | General · 1 día | 35 € | 200 | 6 | Acceso al recinto un día (sábado o domingo). |
| 2 | Abono 2 días | 60 € | 100 | 4 | Los dos días con una sola pulsera. Más barato que dos generales. |
| 3 | Adaptada | 35 € | 20 | 2 | Plataforma accesible y acompañante gratis. Pocas plazas porque la plataforma tiene aforo limitado. |
| 4 | VIP | 120 € | 5 | 2 | Los dos días, zona VIP, entrada rápida y aparcamiento. Muy pocas plazas. |

### Datos de cada tipo

- `id`: número que identifica el tipo.
- `nombre`: se muestra en la tarjeta.
- `descripcion`: frase corta para la portada.
- `detalle`: descripción completa para la página del tipo.
- `precio`: en euros, por entrada.
- `plazas_totales`: aforo de ese tipo.
- `plazas_libres`: las que quedan. Baja con cada compra y sube si se anula.
- `max_por_compra`: limita a quien intente acaparar entradas. Cada tipo tiene el suyo porque no es lo mismo una general que una VIP.

### Datos de cada compra

- `id`: número de compra, que se usa en la URL `/compra/{id}`.
- `codigo`: código único (por ejemplo `SOINU-3F9A2C`) que se enseña en la puerta.
- `entrada_id` y `entrada_nombre`: tipo comprado. El nombre se guarda para que la compra se lea sola.
- `cantidad`, `precio_unidad` y `total`.
- `fecha`: fecha y hora de la compra.
- `nombre` y `correo` del comprador. **No se pide DNI**: para entrar basta con el código y el correo sirve para enviar la entrada, así que el DNI no hace falta y no se pide.
- `anulada`: `true` si se ha anulado.

### Reglas

1. **Cantidad**: mínimo 1 y máximo el `max_por_compra` de ese tipo (y nunca más de 10). Tiene que ser un número entero.
2. **Sin plazas**: si la cantidad es mayor que las plazas libres, la compra se rechaza (409 en la API y aviso en la página). Si quedan 0, el tipo sale como **«Agotada»** y no se puede comprar.
3. **Nombre**: entre 2 y 60 caracteres.
4. **Correo**: debe tener forma `algo@dominio.ext`, sin espacios y con 100 caracteres como máximo. Se guarda en minúsculas.
5. **El total lo calcula el servidor** (`precio × cantidad`) con el precio guardado. El formulario no envía ningún precio.
6. **Anular** una compra devuelve sus plazas. Una compra anulada no se puede volver a anular.

## API (JSON)

| Ruta | Qué hace | Códigos |
|------|----------|---------|
| `GET /api/entradas` | Lista los tipos con sus plazas libres | 200 |
| `GET /api/entradas/{id}` | Un tipo | 200 · 404 |
| `POST /api/compras` | Crea una compra y descuenta las plazas | 201 · 404 tipo no existe · 422 datos mal · 409 sin plazas |
| `GET /api/compras` | Todas las compras | 200 |
| `GET /api/compras/{id}` | Una compra | 200 · 404 |
| `POST /api/compras/{id}/anular` | Anula y devuelve plazas | 200 · 404 |

Ejemplo de cuerpo para `POST /api/compras`:

```json
{"entrada_id": 1, "cantidad": 2, "nombre": "Ane Etxeberria", "correo": "ane@example.com"}
```

## Páginas

- `/`: portada con una tarjeta por tipo (nombre, precio y plazas libres, o «Agotada»).
- `/entradas/{id}`: descripción completa y formulario de compra. Si el id no existe, sale una página de error.
- `POST /entradas/{id}/comprar`: si todo va bien, redirige con **303** a `/compra/{id}` (POST-redirect-GET). Si algo falla, vuelve a pintar el formulario con el error (**400**) sin borrar lo escrito.
- `/compra/{id}`: confirmación con el resumen, el total y el código. Recargarla no repite la compra.
- `/compras`: listado para el organizador, con buscador por correo y total recaudado.

## Qué he ampliado (si sobra tiempo)

- [x] Página con todas las compras y buscador por correo (`/compras`).
- [x] Anular una compra devolviendo las plazas.
- [x] Código único por compra que se ve en la confirmación.
- [x] Aspecto propio: cabecera de SOINU, colores en variables CSS y tarjetas.

## Equipo 3

### Deiner
- Se me da bien: programar.
- Me da respeto de este curso: aprender a usar Git.

### Adan
- Se me da bien: trabajar en equipo.
- Me da respeto: GitHub.

### Javier
- Se me da bien: tener pacienza y minimizar los problemas
- Me da respeto: las consecuencias 

### Luis
- Se me da bien: trabajo en equipo, adaptación a nuevas herrramientas, resolución de problemas.
- Me da respeto: el poco tiempo que tenemos.
