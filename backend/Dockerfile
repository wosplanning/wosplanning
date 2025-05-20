###############################
#            Base             #
###############################
FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

###############################
#         Development         #
###############################
FROM base AS development

# Install development-specific packages if needed
RUN pip install --no-cache-dir pytest pytest-cov black isort

# Use hot reloading for development
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--reload" ]

###############################
#         Production          #
###############################
FROM base AS production

COPY . .

RUN pip install --no-cache-dir gunicorn

CMD [ "gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000" ]