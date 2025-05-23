
import streamlit as st
import pandas as pd
from docx import Document

st.set_page_config(page_title="ACE Writer v2 – Redacción Validada", layout="wide")

st.title("✍️ ACE Writer v2 – Redacción Validada")

# ----------------------------
# Funciones de validación
# ----------------------------

def validar_plantilla_word(path_plantilla):
    required_styles = [
        'Heading 1', 'Heading 2', 'Heading 3', 'Normal',
        'Quote', 'Reference', 'List Bullet', 'List Number'
    ]
    doc = Document(path_plantilla)
    styles = doc.styles
    results = []
    for style in required_styles:
        results.append({
            'Estilo': style,
            '¿Presente?': '✅ Sí' if style in styles else '❌ No'
        })
    return pd.DataFrame(results)

def validar_tabla_referencias_flexible(df):
    required_columns = [
        "Autores", "Año", "Título del artículo", "Journal",
        "Volumen", "Número", "Páginas", "DOI/URL",
        "Nivel de evidencia", "Cuartil", "Subtema asignado", "¿Incluir?", "Justificación"
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return pd.DataFrame([{"Error": f"Faltan columnas: {', '.join(missing_columns)}"}])

    results = []
    for _, row in df.iterrows():
        missing_critical = [col for col in ["Autores", "Año", "Título del artículo", "Journal", "DOI/URL"]
                            if pd.isna(row[col]) or str(row[col]).strip() == ""]
        missing_secondary = [col for col in required_columns if col not in missing_critical and 
                             (pd.isna(row[col]) or str(row[col]).strip() == "")]
        estado = (
            "✅ Completa" if not missing_critical and not missing_secondary else
            "⚠ Incompleta (faltan secundarios)" if not missing_critical else
            "🔍 Requiere revisión manual (faltan críticos)"
        )
        results.append({
            "Referencia": f"{row['Autores']} ({row['Año']}) - {row['Título del artículo']}",
            "Estado": estado,
            "Faltan críticos": ", ".join(missing_critical) if missing_critical else "",
            "Faltan secundarios": ", ".join(missing_secondary) if missing_secondary else ""
        })

    return pd.DataFrame(results)

# ----------------------------
# Flujo de ACE Writer
# ----------------------------

st.subheader("Paso 1️⃣ – Cargar Plantilla Word (.dotx)")
plantilla_file = st.file_uploader("Subí tu plantilla Word con estilos predefinidos", type=["dotx"])

if plantilla_file:
    plantilla_result = validar_plantilla_word(plantilla_file)
    st.write("✅ Resultado de validación de estilos:")
    st.dataframe(plantilla_result)

    if "❌ No" in plantilla_result["¿Presente?"].values:
        st.warning("La plantilla tiene errores. Subí una nueva antes de continuar.")
    else:
        st.success("Plantilla válida. Podés continuar al paso 2.")

        st.subheader("Paso 2️⃣ – Cargar tabla de referencias (.csv)")
        referencias_file = st.file_uploader("Subí la tabla con referencias científicas", type=["csv"])

        if referencias_file:
            df_referencias = pd.read_csv(referencias_file)
            resultado_refs = validar_tabla_referencias_flexible(df_referencias)
            st.write("📚 Resultado de validación de referencias:")
            st.dataframe(resultado_refs)

            if any(resultado_refs["Estado"].str.contains("Requiere revisión manual")):
                st.warning("Hay referencias con datos críticos faltantes. Revisá antes de continuar.")
            else:
                st.success("Referencias válidas. Ya podés redactar tu capítulo con tranquilidad.")
                st.button("📝 Redactar capítulo", type="primary")
