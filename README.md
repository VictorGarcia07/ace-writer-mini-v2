
# ACE Writer Mini V2 – Versión Final (Exportación + Autocompletado)

Esta app de Streamlit permite a cualquier miembro del equipo (como Matías) generar subtemas completos para eBooks de ACE usando referencias científicas validadas.

---

## ✅ ¿Qué hace esta versión?

- Genera automáticamente el contenido del subtema usando GPT-4
- Detecta si el texto es demasiado corto (<1500 palabras) y lo amplía
- Valida cuántas palabras reales tiene
- Verifica si las referencias cargadas fueron citadas en el texto
- Exporta directamente el resultado en formato `.docx` o `.md`

---

## 📦 ¿Qué archivo subir a GitHub?

Subí y reemplazá este archivo:

```
ace_writer_mini_v2.py
```

💡 Debe estar en la raíz del repositorio.

---

## 📂 ¿Qué archivo subir a Streamlit Secrets?

Desde `Manage App → Secrets`, agregá esto:

```
OPENAI_API_KEY = "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

✅ Con comillas dobles `"..."`

---

## 📥 ¿Qué tiene que hacer Matías paso a paso?

1. Cargar la tabla `.csv` de referencias validada
2. Completar el nombre del capítulo y subtema
3. Presionar **“✍️ Generar redacción del subtema”**
4. Esperar a que se complete (incluso si necesita ampliación)
5. Validar cantidad de palabras y autores citados
6. Exportar el texto en `.docx` o `.md`

---

## 🧠 Notas técnicas para desarrolladores

- El texto ampliado se guarda en `st.session_state.final_text`
- Las referencias se buscan en la columna `"Referencia (APA 7)"`
- Usa `max_tokens=3200` en la primera tanda y 2000 si se necesita extensión
