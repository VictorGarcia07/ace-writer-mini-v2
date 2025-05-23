
import streamlit as st
import pandas as pd
from docx import Document
import openai
import time

st.set_page_config(page_title="ACE Writer GPT", layout="wide")
st.title("ACE Writer GPT – Redacción automática")

# Inicialización de estado
if "mostrar_redaccion" not in st.session_state:
    st.session_state["mostrar_redaccion"] = False
if "referencias_finales" not in st.session_state:
    st.session_state["referencias_finales"] = []
if "subtitulo" not in st.session_state:
    st.session_state["subtitulo"] = ""
if "contenido_redactado" not in st.session_state:
    st.session_state["contenido_redactado"] = ""
if "redaccion_iniciada" not in st.session_state:
    st.session_state["redaccion_iniciada"] = False

st.subheader("Paso 0 – Ingresá tu clave de OpenAI")
api_key = st.text_input("API Key (formato sk-...):", type="password")

def generar_redaccion(subtitulo, referencias, api_key):
    openai.api_key = api_key
    ref_texto = "\n".join([
        f"{i+1}. {r['Autores']} ({r['Año']}). {r['Título del artículo']}. {r['Journal']}."
        for i, (_, r) in enumerate(referencias)
    ])
    prompt = f"""
Actuás como redactor científico del eBook ACE. Vas a redactar un subtema técnico en ciencias del ejercicio para entrenadores profesionales.

Subtema: {subtitulo}

Instrucciones:
- Mínimo 1500 palabras.
- Redactá en tono técnico-claro, dirigido a un coach.
- Usá ejemplos aplicados, analogías, storytelling breve.
- Cada 500 palabras, sugerí una imagen educativa útil (ej: 'Sugerir imagen: curva fuerza-velocidad').
- Utilizá estas referencias como base:

{ref_texto}

Finalizá con una sección de referencias en formato APA 7.
"""

    respuesta = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Sos redactor científico experto en ciencias del ejercicio."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=3000
    )
    return respuesta["choices"][0]["message"]["content"]

# Paso 1 – Subir plantilla
plantilla_file = st.file_uploader("Subí tu plantilla Word (.dotx)", type=["dotx"])

# Paso 2 – Subir referencias
referencias_file = st.file_uploader("Subí tu tabla de referencias (.csv)", type=["csv"])

if plantilla_file and referencias_file:
    df_refs = pd.read_csv(referencias_file)
    referencias_validas = []
    for i, row in df_refs.iterrows():
        if all(pd.notna(row[col]) and str(row[col]).strip() != "" for col in ["Autores", "Año", "Título del artículo", "Journal", "DOI/URL"]):
            referencias_validas.append((i + 1, row))

    st.session_state["referencias_finales"] = referencias_validas

    st.session_state["subtitulo"] = st.text_input("Ingresá el subtítulo del capítulo:", value=st.session_state["subtitulo"])

    if st.button("Iniciar redacción automática con GPT") and api_key:
        with st.spinner("Generando redacción..."):
            resultado = generar_redaccion(st.session_state["subtitulo"], st.session_state["referencias_finales"], api_key)
            st.session_state["contenido_redactado"] = resultado
            st.session_state["redaccion_iniciada"] = True

if st.session_state["redaccion_iniciada"]:
    st.subheader("Redacción generada")
    st.text_area("Contenido:", value=st.session_state["contenido_redactado"], height=500)

    if st.button("Exportar a Word"):
        doc = Document()
        doc.add_heading(st.session_state["subtitulo"], level=1)
        doc.add_paragraph(st.session_state["contenido_redactado"])
        file_path = "/mnt/data/redaccion_acewriter_gpt.docx"
        doc.save(file_path)
        with open(file_path, "rb") as f:
            st.download_button("Descargar Word", data=f, file_name="Redaccion_ACEWriter.docx")
