# AI Sentiment Service

Веб-сервис анализа тональности русскоязычных текстов. Классифицирует текст как **POSITIVE**, **NEGATIVE** или **NEUTRAL** на основе модели [blanchefort/rubert-base-cased-sentiment](https://huggingface.co/blanchefort/rubert-base-cased-sentiment).

## Скриншоты

| POSITIVE | NEGATIVE |
|---|---|
| ![Positive](docs/screenshot-1.png) | ![Negative](docs/screenshot-2.png) |

| Health check | История из БД |
|---|---|
| ![Health check](docs/screenshot-3.png) | ![История](docs/screenshot-4.png) |

## Стек технологий

| Компонент | Технология |
|---|---|
| Backend API | FastAPI + Pydantic v2 |
| ML-модель | Hugging Face Transformers (RuBERT) |
| ML-ускорение | ONNX Runtime через `optimum` (опционально) |
| Очередь задач | Celery + Redis |
| База данных | PostgreSQL + SQLAlchemy 2.0 (async) |
| Миграции | Alembic |
| UI | Streamlit + Plotly |
| Reverse proxy | Nginx (rate limiting 5 req/min) |
| Оркестрация | Docker Compose |
| Менеджер зависимостей | uv |

## Быстрый старт

```bash
cp .env.example .env
docker compose up --build -d
```

Первый запуск занимает 1–2 минуты: скачивается ML-модель (~700 MB) и применяются миграции БД.

Проверить готовность:

```bash
docker compose ps
```

Все контейнеры должны быть в статусе `healthy` или `running`.

- **UI:** http://localhost
- **API:** http://localhost/api
- **Swagger:** http://localhost/api/docs

## Примеры API

### Health check

```bash
curl http://localhost/api/health
```

```json
{"status": "ok", "checks": {"api": true, "model": true, "redis": true}}
```

### Синхронный анализ

```bash
curl -X POST http://localhost/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Отличный фильм!"}'
```

```json
{
  "label": "POSITIVE",
  "confidence": 0.9921,
  "all_scores": {"NEUTRAL": 0.0043, "POSITIVE": 0.9921, "NEGATIVE": 0.0036},
  "elapsed_ms": 142.5
}
```

### Асинхронный анализ

```bash
# 1. Отправить задачу
curl -X POST http://localhost/api/analyze/async \
  -H "Content-Type: application/json" \
  -d '{"text": "Ужасный сервис, всё сломано"}'
```

```json
{"task_id": "abc-123", "status": "PENDING"}
```

```bash
# 2. Получить результат (подставьте task_id из ответа выше)
curl http://localhost/api/tasks/abc-123
```

### История анализов

```bash
curl http://localhost/api/history
```

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "text": "Отличный фильм!",
    "label": "POSITIVE",
    "confidence": 0.9921,
    "all_scores": {"NEUTRAL": 0.0043, "POSITIVE": 0.9921, "NEGATIVE": 0.0036},
    "elapsed_ms": 142.5,
    "created_at": "2026-04-28T00:52:03+00:00"
  }
]
```

## Конфигурация

Все параметры задаются через `.env` (см. `.env.example`):

| Переменная | Описание | По умолчанию |
|---|---|---|
| `MODEL_NAME` | Название модели Hugging Face | `blanchefort/rubert-base-cased-sentiment` |
| `USE_ONNX` | Использовать ONNX Runtime вместо PyTorch | `false` |
| `MAX_TEXT_LENGTH` | Максимальная длина текста в токенах | `512` |
| `DATABASE_URL` | URL подключения к PostgreSQL | `postgresql+asyncpg://sentiment:sentiment@postgres:5432/sentiment` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

## Остановка

```bash
docker compose down
```

Чтобы также удалить данные БД и веса модели:

```bash
docker compose down -v
```
