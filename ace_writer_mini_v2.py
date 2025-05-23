
import streamlit as st
import pandas as pd
from docx import Document
import openai
import time

st.set_page_config(page_title="ACE Writer Mini v14", layout="wide")
st.title("ACE Writer – Redacción GPT con validaciones completas")

# Estado
if "clave_ok" not in st.session_state:
    st.session_state["clave_ok"] = False
if "referencias" not in st.session_state:
    st.session_state["referencias"] = []
if "redaccion" not in st.session_state:
    st.session_state["redaccion"] = ""
if "ampliacion" not in st.session_state:
    st.session_state["ampliacion"] = ""
if "subtitulo" not in st.session_state:
    st.session_state["subtitulo"] = ""

# Paso 0 – API Key
st.subheader("Paso 0 – API Key OpenAI")
api_key = st.text_input("Ingresá tu clave OpenAI (formato sk-...)", type="password")
if api_key.startswith("sk-"):
    st.success("✅ Clave válida")
    st.session_state["clave_ok"] = True
else:
    st.info("Esperando clave válida...")

# Paso 1 – Plantilla
st.subheader("Paso 1 – Subí tu plantilla Word")
plantilla_file = st.file_uploader("Plantilla .dotx", type=["dotx"])
if plantilla_file:
    from docx import Document
    doc = Document(plantilla_file)
    estilos_requeridos = ['Heading 1', 'Heading 2', 'Normal', 'Reference']
    presentes = [est.name for est in doc.styles]
    validacion = [{"Estilo": est, "Presente": "✅" if est in presentes else "❌"} for est in estilos_requeridos]
    st.dataframe(pd.DataFrame(validacion))
    if all(est in presentes for est in estilos_requeridos):
        st.success("✅ Plantilla válida")

# Paso 2 – Referencias
st.subheader("Paso 2 – Subí tu tabla de referencias (.csv)")
archivo_csv = st.file_uploader("Archivo de referencias", type=["csv"])
referencias_validas, referencias_incompletas = [], []

if archivo_csv:
    df = pd.read_csv(archivo_csv)
    for i, row in df.iterrows():
        if all(pd.notna(row[col]) and str(row[col]).strip() != "" for col in ["Autores", "Año", "Título del artículo", "Journal"]):
            referencias_validas.append(row)
        else:
            referencias_incompletas.append(row)

    if referencias_validas:
        st.success(f"✅ {len(referencias_validas)} referencias validadas automáticamente")
    if referencias_incompletas:
        st.warning(f"🛠 {len(referencias_incompletas)} referencias con validación manual")
        usar_incompletas = st.checkbox("¿Incluir todas las referencias manuales?", value=True)
        if usar_incompletas:
            referencias_validas.extend(referencias_incompletas)

    st.session_state["referencias"] = referencias_validas

# Paso 3 – Subtítulo
st.subheader("Paso 3 – Ingresá el subtítulo del capítulo")
st.session_state["subtitulo"] = st.text_input("Subtítulo:", value=st.session_state["subtitulo"])

# Paso 4 – Redacción
def generar_redaccion(parte, api_key, subtitulo, referencias):
    client = openai.OpenAI(api_key=api_key)
    ref_texto = "\n".join([
        f"{r['Autores']} ({r['Año']}). {r['Título del artículo']}. {r['Journal']}."
        for r in referencias
    ])
    prompt = f"""
Actuás como redactor científico para el eBook ACE. Vas a redactar el subtema titulado: {subtitulo}

Instrucciones:
- Redactá con tono técnico-claro, dirigido a entrenadores
- Mínimo 1500 palabras en total. Esta es la parte {parte}.
- Cada 500 palabras sugerí una imagen educativa (ej: 'Sugerir imagen: curva F-v')
- Usá estas referencias como base (no inventes):

{ref_texto}

Terminá con una sección de referencias en formato APA 7.
"""
    if parte == 2:
        prompt = "Continuá la redacción anterior sin repetir contenido. " + prompt

    respuesta = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Sos redactor científico experto en ciencias del ejercicio."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.65,
        max_tokens=5000
    )
    return respuesta.choices[0].message.content

if st.button("🚀 Generar redacción completa"):
    if st.session_state["clave_ok"] and st.session_state["referencias"]:
        with st.spinner("Redactando con GPT..."):
            st.session_state["redaccion"] = generar_redaccion(1, api_key, st.session_state["subtitulo"], st.session_state["referencias"])

if st.session_state["redaccion"]:
    st.subheader("Texto generado")
    st.text_area("Redacción", value=st.session_state["redaccion"], height=400)
    palabras = len(st.session_state["redaccion"].split())
    st.markdown(f"📊 Palabras: {palabras}")
    if palabras < 1500:
        if st.button("➕ Solicitar ampliación"):
            with st.spinner("Solicitando ampliación..."):
                st.session_state["ampliacion"] = generar_redaccion(2, api_key, st.session_state["subtitulo"], st.session_state["referencias"])

if st.session_state["ampliacion"]:
    st.subheader("Ampliación generada")
    st.text_area("Redacción ampliada", value=st.session_state["ampliacion"], height=400)

if st.session_state["redaccion"]:
    if st.button("💾 Exportar todo en Word"):
        doc = Document()
        doc.add_heading(st.session_state["subtitulo"], level=1)
        doc.add_paragraph(st.session_state["redaccion"])
        if st.session_state["ampliacion"]:
            doc.add_paragraph(st.session_state["ampliacion"])
        path = "/mnt/data/redaccion_final_v14.docx"
        doc.save(path)
        with open(path, "rb") as f:
            st.download_button("📥 Descargar Word completo", data=f, file_name="ACEWriter_v14.docx")
