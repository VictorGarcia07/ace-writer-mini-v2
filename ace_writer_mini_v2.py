
import streamlit as st
import pandas as pd
from docx import Document
import openai
import time

st.set_page_config(page_title="ACE Writer Mini v15", layout="wide")
st.title("ACE Writer – Redacción GPT con ampliación automática")

# Estado inicial
if "clave_ok" not in st.session_state:
    st.session_state["clave_ok"] = False
if "referencias" not in st.session_state:
    st.session_state["referencias"] = []
if "redaccion" not in st.session_state:
    st.session_state["redaccion"] = ""
if "subtitulo" not in st.session_state:
    st.session_state["subtitulo"] = ""

# Paso 0 – API Key
st.subheader("Paso 0 – API Key OpenAI")
api_key = st.text_input("Clave API (formato sk-...)", type="password")
if api_key.startswith("sk-"):
    st.success("✅ Clave válida")
    st.session_state["clave_ok"] = True
else:
    st.info("Esperando clave válida...")

# Paso 1 – Plantilla
st.subheader("Paso 1 – Validación de plantilla Word (.dotx)")
plantilla = st.file_uploader("Subí tu plantilla Word", type=["dotx"])
if plantilla:
    doc = Document(plantilla)
    required = ['Heading 1', 'Heading 2', 'Normal', 'Reference']
    found = [s.name for s in doc.styles]
    valid = [{"Estilo": s, "Presente": "✅" if s in found else "❌"} for s in required]
    st.dataframe(pd.DataFrame(valid))

# Paso 2 – Referencias
st.subheader("Paso 2 – Cargar y validar referencias")
archivo = st.file_uploader("Subí tu archivo .csv", type=["csv"])
refs_completas, refs_manual = [], []

if archivo:
    df = pd.read_csv(archivo)
    for i, row in df.iterrows():
        if all(pd.notna(row[col]) and str(row[col]).strip() != "" for col in ["Autores", "Año", "Título del artículo", "Journal"]):
            refs_completas.append(row)
        else:
            refs_manual.append(row)

    st.success(f"✅ {len(refs_completas)} referencias validadas automáticamente")
    st.warning(f"🛠 {len(refs_manual)} referencias con validación manual")

    if refs_manual:
        for i, row in enumerate(refs_manual):
            if st.checkbox(f"Incluir: {row['Autores']} ({row['Año']}) - {row['Título del artículo']}", key=f"ref_manual_{i}", value=True):
                refs_completas.append(row)

    st.session_state["referencias"] = refs_completas

# Paso 3 – Subtítulo
st.subheader("Paso 3 – Subtítulo del capítulo")
st.session_state["subtitulo"] = st.text_input("Subtítulo del capítulo", value=st.session_state["subtitulo"])

# Generar redacción
def redactar(subtitulo, refs, api_key, continuar=False):
    client = openai.OpenAI(api_key=api_key)
    ref_texto = "\n".join([
        f"{r['Autores']} ({r['Año']}). {r['Título del artículo']}. {r['Journal']}."
        for r in refs
    ])
    prompt = f"""
Actuás como redactor científico del eBook ACE.

Subtema: {subtitulo}

Instrucciones:
- Mínimo 1500 palabras
- Tono técnico-claro, dirigido a entrenadores
- Cada 500 palabras sugerí una imagen educativa (ej: 'Sugerir imagen: curva fuerza-potencia')
- Citá con formato APA dentro del texto

Referencias base:
{ref_texto}

Finalizá con sección de referencias APA 7.
"""
    if continuar:
        prompt = "Continuá la redacción anterior sin repetir. " + prompt

    respuesta = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Sos redactor científico experto en entrenamiento."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.65,
        max_tokens=5000
    )
    return respuesta.choices[0].message.content

# Paso 4 – Generación automática con ampliación opcional
if st.button("🚀 Generar redacción completa"):
    if st.session_state["clave_ok"] and st.session_state["referencias"]:
        with st.spinner("Redactando con GPT..."):
            parte1 = redactar(st.session_state["subtitulo"], st.session_state["referencias"], api_key)
            palabras1 = len(parte1.split())
            st.session_state["redaccion"] = parte1

            if palabras1 < 1500:
                st.info("Redacción incompleta. Solicitando ampliación automática...")
                parte2 = redactar(st.session_state["subtitulo"], st.session_state["referencias"], api_key, continuar=True)
                st.session_state["redaccion"] += "\n\n" + parte2

# Mostrar resultados
if st.session_state["redaccion"]:
    st.subheader("Texto generado completo")
    st.text_area("Redacción final", value=st.session_state["redaccion"], height=500)
    total = len(st.session_state["redaccion"].split())
    st.markdown(f"📊 Palabras totales: {total}")
    if st.button("💾 Exportar a Word"):
        doc = Document()
        doc.add_heading(st.session_state["subtitulo"], level=1)
        doc.add_paragraph(st.session_state["redaccion"])
        ruta = "/mnt/data/acewriter_v15.docx"
        doc.save(ruta)
        with open(ruta, "rb") as f:
            st.download_button("📥 Descargar documento", data=f, file_name="ACEWriter_v15.docx")
