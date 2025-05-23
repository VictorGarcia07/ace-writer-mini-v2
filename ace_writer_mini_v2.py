
import streamlit as st
import pandas as pd
from docx import Document
import openai
import time

st.set_page_config(page_title="ACE Writer Mini v17", layout="wide")
st.title("ACE Writer – Redacción profesional con ampliación automática")

# Estado
if "clave_ok" not in st.session_state:
    st.session_state["clave_ok"] = False
if "referencias" not in st.session_state:
    st.session_state["referencias"] = []
if "subtema" not in st.session_state:
    st.session_state["subtema"] = ""
if "redaccion" not in st.session_state:
    st.session_state["redaccion"] = ""
if "export_ready" not in st.session_state:
    st.session_state["export_ready"] = False

# Paso 0 – Clave OpenAI
api_key = st.text_input("🔐 Ingresá tu clave OpenAI", type="password")
if api_key.startswith("sk-"):
    st.session_state["clave_ok"] = True
    st.success("✅ Clave válida")

# Paso 1 – Subir referencias
st.subheader("📄 Paso 1 – Subí la tabla de referencias .csv")
archivo_csv = st.file_uploader("Archivo .csv con referencias", type=["csv"])
referencias_formateadas = []

if archivo_csv:
    df = pd.read_csv(archivo_csv)
    for i, row in df.iterrows():
        if all(pd.notna(row[col]) and str(row[col]).strip() != "" for col in ["Autores", "Año", "Título del artículo", "Journal"]):
            ref_str = f"{row['Autores']} ({row['Año']}). {row['Título del artículo']}. {row['Journal']}."
            referencias_formateadas.append(ref_str)

# Paso 2 – Subtítulo del subtema
st.subheader("✏️ Paso 2 – Escribí el subtítulo del subtema")
st.session_state["subtema"] = st.text_input("Subtítulo:", value=st.session_state["subtema"])

# Paso 3 – Generar redacción
def redaccion_completa(subtema, referencias, api_key):
    client = openai.OpenAI(api_key=api_key)

    base_prompt = f"""
Actuás como redactor científico del Proyecto eBooks ACE.
Tu tarea es redactar el subtema titulado "{subtema}", que forma parte del eBook de entrenamiento de fuerza y potencia para entrenadores.

📌 Condiciones obligatorias:
– El texto debe tener mínimo 1500 palabras reales
– Incluir al menos 1 recurso visual sugerido cada 500 palabras
– Utilizar solo las referencias incluidas a continuación
– Cerrar con una sección de referencias en formato APA 7, solo con las fuentes citadas realmente en el cuerpo

📚 Lista de referencias válidas:
{chr(10).join(referencias)}

Redactá el texto directamente a continuación, en tono técnico claro, orientado a entrenadores profesionales, con ejemplos prácticos y subtítulos.
"""

    with st.spinner("✍️ Generando redacción inicial..."):
        time.sleep(1)
        respuesta = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Sos redactor experto en ciencias del ejercicio."},
                {"role": "user", "content": base_prompt}
            ],
            temperature=0.65,
            max_tokens=5000
        )
    texto = respuesta.choices[0].message.content
    return texto

def ampliacion_si_necesaria(texto, referencias, subtema, api_key):
    if len(texto.split()) >= 1500:
        return texto
    client = openai.OpenAI(api_key=api_key)
    prompt_ext = f"""
El siguiente texto fue generado para el subtema "{subtema}" pero es incompleto ({len(texto.split())} palabras).
Extendelo hasta alcanzar mínimo 1500 palabras, sin repetir lo anterior. Agregá ejemplos, análisis y profundidad técnica.

Texto original:
{texto}
"""
    with st.spinner("🔁 Solicitando ampliación automática..."):
        time.sleep(1)
        ampliado = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Sos redactor experto en entrenamiento."},
                {"role": "user", "content": prompt_ext}
            ],
            temperature=0.65,
            max_tokens=4000
        )
    return texto + "\n\n" + ampliado.choices[0].message.content

# Botón para generar
if st.button("🚀 Generar redacción"):
    if st.session_state["clave_ok"] and st.session_state["subtema"] and referencias_formateadas:
        redaccion_inicial = redaccion_completa(st.session_state["subtema"], referencias_formateadas, api_key)
        texto_final = ampliacion_si_necesaria(redaccion_inicial, referencias_formateadas, st.session_state["subtema"], api_key)
        st.session_state["redaccion"] = texto_final
        st.session_state["export_ready"] = True
        st.success(f"✅ Redacción lista con {len(texto_final.split())} palabras.")

# Mostrar texto generado
if st.session_state["redaccion"]:
    st.subheader("🧾 Redacción final")
    st.text_area("Texto generado", value=st.session_state["redaccion"], height=500)

# Exportar
if st.session_state["export_ready"]:
    if st.button("💾 Exportar Word"):
        doc = Document()
        doc.add_heading(st.session_state["subtema"], level=1)
        doc.add_paragraph(st.session_state["redaccion"])
        path = "/mnt/data/redaccion_final_v17.docx"
        doc.save(path)
        with open(path, "rb") as f:
            st.download_button("📥 Descargar Word", data=f, file_name="ACEWriter_v17.docx")
