<<<<<<< HEAD
import re
import secrets
from datetime import datetime

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

app = FastAPI(title="SOINU · Venta de entradas")
templates = Jinja2Templates(directory="templates")

# ---------- DATOS (en memoria: se pierden al reiniciar el servidor) ----------
ENTRADAS = [
    {
        "id": 1,
        "nombre": "General · 1 día",
        "descripcion": "Acceso al recinto un día a elegir.",
        "detalle": "Acceso a todos los escenarios durante un día (sábado o domingo), "
        "de 17:00 al cierre. Se puede salir y volver a entrar con la pulsera.",
        "precio": 35.0,
        "plazas_totales": 200,
        "plazas_libres": 200,
        "max_por_compra": 6,
    },
    {
        "id": 2,
        "nombre": "Abono 2 días",
        "descripcion": "Sábado y domingo con una sola pulsera.",
        "detalle": "Acceso a todos los escenarios los dos días del festival. "
        "Sale más barato que comprar dos entradas generales.",
        "precio": 60.0,
        "plazas_totales": 100,
        "plazas_libres": 100,
        "max_por_compra": 4,
    },
    {
        "id": 3,
        "nombre": "Adaptada",
        "descripcion": "Plataforma accesible y acompañante gratis.",
        "detalle": "Para personas con movilidad reducida o discapacidad. Incluye sitio en la "
        "plataforma accesible frente al escenario principal y entrada gratuita para "
        "un acompañante (no hace falta comprarla).",
        "precio": 35.0,
        "plazas_totales": 20,
        "plazas_libres": 20,
        "max_por_compra": 2,
    },
    {
        "id": 4,
        "nombre": "VIP",
        "descripcion": "Zona VIP, barra propia y aparcamiento.",
        "detalle": "Los dos días, con acceso a la zona VIP (barra y baños propios), "
        "entrada rápida y plaza de aparcamiento. Plazas muy limitadas.",
        "precio": 120.0,
        "plazas_totales": 5,
        "plazas_libres": 5,
        "max_por_compra": 2,
    },
]

COMPRAS = []

CANTIDAD_MINIMA = 1
CORREO_VALIDO = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def siguiente_id(lista):
    return max((x["id"] for x in lista), default=0) + 1


def buscar_entrada(entrada_id):
    for e in ENTRADAS:
        if e["id"] == entrada_id:
            return e
    return None


def buscar_compra(compra_id):
    for c in COMPRAS:
        if c["id"] == compra_id:
            return c
    return None


def calcular_total(entrada, cantidad):
    # El total SIEMPRE lo calcula el servidor con el precio guardado.
    return round(entrada["precio"] * cantidad, 2)


def nuevo_codigo():
    # Código único por compra, por ejemplo SOINU-3F9A2C
    while True:
        codigo = "SOINU-" + secrets.token_hex(3).upper()
        if all(c["codigo"] != codigo for c in COMPRAS):
            return codigo


class CompraNueva(BaseModel):
    entrada_id: int = Field(ge=1)
    cantidad: int = Field(ge=CANTIDAD_MINIMA, le=10)
    nombre: str = Field(min_length=2, max_length=60)
    correo: str = Field(max_length=100, pattern=CORREO_VALIDO)


class ErrorCompra(Exception):
    def __init__(self, mensaje, codigo_http):
        self.mensaje = mensaje
        self.codigo_http = codigo_http


