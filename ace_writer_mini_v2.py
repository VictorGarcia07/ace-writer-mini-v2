
import streamlit as st
import pandas as pd
import openai
from docx import Document
import tempfile
import os
import re

st.set_page_config(page_title="ACE Writer Mini – Versión Final", layout="wide")
st.title("🧠 ACE Writer Mini – Generador de capítulos científicos")

# Inicialización de estado
for key in ["clave_ok", "redaccion", "citadas", "subtema", "referencias_completas", "referencias_incompletas"]:
    if key not in st.session_state:
        st.session_state[key] = [] if "referencias" in key or key == "citadas" else ""

# Paso 0 – API Key
api_key = st.text_input("🔐 Clave OpenAI", type="password")
if api_key.startswith("sk-"):
    st.session_state["clave_ok"] = True
    st.success("✅ Clave válida")

# Paso 1 – Plantilla Word
st.subheader("Paso 1 – Subí tu plantilla Word (.dotx)")
plantilla = st.file_uploader("📂 Plantilla Word", type=["dotx"])
if plantilla:
    doc = Document(plantilla)
    requeridos = ["Heading 1", "Heading 2", "Normal", "Reference"]
    encontrados = [s.name for s in doc.styles]
    validacion = [{"Estilo": s, "Presente": "✅" if s in encontrados else "❌"} for s in requeridos]
    st.dataframe(pd.DataFrame(validacion))

# Paso 2 – Cargar referencias
st.subheader("Paso 2 – Subí tu archivo .csv con referencias")
archivo_csv = st.file_uploader("📄 Archivo .csv", type=["csv"])
referencias_seleccionadas = []

if archivo_csv:
    df = pd.read_csv(archivo_csv)
    columnas = ["Autores", "Año", "Título del artículo", "Journal"]
    completas, incompletas = [], []

    for i, row in df.iterrows():
        if any(pd.isna(row.get(col, "")) or str(row[col]).strip() == "" for col in columnas):
            ref = f"Fila {i+1}: {row.to_dict()}"
            incompletas.append(ref)
            continue
        ref = f"{row['Autores']} ({row['Año']}). {row['Título del artículo']}. {row['Journal']}."
        if "DOI" in row and pd.notna(row["DOI"]):
            ref += f" https://doi.org/{row['DOI']}"
        completas.append(ref)

    referencias_seleccionadas.extend(completas)
    st.success(f"✅ {len(completas)} referencias completas agregadas automáticamente.")
    if incompletas:
        st.warning(f"⚠️ {len(incompletas)} referencias incompletas detectadas.")
        seleccionar_todas = st.checkbox("Seleccionar todas las incompletas")
        for i, ref in enumerate(incompletas):
            if seleccionar_todas or st.checkbox(ref, key=f"incomp_{i}"):
                referencias_seleccionadas.append(ref)

# Paso 3 – Ingreso del subtítulo
st.subheader("Paso 3 – Ingresá el subtítulo del subtema")
st.session_state["subtema"] = st.text_input("✏️ Subtema del capítulo", value=st.session_state["subtema"])

# Paso 4 – Redacción con GPT
def redactar_con_gpt(subtema, capitulo, referencias, api_key):
    prompt = f"""Actuás como redactor científico del Proyecto eBooks ACE.
Tu tarea es redactar el subtema titulado "{subtema}", parte del capítulo "{capitulo}" de un e-book científico.

📌 Requisitos:
– Redactar un texto científicamente sólido y bien estructurado. El mínimo es de 1500 palabras reales, pero si el tema se agota correctamente con menos, se puede entregar así.
– Incluir 1 sugerencia de recurso visual cada 500 palabras
– Usar solo las referencias proporcionadas
– Cerrar con sección de referencias APA 7, solo si fueron citadas

📚 Lista de referencias válidas:
{chr(10).join(referencias)}

Redactá con tono técnico claro, orientado a entrenadores, usando ejemplos prácticos y subtítulos jerárquicos.
"""
    try:
        client = openai.OpenAI(api_key=api_key)
        with st.spinner("Generando texto..."):
            r1 = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4096
            )
        return r1.choices[0].message.content
    except Exception as e:
        st.error("Error al generar redacción: " + str(e))
        return ""

            extra = extra.replace(base, "")
        return base + "\n\n" + extra
    except Exception as e:
        st.error("❌ Error al generar redacción: " + str(e))
        return ""

