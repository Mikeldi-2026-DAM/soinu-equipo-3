# Muro de mensajes

Semana 1 de Python (2.º DAM). **Plantilla del bloque 4: ya tiene hecha la API (bloques 1 a 3); empieza en la portada con Jinja2.** Una web con FastAPI y Jinja2 donde se escribe un nombre y un mensaje y todos los mensajes
salen en la portada.

> Rellena este README a lo largo de la semana: qué hace el muro, cómo se arranca, qué has ampliado y quién puede borrar.

## Cómo se arranca

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Abre <http://127.0.0.1:8000/> y, para probar la API, <http://127.0.0.1:8000/docs>.

## Qué he ampliado

(Bloque 5.)
