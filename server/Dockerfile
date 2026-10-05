FROM python:3.13-slim-bookworm

ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install poetry==2.1.3

COPY pyproject.toml poetry.lock ./

COPY src ./src

COPY README.md ./

RUN poetry install --no-root

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
