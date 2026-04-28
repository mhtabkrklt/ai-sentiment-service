# Слабая связность
# UX асинхронности
# Обработка сбоев
# Визуальная репрезентация
import os
import time

import httpx
import plotly.graph_objects as go
import streamlit as st

API_URL = os.getenv("API_URL", "http://nginx/api")

st.set_page_config(page_title="Анализ тональности", layout="wide")
st.title("Анализ тональности русскоязычных текстов")

if "history" not in st.session_state:
    st.session_state.history = []

tab_sync, tab_async, tab_health = st.tabs(
    ["Быстрый анализ", "Асинхронный (длинный текст)", "Здоровье сервиса"]
)


def _safe_request(method: str, url: str, **kwargs):
    try:
        resp = getattr(httpx, method)(url, timeout=30, **kwargs)
        if resp.status_code == 503:
            st.warning("⚠️ Сервис временно недоступен")
            return None
        return resp
    except httpx.RequestError:
        st.warning("⚠️ Сервис временно недоступен")
        return None


def _plot_scores(all_scores: dict):
    labels = list(all_scores.keys())
    values = list(all_scores.values())
    colors = {
        "POSITIVE": "#2ecc71",
        "NEGATIVE": "#e74c3c",
        "NEUTRAL": "#3498db",
    }
    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker_color=[colors.get(lbl, "#95a5a6") for lbl in labels],
            )
        ]
    )
    fig.update_layout(
        title="Вероятности классов",
        yaxis_title="Вероятность",
        yaxis_range=[0, 1],
    )
    st.plotly_chart(fig, use_container_width=True)


def _plot_history_data(entries: list):
    counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
    for entry in entries:
        label = entry.get("label", "NEUTRAL")
        counts[label] = counts.get(label, 0) + 1
    colors = {
        "POSITIVE": "#2ecc71",
        "NEGATIVE": "#e74c3c",
        "NEUTRAL": "#3498db",
    }
    fig = go.Figure(
        data=[
            go.Bar(
                x=list(counts.keys()),
                y=list(counts.values()),
                marker_color=[colors[k] for k in counts],
            )
        ]
    )
    fig.update_layout(title=f"Распределение тональностей (всего: {len(entries)})")
    st.plotly_chart(fig, use_container_width=True)


with tab_sync:
    text_sync = st.text_area(
        "Введите текст для анализа",
        key="sync_text",
        max_chars=2000,
        height=150,
    )
    if st.button("Анализировать", key="sync_btn"):
        if not text_sync.strip():
            st.error("Введите текст")
        else:
            with st.spinner("Анализирую..."):
                resp = _safe_request(
                    "post",
                    f"{API_URL}/analyze",
                    json={"text": text_sync},
                )
            if resp and resp.status_code == 200:
                data = resp.json()
                st.session_state.history.append(data)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Тональность", data["label"])
                    st.metric("Уверенность", f"{data['confidence']:.1%}")
                    st.metric("Время", f"{data['elapsed_ms']:.0f} мс")
                with col2:
                    _plot_scores(data["all_scores"])
            elif resp:
                st.error(f"Ошибка: {resp.status_code} — {resp.text}")

with tab_async:
    text_async = st.text_area(
        "Введите текст для анализа",
        key="async_text",
        max_chars=2000,
        height=150,
    )
    if st.button("Отправить в очередь", key="async_btn"):
        if not text_async.strip():
            st.error("Введите текст")
        else:
            resp = _safe_request(
                "post",
                f"{API_URL}/analyze/async",
                json={"text": text_async},
            )
            if resp and resp.status_code == 202:
                task_id = resp.json()["task_id"]
                st.info(f"Задача создана: {task_id}")
                progress_bar = st.progress(0)
                status_placeholder = st.empty()
                max_polls = 120
                for i in range(max_polls):
                    poll = _safe_request("get", f"{API_URL}/tasks/{task_id}")
                    if poll is None:
                        break
                    poll_data = poll.json()
                    status = poll_data["status"]
                    progress_bar.progress(min((i + 1) / max_polls, 1.0))
                    status_placeholder.text(f"Статус: {status}")
                    if status == "SUCCESS":
                        result = poll_data["result"]
                        st.session_state.history.append(result)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Тональность", result["label"])
                            st.metric(
                                "Уверенность", f"{result['confidence']:.1%}"
                            )
                            st.metric(
                                "Время", f"{result['elapsed_ms']:.0f} мс"
                            )
                        with col2:
                            _plot_scores(result["all_scores"])
                        break
                    elif status == "FAILURE":
                        st.error(
                            f"Задача завершилась с ошибкой: {poll_data.get('error')}"
                        )
                        break
                    time.sleep(0.5 if i < 10 else 1)
            elif resp:
                st.error(f"Ошибка: {resp.status_code}")

with tab_health:
    if st.button("Проверить здоровье", key="health_btn"):
        resp = _safe_request("get", f"{API_URL}/health")
        if resp and resp.status_code in (200, 503):
            data = resp.json()
            st.json(data)
        elif resp:
            st.error(f"Ошибка: {resp.status_code}")

st.divider()
st.subheader("История запросов")
resp_hist = _safe_request("get", f"{API_URL}/history")
if resp_hist and resp_hist.status_code == 200:
    history_data = resp_hist.json()
    if history_data:
        _plot_history_data(history_data)
        with st.expander("Показать таблицу"):
            st.dataframe(
                [
                    {
                        "Текст": e["text"],
                        "Тональность": e["label"],
                        "Уверенность": f"{e['confidence']:.1%}",
                        "Время (мс)": f"{e['elapsed_ms']:.0f}",
                        "Дата": e["created_at"][:19].replace("T", " "),
                    }
                    for e in history_data
                ]
            )
    else:
        st.info("История пуста")
else:
    st.info("История недоступна")
