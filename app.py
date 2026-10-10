from __future__ import annotations

import streamlit as st
import json
import os
from datetime import datetime, date
from collections import Counter

import pandas as pd


st.set_page_config(
    page_title=" Dashboard de Tareas",
    page_icon="📋",
    layout="wide",
)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tareas.json")


def cargar_tareas() -> list[dict]:
    """Carga las tareas desde el archivo JSON."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def guardar_tareas(tareas: list[dict]):
    """Guarda las tareas en el archivo JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tareas, f, ensure_ascii=False, indent=2, default=str)


# --- Inicializar estado ---
if "tareas" not in st.session_state:
    st.session_state.tareas = cargar_tareas()

CATEGORIAS = ["📌 General", "💼 Trabajo", "📚 Estudio", "🏠 Hogar", "💪 Salud", "🎯 Proyecto"]
PRIORIDADES = {"🔴 Alta": 1, "🟡 Media": 2, "🟢 Baja": 3}

# --- CSS personalizado ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        text-align: center;
        padding: 0.5rem 0 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    .metric-card h3 { margin: 0; font-size: 2rem; }
    .metric-card p { margin: 0; font-size: 0.9rem; opacity: 0.85; }
    .task-done { text-decoration: line-through; opacity: 0.55; }
</style>
""", unsafe_allow_html=True)


st.markdown('<div class="main-header">📋 Dashboard de Tareas</div>', unsafe_allow_html=True)


with st.sidebar:
    st.header("➕ Nueva Tarea")
    with st.form("form_nueva_tarea", clear_on_submit=True):
        titulo = st.text_input("Título *", placeholder="Ej: Estudiar para el examen")
        descripcion = st.text_area("Descripción", placeholder="Detalles opcionales…", height=80)
        col_cat, col_pri = st.columns(2)
        with col_cat:
            categoria = st.selectbox("Categoría", CATEGORIAS)
        with col_pri:
            prioridad = st.selectbox("Prioridad", list(PRIORIDADES.keys()))
        usar_fecha = st.checkbox("¿Tiene fecha límite?")
        fecha_limite = st.date_input("Fecha límite") if usar_fecha else None
        submitted = st.form_submit_button("Agregar tarea", use_container_width=True)

        if submitted:
            if not titulo.strip():
                st.warning("El título es obligatorio.")
            else:
                nueva = {
                    "id": int(datetime.now().timestamp() * 1000),
                    "titulo": titulo.strip(),
                    "descripcion": descripcion.strip(),
                    "categoria": categoria,
                    "prioridad": prioridad,
                    "fecha_limite": str(fecha_limite) if fecha_limite else None,
                    "completada": False,
                    "fecha_creacion": datetime.now().isoformat(),
                }
                st.session_state.tareas.insert(0, nueva)
                guardar_tareas(st.session_state.tareas)
                st.success(f"✅ «{titulo}» agregada")
                st.rerun()

    st.divider()
    st.header("🔍 Filtros")
    filtro_estado = st.radio("Estado", ["Todas", "Pendientes", "Completadas"], horizontal=True)
    filtro_categoria = st.multiselect("Categorías", CATEGORIAS, default=[])
    filtro_prioridad = st.multiselect("Prioridades", list(PRIORIDADES.keys()), default=[])

# =====================================================================
# MÉTRICAS
# =====================================================================
tareas = st.session_state.tareas
total = len(tareas)
completadas = sum(1 for t in tareas if t["completada"])
pendientes = total - completadas
porcentaje = int((completadas / total) * 100) if total else 0

# Tareas vencidas (fecha límite pasada y no completadas)
hoy = str(date.today())
vencidas = sum(
    1 for t in tareas
    if not t["completada"] and t.get("fecha_limite") and t["fecha_limite"] < hoy
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("📊 Total", total)
m2.metric("⏳ Pendientes", pendientes)
m3.metric("✅ Completadas", f"{completadas}  ({porcentaje}%)")
m4.metric("⚠️ Vencidas", vencidas)

st.divider()

# =====================================================================
# BARRA DE PROGRESO
# =====================================================================
if total:
    st.caption(f"Progreso general: {porcentaje}%")
    st.progress(porcentaje / 100)

# =====================================================================
# APLICAR FILTROS
# =====================================================================
tareas_filtradas = list(tareas)

if filtro_estado == "Pendientes":
    tareas_filtradas = [t for t in tareas_filtradas if not t["completada"]]
elif filtro_estado == "Completadas":
    tareas_filtradas = [t for t in tareas_filtradas if t["completada"]]

if filtro_categoria:
    tareas_filtradas = [t for t in tareas_filtradas if t["categoria"] in filtro_categoria]

if filtro_prioridad:
    tareas_filtradas = [t for t in tareas_filtradas if t["prioridad"] in filtro_prioridad]

# Ordenar por prioridad (alta primero) y luego pendientes primero
tareas_filtradas.sort(key=lambda t: (t["completada"], PRIORIDADES.get(t["prioridad"], 99)))

# =====================================================================
# LISTA DE TAREAS
# =====================================================================
if not tareas_filtradas:
    st.info("No hay tareas que mostrar. ¡Agrega una desde la barra lateral! 👈")
else:
    st.subheader(f"📝 Tareas ({len(tareas_filtradas)})")
    for i, tarea in enumerate(tareas_filtradas):
        tid = tarea["id"]
        esta_vencida = (
            not tarea["completada"]
            and tarea.get("fecha_limite")
            and tarea["fecha_limite"] < hoy
        )
        borde = "🔴" if esta_vencida else ("✅" if tarea["completada"] else "⬜")

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([0.5, 6, 2, 2])

            with c1:
                st.markdown(f"### {borde}")

            with c2:
                titulo_display = tarea["titulo"]
                if tarea["completada"]:
                    titulo_display = f"~~{titulo_display}~~"
                st.markdown(f"**{titulo_display}**")
                detalles = f"{tarea['categoria']}  ·  {tarea['prioridad']}"
                if tarea.get("fecha_limite"):
                    detalles += f"  ·  📅 {tarea['fecha_limite']}"
                st.caption(detalles)
                if tarea["descripcion"]:
                    st.caption(tarea["descripcion"])

            with c3:
                if not tarea["completada"]:
                    if st.button("✅ Completar", key=f"done_{tid}"):
                        for t in st.session_state.tareas:
                            if t["id"] == tid:
                                t["completada"] = True
                                t["fecha_completada"] = datetime.now().isoformat()
                                break
                        guardar_tareas(st.session_state.tareas)
                        st.rerun()
                else:
                    if st.button("↩️ Reabrir", key=f"undo_{tid}"):
                        for t in st.session_state.tareas:
                            if t["id"] == tid:
                                t["completada"] = False
                                t.pop("fecha_completada", None)
                                break
                        guardar_tareas(st.session_state.tareas)
                        st.rerun()

            with c4:
                if st.button("🗑️ Eliminar", key=f"del_{tid}"):
                    st.session_state.tareas = [t for t in st.session_state.tareas if t["id"] != tid]
                    guardar_tareas(st.session_state.tareas)
                    st.rerun()

# =====================================================================
# GRÁFICAS (solo si hay tareas)
# =====================================================================
if total:
    st.divider()
    st.subheader("📊 Estadísticas")

    g1, g2 = st.columns(2)

    # Tareas por categoría
    conteo_cat = Counter(t["categoria"] for t in tareas)
    with g1:
        df_cat = pd.DataFrame(conteo_cat.items(), columns=["Categoría", "Cantidad"])
        df_cat = df_cat.sort_values("Cantidad", ascending=False)
        st.bar_chart(df_cat, x="Categoría", y="Cantidad")

    # Tareas por prioridad
    conteo_pri = Counter(t["prioridad"] for t in tareas)
    with g2:
        df_pri = pd.DataFrame(conteo_pri.items(), columns=["Prioridad", "Cantidad"])
        st.bar_chart(df_pri, x="Prioridad", y="Cantidad")

# --- Pie de página ---
st.divider()
st.caption("Dashboard de Tareas · Hecho con Streamlit 🐍")

