# Digital Analytics Dashboard

## Description

Digital Analytics Dashboard is a full-stack, containerized web application for real-time monitoring and analytics of business events, alerts, and service metrics. The platform features secure OAuth and JWT-based authentication, role-based access, and a modern, interactive dashboard for operational intelligence and business insights.

**Real-time data ingestion** is supported via a WebSocket API, allowing external sources to stream metrics directly into the system. Data is validated, authorized via API keys (managed in Redis), and published to Kafka topics for downstream processing. Kafka consumers persist data to SQL Server and front-end, enabling live updates and historical analytics. The backend is built with FastAPI, while the frontend is a responsive HTML/CSS/JS application using Chart.js for visualizations. The stack is fully dockerized for easy deployment along with complete CI/CD pipeline

---

## Features

- **User Authentication** (OAuth, JWT)
- **Role-based Access Control** (Client/Developer)
- **API Key Management** for secure external ingestion (via Redis)
- **Real-time Data Ingestion** via WebSocket API
- **Kafka-based Streaming** for metrics and events
- **Interactive Charts & Visualizations** (Chart.js)
- **User Preferences & Customization**
- **RESTful API Endpoints** (FastAPI)
- **Responsive Frontend** (Bootstrap 5)
- **Dockerized Deployment**
- **CI/CD with GitHub Actions**
- **Real-time Data Updates via WebSockets**
- **Modular FastAPI Backend** with clear separation of API, ingestion, and Kafka logic

---

## Tools & Technologies

- **Database:** Microsoft SQL Server
- **Backend:** FastAPI, Pydantic, PyJWT, Confluent-Kafka, Redis
- **Ingestion:** FastAPI WebSocket, Redis (API key store), Kafka Producer
- **Kafka:** Confluent-Kafka Python client (Producer/Consumer)
- **Frontend:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Chart.js
- **Authentication:** OAuth (Google), JWT
- **Testing:** Pytest, FastAPI TestClient
- **Linting/Formatting:** Flake8, Black, Prettier, ESLint, Stylelint
- **Containerization:** Docker, Docker Compose
- **CI/CD:** GitHub Actions

---

## Data Ingestion & Real-Time Flow

### External Data Ingestion

- External sources can ingest data in real-time via a WebSocket endpoint exposed by the backend.
- **API Key Registration:**  
  Before sending data, register your API key in Redis using the script [`injestion/set_api_key.py`](injestion/set_api_key.py):
  ```sh
  python injestion/set_api_key.py
  ```
  This script reads `API_KEY`, `REDIS_HOST`, and `REDIS_PORT` from your `.env` and stores the key in Redis.

- **WebSocket Ingestion Endpoint:**  
  Send real-time metrics to the backend via WebSocket at:
  ```
  ws://localhost:8000/ws/ingest?api_key=YOUR_API_KEY
  ```
  The endpoint is implemented in [`injestion/external_ingest.py`](injestion/external_ingest.py).  
  Only registered API keys are allowed. Each message must include `source_id`, `metric_name`, and `value`.

- **Kafka Integration:**  
  Ingested data is published to Kafka topics (`EXTERNAL_TOPIC`, etc.), and backend consumers process and persist the data to SQL Server.


## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/ZeeshanM96/AnalyticsPlatfrom.git
   cd AnalyticsPlatfrom
   ```

2. **Configure Environment**

Create and setup your `.env` file and update with your database connection and secret keys.

   ```sh
   # Database config
   DB_SERVER=YOUR-LOCALHOST-IP, YOUR TCP/IP
   DB_DATABASE="YOUR DATABASE NAME"
   DB_USER="YOUR USERNAME"
   DB_PASSWORD="YOUR PASSWORD"
   ACCEPT_EULA=Y

   # JWT config
   JWT_SECRET=YOUR JWT SECRET
   JWT_ALGORITHM=HS256
   JWT_EXPIRATION_MINUTES=60

   # Kafka config
   KAFKA_BROKER=YOUR_BROKER:YOUR_PORT
   DB_TOPIC=YOUR_DBTOPIC
   WS_TOPIC=YOUR_WSTOPIC
   EXTERNAL_TOPIC=YOUR_EXTERNAL_TOPIC
   CONSUMER_GROUP_DB=YOUR_DB_WRITE_GROUP
   CONSUMER_GROUP_WS=YOUR_WS_GROUP
   CONSUMER_GROUP_EXTERNAL=YOUR_CONSUMER_GROUP_EXTERNAL
   PRODUCE_INTERVAL_SEC=1
   MESSAGES_PER_SECOND=1

   # Ingestion config
   REDIS_HOST=YOUR_REDIS_HOST
   REDIS_PORT=YOUR_REDIS_PORT
   API_KEY=YOUR_API_KEY

   # Google OAuth config
   GOOGLE_CLIENT_ID = YOUR_GOOGLE_CLIENT_ID
   GOOGLE_CLIENT_SECRET = YOUR_GOOGLE_CLIENT_SECRET
   SESSION_SECRET= YOUR_SESSION_SECRET
   ```
   Your can regenerate a smilar schema by running `database.sql` file
   
3. **Build and Run with Docker**
   Just for good practice pull down all the containers:
   ```sh
   docker compose down --volumes --remove-orphans
   ```
   then build it again,
   ```sh
   docker-compose up --build
   ```

- The backend will be available at [http://localhost:8000](http://localhost:8000)
- The frontend is served via FastAPI static routes (e.g., `/html/login.html`, `/html/dashboard.html`)

4. **Run Tests (Optional)**

```sh
docker-compose run --rm fastapi pytest
```

Or locally:

```sh
pip install -r requirements.txt
pytest
```

### System Design:

### DB design:
![DBDesign](https://github.com/user-attachments/assets/675db00b-9468-42b6-af57-45e04794b26d)

Your can regenerate a smilar schema using database.sql file

### Application Design:
![screencapture-127-0-0-1-8000-dashboard-2025-06-26-01_11_50_pages-to-jpg-0001](https://github.com/user-attachments/assets/15a9550b-bf6c-469d-bf53-fad9c24cf846)


### TODO's:
Add Observability & Monitoring Stack for Backend & Kafka.


### Additional Notes
All API endpoints are documented and accessible via /docs (FastAPI Swagger UI).
For real-time features, ensure your browser supports WebSockets.

### License
This project is licensed under the MIT License.
