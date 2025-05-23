
import streamlit as st
import pandas as pd
from docx import Document
import openai
import time

st.set_page_config(page_title="ACE Writer Mini v13", layout="wide")
st.title("ACE Writer – Redacción con ampliación automática")

if "clave" not in st.session_state:
    st.session_state["clave"] = ""
if "redaccion" not in st.session_state:
    st.session_state["redaccion"] = ""
if "segunda_parte" not in st.session_state:
    st.session_state["segunda_parte"] = ""
if "completo" not in st.session_state:
    st.session_state["completo"] = ""
if "referencias" not in st.session_state:
    st.session_state["referencias"] = []
if "subtitulo" not in st.session_state:
    st.session_state["subtitulo"] = ""

st.subheader("Paso 0 – API Key")
st.session_state["clave"] = st.text_input("API Key OpenAI", type="password")

def generar(parte, referencias, subtitulo, clave):
    client = openai.OpenAI(api_key=clave)
    ref_texto = "\n".join([
        f"{i+1}. {r['Autores']} ({r['Año']}). {r['Título del artículo']}. {r['Journal']}."
        for i, r in enumerate(referencias)
    ])
    ampliacion = "Esta es una continuación de una redacción iniciada previamente. Continuá sin repetir lo anterior." if parte == 2 else ""
    prompt = f"""
Actuás como redactor científico para un eBook de entrenamiento de fuerza. Vas a redactar un subtema con base científica para coaches.

Subtema: {subtitulo}

Instrucciones:
- Redactá con tono técnico-claro y voz cercana
- Mínimo 1500 palabras en total. Esta es la parte {parte}.
- Cada ~500 palabras sugerí una imagen educativa (ej: 'Sugerir imagen: curva fuerza-potencia')
- Al final, agregá las referencias utilizadas en formato APA 7

{ampliacion}

Usá estas referencias como base (sin inventar):

{ref_texto}
"""

    respuesta = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Sos redactor científico experto en entrenamiento y ciencias del ejercicio."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.65,
        max_tokens=5000
    )
    return respuesta.choices[0].message.content

# Subida de referencias y subtítulo
archivo = st.file_uploader("📄 Subí tu tabla de referencias .csv", type=["csv"])
if archivo:
    df = pd.read_csv(archivo)
    referencias = []
    for i, row in df.iterrows():
        if all(pd.notna(row[col]) and str(row[col]).strip() != "" for col in ["Autores", "Año", "Título del artículo", "Journal"]):
            referencias.append(row)
    st.session_state["referencias"] = referencias

st.session_state["subtitulo"] = st.text_input("✏️ Subtítulo del capítulo", value=st.session_state["subtitulo"])

# Generar parte 1
if st.button("🚀 Generar redacción (Parte 1)") and st.session_state["clave"] and st.session_state["referencias"]:
    with st.spinner("Generando redacción (Parte 1)..."):
        st.session_state["redaccion"] = generar(1, st.session_state["referencias"], st.session_state["subtitulo"], st.session_state["clave"])
        time.sleep(1)

if st.session_state["redaccion"]:
    st.subheader("Parte 1 generada")
    st.text_area("Contenido Parte 1", value=st.session_state["redaccion"], height=400)
    palabras = len(st.session_state["redaccion"].split())
    st.markdown(f"📊 Palabras generadas: {palabras}")
    if palabras < 1300:
        st.info("Se generó menos de 1500 palabras. Podés generar una ampliación abajo.")

    if st.button("➕ Solicitar ampliación (Parte 2)"):
        with st.spinner("Solicitando ampliación..."):
            st.session_state["segunda_parte"] = generar(2, st.session_state["referencias"], st.session_state["subtitulo"], st.session_state["clave"])

# Mostrar ampliación
if st.session_state["segunda_parte"]:
    st.subheader("Parte 2 generada")
    st.text_area("Contenido Parte 2", value=st.session_state["segunda_parte"], height=400)

# Exportar
if st.session_state["redaccion"] or st.session_state["segunda_parte"]:
    if st.button("💾 Exportar Word completo"):
        doc = Document()
        doc.add_heading(st.session_state["subtitulo"], level=1)
        doc.add_paragraph(st.session_state["redaccion"])
        if st.session_state["segunda_parte"]:
            doc.add_paragraph(st.session_state["segunda_parte"])
        ruta = "/mnt/data/redaccion_completa_v13.docx"
        doc.save(ruta)
        with open(ruta, "rb") as f:
            st.download_button("📥 Descargar redacción completa", data=f, file_name="ACEWriter_v13.docx")
