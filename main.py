from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Muro")

# ---------- DATOS (en memoria: se pierden al reiniciar el servidor) ----------
MENSAJES = [
    {"id": 1, "autor": "Ane", "texto": "Bienvenidos al muro de 2.º DAM"},
    {"id": 2, "autor": "Iker", "texto": "¿Alguien ha conseguido arrancar uvicorn?"},
]


def siguiente_id():
    return max((m["id"] for m in MENSAJES), default=0) + 1


class MensajeNuevo(BaseModel):
    autor: str = Field(min_length=1, max_length=30)
    texto: str = Field(min_length=1, max_length=280)


@app.get("/salud")
def salud():
    return {"ok": True, "app": "Muro"}


@app.get("/hola/{nombre}")
def hola(nombre: str):
    return {"saludo": f"Hola, {nombre}"}


# ---------- API (JSON) ----------
@app.get("/api/mensajes")
def listar_mensajes():
    return MENSAJES


@app.get("/api/mensajes/{mensaje_id}")
def ver_mensaje(mensaje_id: int):
    for m in MENSAJES:
        if m["id"] == mensaje_id:
            return m
    raise HTTPException(status_code=404, detail="No existe ese mensaje")


@app.post("/api/mensajes", status_code=201)
def crear_mensaje(nuevo: MensajeNuevo):
    mensaje = {"id": siguiente_id(), **nuevo.model_dump()}
    MENSAJES.append(mensaje)
    return mensaje
