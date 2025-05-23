import streamlit as st
import pandas as pd
import docx
import re
from io import BytesIO
import openai

# ---------- FUNCIONES ----------

def contar_tokens(texto):
    palabras = texto.split()
    return int(len(palabras) * 1.33)

def contar_palabras(texto):
    return len(texto.split())

def validar_citas(df):
    completas = df[df[['DOI', 'Título del artículo', 'Journal']].notnull().all(axis=1)]
    incompletas = df[~df.index.isin(completas.index)]
    return completas, incompletas

def extraer_apellidos_citados(texto):
    return re.findall(r'\(([^\)]+), \d{4}\)', texto)

def construir_referencias_apa(apellidos_en_texto, df_referencias):
    citas = []
    for _, fila in df_referencias.iterrows():
        apellido = fila['Autores'].split(',')[0].strip()
        if re.search(rf'\({apellido}, \d{{4}}\)', texto):
            citas.append(fila)
    referencias = []
    for _, fila in pd.DataFrame(citas).drop_duplicates().iterrows():
        ref = f"{fila['Autores']} ({fila['Año']}). {fila['Título del artículo']}. {fila['Journal']}, {fila['Volumen']}, {fila['Páginas']}. {fila['DOI']}"
        referencias.append(ref)
    return referencias, len(referencias)

def exportar_a_word(texto, referencias, plantilla):
    doc = docx.Document(plantilla)
    doc.add_paragraph(texto)
    doc.add_paragraph("\nAplicación práctica para el entrenador:")
    doc.add_paragraph("(Completar bloque de aplicación práctica aquí.)")
    doc.add_paragraph("\nReferencias:")
    for ref in referencias:
        doc.add_paragraph(ref, style='Normal')
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def redactar_con_gpt(subtema, capitulo, referencias, api_key):
    prompt = f"""Actuás como generador de contenido técnico para un eBook educativo en ciencias del ejercicio.
Vas a redactar un texto completo para el subtema: '{subtema}', perteneciente al capítulo '{capitulo}'.

Tu redacción debe cumplir con:
– Estilo técnico-claro, posgrado, voz cercana.
– Estructura: introducción, desarrollo con subtítulos, ejemplos prácticos, y conclusión aplicada.
– Integrar citas en formato APA (Apellido, Año) solo de esta lista:

{chr(10).join(referencias)}

No uses otras fuentes. No repitas conceptos. Redactá todo en una sola entrega. El mínimo es 1500 palabras, pero si el tema se agota bien en menos, está permitido.

Redactá ahora el texto completo:
"""

    try:
        client = openai.OpenAI(api_key=api_key)
        with st.spinner("Generando texto..."):
            r = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4096
            )
        return r.choices[0].message.content
    except Exception as e:
        st.error("Error al generar redacción: " + str(e))
        return ""

# ---------- INTERFAZ PRINCIPAL ----------

st.title("ACE Writer Mini v55")

api_key = st.text_input("API Key de OpenAI", type="password")
plantilla = st.file_uploader("Cargar plantilla Word (.docx)", type="docx")
archivo_csv = st.file_uploader("Cargar archivo de referencias (.csv)", type="csv")

if api_key and plantilla and archivo_csv:
    df = pd.read_csv(archivo_csv)
    completas, incompletas = validar_citas(df)
    st.success(f"Referencias completas: {len(completas)} | Incompletas: {len(incompletas)}")

    seleccionadas = []
    if not incompletas.empty:
        seleccionadas = st.multiselect("Selecciona manualmente las incompletas:", list(incompletas['Autores']))
        if st.button("Seleccionar todas las incompletas"):
            seleccionadas = list(incompletas['Autores'])

    referencias_validas = pd.concat([completas, incompletas[incompletas['Autores'].isin(seleccionadas)]])
    st.session_state["referencias"] = referencias_validas

    subtema = st.text_input("Subtítulo del subtema")
    if subtema and st.button("Generar redacción" if "redaccion" not in st.session_state else "Regenerar redacción"):
        lista_refs = [f"{a}, {b}" for a, b in zip(referencias_validas['Autores'], referencias_validas['Año'])]
        texto = redactar_con_gpt(subtema, "Capítulo auto-generado", lista_refs, api_key)
        st.session_state["redaccion"] = texto

    if "redaccion" in st.session_state:
        texto = st.session_state["redaccion"]
        st.subheader("Texto generado") 
        st.markdown(texto)

        palabras = contar_palabras(texto)
        st.write(f"Palabras: {palabras} | Tokens estimados: {contar_tokens(texto)}")

        if st.button("¿Por qué se truncó?"):
            razon = "Parece que el modelo consideró agotado el tema antes de llegar a 1500 palabras." if palabras < 1500 else "Texto completo generado."
            st.info(razon)

        if st.button("Descargar Word generado"):
            citas, _ = construir_referencias_apa(extraer_apellidos_citados(texto), st.session_state["referencias"])
            buffer = exportar_a_word(texto, citas, plantilla)
            st.download_button("Descargar .docx", data=buffer, file_name=f"{subtema}.docx")

        if st.button("Generar nuevo subtema"):
            for key in ["redaccion", "subtema", "citadas"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()