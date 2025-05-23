
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
    prompt = f"""🎯 PROMPT PARA API DE GENERACIÓN DE TEXTO DEL EBOOK ACE\n\nActuás como un generador automático de contenido técnico para eBooks educativos en ciencias del ejercicio. Tu objetivo es redactar textos que cumplan con todos los criterios de calidad definidos por el Proyecto ACE, exceptuando la inclusión de Call to Actions (CTA), que no es necesaria en esta sección.\n\n📌 Instrucciones de mejora obligatoria:\n\nRevisa cada texto generado y asegurate de cumplir con los siguientes 11 criterios. Si algún punto no se cumple, ajustá automáticamente el texto:\n\n1. Estructura clara con títulos jerárquicos (#, ##, ###)\n2. Subtemas bien delimitados, con desarrollo lógico y progresivo.\n3. Evidencia científica actual, basada en revisiones sistemáticas o meta-análisis Q1/Q2 entre 2005 y 2025 (citar DOI).\n4. Referencias en formato APA 7, al final del texto.\n5. Sugerencias visuales útiles (diagramas, tablas, gráficos, infografías por sección).\n6. Tono técnico y cercano, dirigido al profesional o coach.\n7. Frases cortas y activas, evitando la voz pasiva.\n8. Storytelling breve, mediante ejemplos prácticos o casos reales.\n9. Aplicación práctica clara, indicando cómo el contenido se usa en el entrenamiento real.\n10. No redundancia ni relleno, con revisión activa de repeticiones conceptuales o verbales.\n11. Consistencia visual sugerida, alineada con el diseño limpio, profesional y la paleta ACE.\n\n🔁 Cada respuesta debe ser autoevaluada internamente con este checklist antes de entregarse.\n\nRedactá el subtema titulado: {subtema}\nCapítulo: {capitulo}\n\n📚 Lista de referencias válidas:\n{chr(10).join(referencias)}\n\n"""
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
        with st.spinner("✍️ Generando texto..."):
            r1 = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4096
            )
        return r1.choices[0].message.content
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
            apellido = ref.split(",")[0]
            if apellido.lower() in texto.lower():
                citas.append(ref)
        st.session_state["citadas"] = list(set(citas))

# Paso 5 – Mostrar texto
if st.session_state.get("redaccion"):
    st.subheader("🧾 Redacción generada")
    st.text_area("Texto", value=st.session_state["redaccion"], height=500)
    st.markdown(f"📊 Palabras: **{len(st.session_state['redaccion'].split())}**")
    st.markdown(f"📚 Citas detectadas: **{len(st.session_state['citadas'])}**")

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
