
# ✍️ ACE Writer Mini V2

**ACE Writer Mini V2** es una aplicación web desarrollada con Streamlit para redactar subtemas de capítulos de eBooks técnicos en ciencias del ejercicio, utilizando exclusivamente referencias científicas validadas.

## 🚀 ¿Qué hace esta app?
- Permite seleccionar un capítulo y subtema del eBook.
- Carga una tabla de referencias validadas (archivo `.csv`).
- Ofrece un editor en tiempo real con contador de palabras (mínimo 1500).
- Verifica que todas las citas utilizadas provengan de la tabla cargada.
- Exporta el resultado en formato **Word (.docx)** o **Markdown (.md)**.
- Muestra las referencias científicas disponibles para consulta.

## 📁 Estructura del repositorio

- `ace_writer_mini_v2.py`: script principal de la app Streamlit.
- `tabla_ejemplo.csv`: tabla de referencias científicas en formato validado.

## 🧪 Ejemplo de uso

1. Subí tu tabla de referencias (debe incluir columnas: `Autor`, `Año`, `Título`, `DOI`).
2. Escribí el texto del subtema respetando el mínimo de palabras.
3. Insertá citas usando los apellidos de los autores.
4. Al final, exportá tu trabajo como `.docx` o `.md`.

## 🧠 Requisitos para correr localmente

```bash
pip install streamlit pandas python-docx
streamlit run ace_writer_mini_v2.py
```

## 📦 Hecho para
Proyecto **eBooks ACE** — Academia de Ciencias del Ejercicio  
Desarrollado por Vity & Carol ✨

---

© 2025 ACE Capacitación — Todos los derechos reservados.