# Botón para generar redacción
if st.button("🚀 Generar redacción"):
    if st.session_state["clave_ok"] and st.session_state["subtema"] and referencias_seleccionadas:
        texto = redactar_con_gpt(st.session_state["subtema"], "Capítulo auto-generado", referencias_seleccionadas, api_key)
        st.session_state["redaccion"] = texto
        citas = []
    for ref in referencias_seleccionadas:
        apellido = ref.split(',')[0].strip()
    coincidencias = re.findall(rf"\({apellido}, \d{{4}}\)", texto)
        if coincidencias:
        citas.append(ref)
    st.session_state["citadas"] = list(set(citas))

# Paso 5 – Mostrar texto
if st.session_state.get("redaccion"):
    st.subheader("🧾 Redacción generada")
    st.text_area("Texto", value=st.session_state["redaccion"], height=500)
    st.markdown(f"📊 Palabras: **{len(st.session_state['redaccion'].split())}**")
    st.markdown(f"📚 Citas detectadas: **{len(st.session_state['citadas'])}**")


# Paso 5.1 – Botón para preguntar por qué se truncó
if st.session_state.get("redaccion") and st.button("🤔 ¿Por qué se truncó este texto?"):
    try:
        analisis_prompt = f"""Actuás como un crítico técnico del equipo editorial de un eBook científico.
Se te dio este texto generado por una IA con el objetivo de desarrollar un subtema de un capítulo, siguiendo normas académicas.

Tu tarea es explicar por qué este texto se truncó con {len(st.session_state['redaccion'].split())} palabras.
Explicá si fue por agotamiento de fuentes, por corte técnico, o por otra razón.
Texto a analizar:
""" + st.session_state["redaccion"]

        r = openai.OpenAI(api_key=api_key).chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": analisis_prompt}],
            temperature=0,
            max_tokens=800
        )
        st.info(r.choices[0].message.content)
    except Exception as e:
        st.error("Error al analizar: " + str(e))

# Paso 5.2 – Regenerar texto
if st.session_state.get("redaccion") and st.button("🔁 Regenerar este subtema"):
    texto = redactar_con_gpt(st.session_state["subtema"], "Capítulo auto-generado", referencias_seleccionadas, api_key)
    st.session_state["redaccion"] = texto
    citas = []
    for ref in referencias_seleccionadas:
        apellido = ref.split(',')[0].strip()
    coincidencias = re.findall(rf"\({apellido}, \d{{4}}\)", texto)
        if coincidencias:
        citas.append(ref)
    st.session_state["citadas"] = list(set(citas))

# Paso 5.3 – Cargar nuevo subtítulo
if st.session_state.get("redaccion") and st.button("➕ Generar nuevo subtema"):
    st.session_state["redaccion"] = ""
    st.session_state["citadas"] = []
    st.session_state["subtema"] = ""
    st.rerun()


# Paso 6 – Exportar a Word
if st.session_state.get("redaccion"):
    if st.button("💾 Exportar a Word"):
        doc = Document(plantilla) if plantilla else Document()
        doc.add_heading(st.session_state["subtema"], level=1)
        doc.add_paragraph(st.session_state["redaccion"])
        doc.add_page_break()
        doc.add_heading("Referencias citadas", level=2)
        for ref in st.session_state["citadas"]:
            doc.add_paragraph(ref)

        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', st.session_state["subtema"].strip()) or "ACEWriter"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        doc.save(temp_file.name)
        with open(temp_file.name, "rb") as f:
            st.download_button("📥 Descargar Word", data=f, file_name=f"{safe_name}.docx")
        os.unlink(temp_file.name)
