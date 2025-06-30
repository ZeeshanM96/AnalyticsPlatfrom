FROM python:3.10-slim

# Install system packages and Microsoft ODBC Driver 17 for SQL Server
RUN apt-get update && \
    apt-get install -y gnupg curl && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && ACCEPT_EULA=Y apt-get install -y \
        msodbcsql17 \
        unixodbc-dev \
        gcc \
        g++ \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 8000

CMD ["bash", "-c", "python injestion/set_api_key.py && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]


