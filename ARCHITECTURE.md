# Архитектура AI Sentiment Service

## Схема компонентов

```
                        ┌──────────────────┐
                        │    Клиент/Браузер │
                        └────────┬─────────┘
                                 │ :80
                        ┌────────▼─────────┐
                        │      Nginx       │
                        │  (reverse proxy) │
                        │  rate limit 5/m  │
                        └──┬───────────┬───┘
               /api/*      │           │      /*
            ┌──────────────▼──┐   ┌────▼────────────┐
            │   FastAPI (api)  │   │  Streamlit (ui) │
            │   :8000          │   │  :8501          │
            └──┬────────────┬──┘   └─────────────────┘
               │            │
    ┌──────────▼──┐   ┌─────▼───────────┐   ┌─────────────────┐
    │    Redis    │   │  Celery Worker  │   │   PostgreSQL    │
    │   :6379    │◄──┤  (ML inference) │   │   :5432         │
    │  db0=broker│   └─────────────────┘   │  (история)      │
    │  db1=result│                          └────────▲────────┘
    └────────────┘                                   │
                                              SQLAlchemy async
                                           (api → analyses table)
```

## Сети Docker

```
frontend_net:  nginx ←→ api ←→ ui
backend_net:   api ←→ worker ←→ redis ←→ postgres
```

UI и Nginx НЕ имеют прямого доступа к Redis и PostgreSQL.

## Порядок запуска

```
postgres ──healthy──► db-migrate (alembic upgrade head) ──► api
redis    ──healthy──►                                    ──► api
model-init ──done──►                                     ──► api ──healthy──► ui, nginx
                                                         ──► worker
```

## Потоки данных

### Синхронный анализ
```
Клиент → Nginx → FastAPI (POST /api/analyze)
                      │
                      ├─ Валидация Pydantic
                      ├─ model.predict(text)
                      ├─ Сохранить результат → PostgreSQL (analyses)
                      └─ Ответ: {label, confidence, all_scores, elapsed_ms}
```

### Асинхронный анализ
```
Клиент → Nginx → FastAPI (POST /api/analyze/async)
                      │
                      ├─ Создать Celery task
                      └─ Ответ 202: {task_id, status: "PENDING"}

Клиент → Nginx → FastAPI (GET /api/tasks/{id})
                      │
                      ├─ Запросить статус из Redis
                      └─ Ответ: {task_id, status, result|error}

                 Celery Worker
                      │
                      ├─ Получить задачу из Redis (broker)
                      ├─ Загрузить модель (ленивая инициализация)
                      ├─ model.predict(text)
                      └─ Сохранить результат в Redis (backend)
```

### WebSocket
```
Клиент ←ws→ Nginx → FastAPI (WS /api/ws/tasks/{id})
                      │
                      └─ Каждые 500мс: статус задачи из Redis
                         Закрытие при SUCCESS/FAILURE
```

### История анализов
```
Клиент → Nginx → FastAPI (GET /api/history)
                      │
                      ├─ SELECT * FROM analyses ORDER BY created_at DESC
                      └─ Ответ: [{id, text, label, confidence, ...}]
```

## Health Check

`GET /api/health` проверяет:
1. API жив
2. ML-модель загружена (`model.is_ready()`)
3. Redis доступен (`redis.ping()`)

Возвращает 200 если всё ОК, 503 если какой-то компонент недоступен.

## ML Pipeline

- Модель: `blanchefort/rubert-base-cased-sentiment` (RuBERT, 3 класса)
- Маппинг: 0=NEUTRAL, 1=POSITIVE, 2=NEGATIVE
- PyTorch: `torch.no_grad()`, `model.eval()`, `truncation=True`
- ONNX (опционально): `optimum.onnxruntime.ORTModelForSequenceClassification`
- Выбор backend: переменная `USE_ONNX` в `.env`

## База данных

- **ORM:** SQLAlchemy 2.0 async (`asyncpg` драйвер)
- **Миграции:** Alembic — файлы в `api/alembic/versions/`
- **Таблица `analyses`:**

| Колонка | Тип | Описание |
|---|---|---|
| `id` | UUID | Первичный ключ |
| `text` | TEXT | Входной текст |
| `label` | VARCHAR(10) | POSITIVE / NEGATIVE / NEUTRAL |
| `confidence` | FLOAT | Уверенность модели |
| `all_scores` | JSON | Вероятности всех классов |
| `elapsed_ms` | FLOAT | Время инференса |
| `created_at` | TIMESTAMPTZ | Время создания |

## Volumes

- `model_cache` — кэш весов модели (`/models`), расшарен между api и worker
- `redis_data` — персистентное хранилище Redis
- `postgres_data` — данные PostgreSQL (`/var/lib/postgresql/data`)
