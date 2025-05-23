
import streamlit as st
import pandas as pd
import openai
from docx import Document
import tempfile
import os

st.set_page_config(page_title="ACE Writer Mini V37", layout="wide")
st.title("✍️ ACE Writer Mini – V37 Estable (Con correcciones de redundancia y exportación)")

# ─────────────────────────────────────────────────────────────
# INICIALIZACIÓN DE VARIABLES
# ─────────────────────────────────────────────────────────────
for key in ["clave_ok", "redaccion", "citadas", "subtema", "referencias_completas", "referencias_incompletas"]:
    if key not in st.session_state:
        st.session_state[key] = "" if key == "subtema" else []

# ─────────────────────────────────────────────────────────────
# PASO 0 – API KEY
# ─────────────────────────────────────────────────────────────
api_key = st.text_input("🔐 Clave OpenAI", type="password")
if api_key.startswith("sk-"):
    st.session_state["clave_ok"] = True
    st.success("✅ Clave válida")
else:
    st.warning("🔑 Ingresá una clave válida para continuar")

# ─────────────────────────────────────────────────────────────
# PASO 1 – PLANTILLA WORD
# ─────────────────────────────────────────────────────────────
st.subheader("Paso 1 – Cargar plantilla Word (.dotx)")
plantilla = st.file_uploader("📂 Plantilla Word", type=["dotx"])
if plantilla:
    doc = Document(plantilla)
    requeridos = ["Heading 1", "Heading 2", "Normal", "Reference"]
    encontrados = [s.name for s in doc.styles]
    resumen = [{"Estilo": s, "Presente": "✅" if s in encontrados else "❌"} for s in requeridos]
    st.dataframe(pd.DataFrame(resumen))

# ─────────────────────────────────────────────────────────────
# PASO 2 – REFERENCIAS CSV
# ─────────────────────────────────────────────────────────────
st.subheader("Paso 2 – Cargar referencias (.csv)")
archivo_csv = st.file_uploader("📄 Archivo .csv", type=["csv"])
selected_refs = []
if archivo_csv:
    df = pd.read_csv(archivo_csv)
    columnas = ["Autores", "Año", "Título del artículo", "Journal"]
    if not all(col in df.columns for col in columnas):
        st.error("❌ El CSV debe incluir columnas: Autores, Año, Título del artículo, Journal")
    else:
        completas, incompletas = [], []
        for _, row in df.iterrows():
            try:
                if any(pd.isna(row.get(c)) or str(row.get(c)).strip() == "" for c in columnas):
                    continue
                ref = f"{row['Autores']} ({row['Año']}). {row['Título del artículo']}. {row['Journal']}."
                if "DOI" in row and pd.notna(row["DOI"]):
                    ref += f" https://doi.org/{row['DOI']}"
                completas.append(ref)
            except:
                continue
        st.success(f"✅ {len(completas)} referencias completas cargadas")
        selected_refs.extend(completas)

# ─────────────────────────────────────────────────────────────
# PASO 3 – SUBTEMA Y BOTÓN
# ─────────────────────────────────────────────────────────────
st.subheader("Paso 3 – Ingresá el subtítulo del subtema")
st.session_state["subtema"] = st.text_input("✏️ Subtema", value=st.session_state["subtema"])

# ─────────────────────────────────────────────────────────────
# GPT GENERACIÓN Y FILTROS
# ─────────────────────────────────────────────────────────────
def redactar_con_gpt(subtema, capitulo, referencias, api_key):
    prompt = f"""Actuás como redactor científico del Proyecto eBooks ACE.
Tu tarea es redactar el subtema titulado **{subtema}**, que forma parte del capítulo **{capitulo}** del eBook ACE.

📌 Condiciones obligatorias:
– El texto debe tener mínimo **1500 palabras reales**
– Incluir al menos **1 recurso visual sugerido cada 500 palabras**
– Utilizar **solo** las referencias incluidas a continuación
– Cerrar con una sección de referencias en formato **APA 7**, solo con las fuentes citadas realmente en el cuerpo

📚 Lista de referencias válidas:
{chr(10).join(referencias)}

Redactá el texto directamente a continuación, en tono técnico claro, orientado a entrenadores profesionales, con ejemplos prácticos y subtítulos.
"""
    try:
        client = openai.OpenAI(api_key=api_key)
        with st.spinner("✍️ Redactando contenido inicial..."):
            r1 = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=3500
            )
        base = r1.choices[0].message.content
        if len(base.split()) >= 1500:
            return base

        # Ampliación automática
        extend = f"Ampliá este texto sin repetir ideas hasta alcanzar 1500 palabras:\n\n{base}"
        with st.spinner("🔁 Solicitando ampliación..."):
            r2 = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": extend}],
                temperature=0.7,
                max_tokens=3000
            )
        extra = r2.choices[0].message.content

        # Eliminar redundancia
        if base in extra:
            extra = extra.replace(base, "")
        return base + "\n\n" + extra
    except Exception as e:
        st.error("❌ Error al generar redacción: " + str(e))
        return ""

if st.button("🚀 Generar redacción"):
    if st.session_state["clave_ok"] and st.session_state["subtema"] and selected_refs:
        capitulo = "Capítulo generado automáticamente"
        texto = redactar_con_gpt(st.session_state["subtema"], capitulo, selected_refs, api_key)
        st.session_state["redaccion"] = texto
        citas = []
        for ref in selected_refs:
            apellido = ref.split(",")[0]
            if apellido.lower() in texto.lower():
                citas.append(ref)
        st.session_state["citadas"] = list(set(citas))

# ─────────────────────────────────────────────────────────────
# MOSTRAR RESULTADOS Y EXPORTAR
# ─────────────────────────────────────────────────────────────
if st.session_state.get("redaccion"):
    st.subheader("🧾 Redacción generada")
    st.text_area("Texto", value=st.session_state["redaccion"], height=500)
    st.markdown(f"📊 Palabras: **{len(st.session_state['redaccion'].split())}**")
    st.markdown(f"📚 Citas detectadas: **{len(st.session_state['citadas'])}**")

    if st.button("💾 Exportar a Word"):
        doc = Document(plantilla) if plantilla else Document()
        doc.add_heading(st.session_state["subtema"], level=1)
        doc.add_paragraph(st.session_state["redaccion"])
        doc.add_page_break()
        doc.add_heading("Referencias citadas", level=2)
        for ref in st.session_state["citadas"]:
            doc.add_paragraph(ref)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        doc.save(temp_file.name)
        with open(temp_file.name, "rb") as f:
            st.download_button("📥 Descargar Word", data=f, file_name="ACEWriter_v37.docx")
        os.unlink(temp_file.name)
