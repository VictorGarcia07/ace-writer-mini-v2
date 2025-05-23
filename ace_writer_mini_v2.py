
import streamlit as st
import pandas as pd
from docx import Document
import openai
import time

# ───────────────────────────────────────────────
# CONFIGURACIÓN INICIAL
# ───────────────────────────────────────────────
st.set_page_config(page_title="ACE Writer Mini V2", layout="wide")
st.title("🧠 ACE Writer Mini V2 – Generación científica automatizada")

# ───────────────────────────────────────────────
# ESTADO INICIAL
# ───────────────────────────────────────────────
for key in ["clave_ok", "referencias_completas", "referencias_incompletas", "subtema", "redaccion", "citadas"]:
    if key not in st.session_state:
        st.session_state[key] = [] if "referencias" in key else ""

# ───────────────────────────────────────────────
# PASO 0 – CLAVE DE OPENAI
# ───────────────────────────────────────────────
api_key = st.text_input("🔐 Clave OpenAI", type="password")
if api_key.startswith("sk-"):
    st.session_state["clave_ok"] = True
    st.success("✅ Clave válida")

# ───────────────────────────────────────────────
# PASO 1 – PLANTILLA WORD
# ───────────────────────────────────────────────
st.subheader("Paso 1 – Cargar plantilla Word (.dotx)")
plantilla = st.file_uploader("📂 Subí tu plantilla Word", type=["dotx"])
if plantilla:
    doc = Document(plantilla)
    requeridos = ["Heading 1", "Heading 2", "Normal", "Reference"]
    encontrados = [s.name for s in doc.styles]
    validacion = [{"Estilo": s, "Presente": "✅" if s in encontrados else "❌"} for s in requeridos]
    st.dataframe(pd.DataFrame(validacion))

# ───────────────────────────────────────────────
# PASO 2 – CARGA DE REFERENCIAS
# ───────────────────────────────────────────────
st.subheader("Paso 2 – Cargar archivo de referencias (.csv)")
archivo_csv = st.file_uploader("📄 Subí tu archivo CSV de referencias", type=["csv"])
selected_refs = []

if archivo_csv:
    df = pd.read_csv(archivo_csv)
    completas, incompletas = [], []
    required = ["Autores", "Año", "Título del artículo", "Journal"]

    for _, row in df.iterrows():
        ref = f"{row['Autores']} ({row['Año']}). {row['Título del artículo']}. {row['Journal']}."
        if "DOI" in df.columns and pd.notna(row["DOI"]):
            ref += f" https://doi.org/{row['DOI']}"
        if all(pd.notna(row.get(col, None)) for col in required):
            completas.append(ref)
        else:
            incompletas.append(ref)

    # Agregar automáticamente las completas
    selected_refs.extend(completas)
    st.success(f"✅ {len(completas)} referencias completas agregadas automáticamente.")
    st.warning(f"⚠️ {len(incompletas)} referencias incompletas encontradas.")

    if incompletas:
        st.markdown("### ✍️ Seleccioná manualmente si querés incluir alguna incompleta")
        select_all = st.checkbox("Seleccionar todas las incompletas")
        for i, ref in enumerate(incompletas):
            if select_all or st.checkbox(ref, key=f"incomp_{i}"):
                selected_refs.append(ref)

# ───────────────────────────────────────────────
# PASO 3 – SUBTÍTULO
# ───────────────────────────────────────────────
st.subheader("Paso 3 – Ingresá el subtítulo del capítulo")
st.session_state["subtema"] = st.text_input("✏️ Subtítulo:", value=st.session_state["subtema"])

# ───────────────────────────────────────────────
# PASO 4 – REDACCIÓN CON GPT
# ───────────────────────────────────────────────
def redactar(subtema, referencias, api_key):
    client = openai.OpenAI(api_key=api_key)
    prompt = f"""Actuás como redactor científico del Proyecto eBooks ACE.
Redactá el subtema titulado "{subtema}" con mínimo 1500 palabras.
Usá estas referencias solamente:
{chr(10).join(referencias)}

Incluí subtítulos, ejemplos prácticos y una sección final con las referencias citadas.
"""
    r1 = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Sos redactor experto en ciencias del ejercicio."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
        max_tokens=5000
    )
    texto = r1.choices[0].message.content
    if len(texto.split()) >= 1500:
        return texto

    ampliacion_prompt = f"Extendé el siguiente texto sin repetirlo, hasta superar 1500 palabras.\n\n{texto}"
    r2 = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Sos redactor experto en ciencias del ejercicio."},
            {"role": "user", "content": ampliacion_prompt}
        ],
        temperature=0.6,
        max_tokens=3000
    )
    return texto + "\n\n" + r2.choices[0].message.content

# ───────────────────────────────────────────────
# PASO 5 – GENERAR REDACCIÓN
# ───────────────────────────────────────────────
if st.button("🚀 Generar redacción"):
    if st.session_state["clave_ok"] and st.session_state["subtema"] and selected_refs:
        texto = redactar(st.session_state["subtema"], selected_refs, api_key)
        st.session_state["redaccion"] = texto
        st.success(f"Redacción generada. Total: {len(texto.split())} palabras.")

        # Detección de citas
        citadas = []
        for ref in selected_refs:
            apellido = ref.split(",")[0]
            if apellido in texto:
                citadas.append(ref)
        st.session_state["citadas"] = citadas

# ───────────────────────────────────────────────
# PASO 6 – MOSTRAR RESULTADO
# ───────────────────────────────────────────────
if st.session_state.get("redaccion"):
    st.subheader("🧾 Resultado")
    st.text_area("Texto generado", value=st.session_state["redaccion"], height=500)
    st.markdown(f"📊 Palabras: **{len(st.session_state['redaccion'].split())}**")
    st.markdown(f"📚 Citas detectadas: **{len(st.session_state['citadas'])}**")

# ───────────────────────────────────────────────
# PASO 7 – EXPORTAR
# ───────────────────────────────────────────────
if st.session_state.get("redaccion"):
    if st.button("💾 Exportar a Word"):
        doc = Document(plantilla) if plantilla else Document()
        doc.add_heading(st.session_state["subtema"], level=1)
        doc.add_paragraph(st.session_state["redaccion"])
        doc.add_page_break()
        doc.add_heading("Referencias citadas", level=2)
        for ref in st.session_state["citadas"]:
            doc.add_paragraph(ref)
        ruta = "/mnt/data/ace_writer_mini_v35.docx"
        doc.save(ruta)
        with open(ruta, "rb") as f:
            st.download_button("📥 Descargar Word", data=f, file_name="ACEWriter_v35.docx")