def realizar_compra(datos: CompraNueva):
    """Comprueba las reglas, descuenta plazas y guarda la compra.
    La usan tanto la API como el formulario, así las reglas están en un solo sitio."""
    entrada = buscar_entrada(datos.entrada_id)
    if entrada is None:
        raise ErrorCompra("No existe ese tipo de entrada.", 404)
    if datos.cantidad > entrada["max_por_compra"]:
        raise ErrorCompra(
            f"Como máximo se pueden comprar {entrada['max_por_compra']} entradas de este tipo.", 422
        )
    if entrada["plazas_libres"] == 0:
        raise ErrorCompra("Esta entrada está agotada.", 409)
    if datos.cantidad > entrada["plazas_libres"]:
        raise ErrorCompra(f"Solo quedan {entrada['plazas_libres']} plazas.", 409)

    entrada["plazas_libres"] -= datos.cantidad
    compra = {
        "id": siguiente_id(COMPRAS),
        "codigo": nuevo_codigo(),
        "entrada_id": entrada["id"],
        "entrada_nombre": entrada["nombre"],
        "cantidad": datos.cantidad,
        "precio_unidad": entrada["precio"],
        "total": calcular_total(entrada, datos.cantidad),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nombre": datos.nombre.strip(),
        "correo": datos.correo.strip().lower(),
        "anulada": False,
    }
    COMPRAS.append(compra)
    return compra


def anular_compra(compra):
    if not compra["anulada"]:
        compra["anulada"] = True
        entrada = buscar_entrada(compra["entrada_id"])
        if entrada is not None:
            entrada["plazas_libres"] += compra["cantidad"]


@app.get("/salud")
def salud():
    return {"ok": True, "app": "SOINU"}


# ---------- API (JSON) ----------
@app.get("/api/entradas")
def api_listar_entradas():
    return ENTRADAS


@app.get("/api/entradas/{entrada_id}")
def api_ver_entrada(entrada_id: int):
    entrada = buscar_entrada(entrada_id)
    if entrada is None:
        raise HTTPException(status_code=404, detail="No existe ese tipo de entrada")
    return entrada


@app.post("/api/compras", status_code=201)
def api_crear_compra(nueva: CompraNueva):
    try:
        return realizar_compra(nueva)
    except ErrorCompra as e:
        raise HTTPException(status_code=e.codigo_http, detail=e.mensaje)


@app.get("/api/compras")
def api_listar_compras():
    return COMPRAS


@app.get("/api/compras/{compra_id}")
def api_ver_compra(compra_id: int):
    compra = buscar_compra(compra_id)
    if compra is None:
        raise HTTPException(status_code=404, detail="No existe esa compra")
    return compra


@app.post("/api/compras/{compra_id}/anular")
def api_anular_compra(compra_id: int):
    compra = buscar_compra(compra_id)
    if compra is None:
        raise HTTPException(status_code=404, detail="No existe esa compra")
    anular_compra(compra)
    return compra


# ---------- PÁGINAS (HTML con Jinja2) ----------
def pagina_error(request, titulo, mensaje, status_code=404):
    return templates.TemplateResponse(
        request, "error.html", {"titulo": titulo, "mensaje": mensaje}, status_code=status_code
    )


@app.get("/", response_class=HTMLResponse)
def portada(request: Request):
    return templates.TemplateResponse(request, "index.html", {"entradas": ENTRADAS})


@app.get("/entradas/{entrada_id}", response_class=HTMLResponse)
def pagina_entrada(request: Request, entrada_id: int):
    entrada = buscar_entrada(entrada_id)
    if entrada is None:
        return pagina_error(request, "Entrada no encontrada", "Ese tipo de entrada no existe.")
    return templates.TemplateResponse(
        request, "entrada.html", {"entrada": entrada, "error": None, "valores": {}}
    )


@app.post("/entradas/{entrada_id}/comprar", response_class=HTMLResponse)
def comprar(
    request: Request,
    entrada_id: int,
    cantidad: str = Form(""),
    nombre: str = Form(""),
    correo: str = Form(""),
):
    entrada = buscar_entrada(entrada_id)
    if entrada is None:
        return pagina_error(request, "Entrada no encontrada", "Ese tipo de entrada no existe.")

    valores = {"cantidad": cantidad, "nombre": nombre, "correo": correo}
    nombre = nombre.strip()
    correo = correo.strip()

    # Validación del formulario con mensajes en castellano
    error = None
    if not cantidad.strip().isdigit():
        error = "La cantidad tiene que ser un número entero."
    elif int(cantidad) < CANTIDAD_MINIMA:
        error = f"Tienes que comprar al menos {CANTIDAD_MINIMA} entrada."
    elif len(nombre) < 2 or len(nombre) > 60:
        error = "El nombre tiene que tener entre 2 y 60 caracteres."
    elif len(correo) > 100 or not re.match(CORREO_VALIDO, correo):
        error = "El correo no es válido (ejemplo: nombre@dominio.com)."

    if error is None:
        try:
            datos = CompraNueva(
                entrada_id=entrada_id, cantidad=int(cantidad), nombre=nombre, correo=correo
            )
            compra = realizar_compra(datos)
            # POST-redirect-GET: recargar la confirmación no repite la compra
            return RedirectResponse(url=f"/compra/{compra['id']}", status_code=303)
        except ErrorCompra as e:
            error = e.mensaje
        except ValueError:
            error = f"Como máximo se pueden comprar {entrada['max_por_compra']} entradas de este tipo."

    return templates.TemplateResponse(
        request,
        "entrada.html",
        {"entrada": entrada, "error": error, "valores": valores},
        status_code=400,
    )


@app.get("/compra/{compra_id}", response_class=HTMLResponse)
def confirmacion(request: Request, compra_id: int):
    compra = buscar_compra(compra_id)
    if compra is None:
        return pagina_error(request, "Compra no encontrada", "No existe ninguna compra con ese número.")
    return templates.TemplateResponse(request, "compra.html", {"compra": compra})


@app.post("/compra/{compra_id}/anular")
def anular(request: Request, compra_id: int):
    compra = buscar_compra(compra_id)
    if compra is None:
        return pagina_error(request, "Compra no encontrada", "No existe ninguna compra con ese número.")
    anular_compra(compra)
    return RedirectResponse(url=f"/compra/{compra_id}", status_code=303)


@app.get("/compras", response_class=HTMLResponse)
def lista_compras(request: Request, correo: str = ""):
    buscado = correo.strip().lower()
    compras = [c for c in COMPRAS if buscado in c["correo"]] if buscado else COMPRAS
    recaudado = sum(c["total"] for c in COMPRAS if not c["anulada"])
    return templates.TemplateResponse(
        request,
        "compras.html",
        {"compras": compras, "correo": correo, "recaudado": recaudado, "total_compras": len(COMPRAS)},
    )
=======
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

app = FastAPI(title="Muro")
templates = Jinja2Templates(directory="templates")
# ---------- DATOS (en memoria: se pierden al reiniciar el servidor) ----------

class MensajeNuevo(BaseModel):
    autor: str = Field(min_length=1, max_length=30)
    texto: str = Field(min_length=1, max_length=280)

MENSAJES = [
    {"id": 1, "autor": "Ane", "texto": "Bienvenidos al muro de 2.º DAM"},
    {"id": 2, "autor": "Iker", "texto": "¿Alguien ha conseguido arrancar uvicorn?"},
]

def siguiente_id():
    return max((m["id"] for m in MENSAJES), default=0) + 1

# 1. GET /salud → {"ok": True, "app": "Muro"}


# ---------- PRUEBA (en el Aula; en tu ordenador: python main.py) ----------
if __name__ == "__main__":
    from aula import Cliente
    c = Cliente(app)
    print(c.get("/salud").json())


@app.get("/api/mensajes")
def obtener_mensajes():
    return MENSAJES

@app.get("/api/mensajes/{id}")
def obtener_mensaje(id: int):
    mensaje = next((m for m in MENSAJES if m["id"] == id), None)
    if not mensaje:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    return mensaje

@app.post("/api/mensajes", status_code=201)
def crear_mensaje(nuevo: MensajeNuevo):
    mensaje = {"id": siguiente_id(), **nuevo.model_dump()}
    MENSAJES.append(mensaje)
    return mensaje

@app.get("/salud")
def salud():
    return {"ok": True, "app": "Muro de Javier Ortega"}

@app.get("/hola/{nombre}")
def hola(nombre: str):
    return {"saludo": f"Hola, {nombre}"}

# ---------- PÁGINAS (HTML) ----------
@app.get("/", response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse(request, "index.html", {"mensajes": MENSAJES})
>>>>>>> 9678cf3c68b2afeb20f36e3fda2484fa94489f88
