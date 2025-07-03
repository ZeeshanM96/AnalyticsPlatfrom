# Digital Analytics Dashboard

## Description

Digital Analytics Dashboard is a full-stack, containerized web application for real-time monitoring and analytics of business events, alerts, and service metrics. The platform features secure OAuth and JWT-based authentication, role-based access, and a modern, interactive dashboard for operational intelligence and business insights.

**Real-time data ingestion** is supported via a WebSocket API, allowing external sources to stream metrics directly into the system. Data is validated, authorized via API keys and secret keys (managed in Redis), and published to Apache Pulsar. Puslar serves as data validation and data cleaning pipeline for us. Clean or valid data is injested to one topic and invalid data is injested to seperate topic. These topic are then published to Kafka topics for downstream processing. Kafka consumers persist data to SQL Server and front-end, enabling live updates and historical analytics. The backend is built with FastAPI, while the frontend is a responsive HTML/CSS/JS application using Chart.js for visualizations. The stack is fully dockerized for easy deployment along with complete CI/CD pipeline

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
  Before sending data, make sure `API_KEY` and `SECRET_KEY` exists for the specfic `SOURCEID`:

- **WebSocket Ingestion Endpoint:**  
  Test the end to send real-time metrics to the backend via WebSocket at:
  ```
  ws://localhost:8000/ws/ingest
  ```
  Make sure header must include `API_KEY`, `SECRET_KEY` and `SOURCEID` before making a request.
  Add a message body with matching below format:
  ```
  {
  "source_id": 1,
  "metric_name": "Humidity",
  "value": 60.4
  }
  ```
  and response would be:
  ![image](https://github.com/user-attachments/assets/e6c1332f-1cb5-4da0-908a-9b1998332f83)

  The endpoint is implemented in [`backend/websocket/websocket.py`](backend/websocket/websocket.py).  
  Only registered `API_KEY`, `SECRET_KEY` and `SOURCEID` are allowed.

  Test the websocket endpoint under `scripttotest` folder. Run the scripts and make sure headers and body is set before you make a request.

- **Apache Pulsar Integration:**  
  - **Pulsar Container:** Runs Apache Pulsar with an init script that deploys a custom Pulsar Function.
  - **Pulsar Function (`validate.Validator`):** Consumes messages from the `raw-ingest` topic, validates and cleanses them, then publishes to the `clean` and `fail` topic.
  - **Pulsar-Kafka Forwarder:** A script `pulsar_to_kafka.py` forwards messages from Pulsar to Kafka using predefined sink configurations.
  
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
   # FastAPI config
    DOMAIN_SERVER=YOUR_DOMAIN_HOST_SERVER
    DOMAIN_PORT=YOUR_DOMAIN_HOST_PORT

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
   FAILED_TOPIC=YOUR_FAILED_TOPIC
   CONSUMER_GROUP_DB=YOUR_DB_WRITE_GROUP
   CONSUMER_GROUP_WS=YOUR_WS_GROUP
   CONSUMER_GROUP_EXTERNAL=YOUR_CONSUMER_GROUP_EXTERNAL
   CONSUMER_GROUP_FAILED=YOUR_CONSUMER_GROUP_FAILED
   PRODUCE_INTERVAL_SEC=1
   MESSAGES_PER_SECOND=1

   # Ingestion config
   REDIS_HOST=YOUR_REDIS_HOST
   REDIS_PORT=YOUR_REDIS_PORT

   # Google OAuth config
   GOOGLE_CLIENT_ID = YOUR_GOOGLE_CLIENT_ID
   GOOGLE_CLIENT_SECRET = YOUR_GOOGLE_CLIENT_SECRET
   SESSION_SECRET= YOUR_SESSION_SECRET

   # Encryption config
   FERNET_KEY=YOUR_FERNET_KEY

   # Pulsar config
   PULSAR_SERVICE_URL=YOUR_PULSAR_SERVICE_URL
   RAW_TOPIC =YOUR_RAW_TOPIC
   PULSAR_CLEAN_TOPIC=YOUR_PULSAR_CLEAN_TOPIC
   PULSAR_DIRTY_TOPIC=YOUR_PULSAR_DIRTY_TOPIC
   ```
   Your can regenerate a smilar schema by running `database.sql` file

3. **Create and Acitivate the virtual ENV**
  ```sh
  python -m venv virenv
  ```
  then:
  ```sh
  .\virenv\Scripts\Activate.ps1
  ```
   
. **Build and Run with Docker**
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

5. **Run Tests (Optional)**

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


### Application Design:
![screencapture-127-0-0-1-8000-dashboard-2025-06-26-01_11_50_pages-to-jpg-0001](https://github.com/user-attachments/assets/15a9550b-bf6c-469d-bf53-fad9c24cf846)


### TODO's:
- Add Observability & Monitoring Stack for Backend & Kafka via Prometheus/Grafana/Loki.


### Additional Notes
All API endpoints are documented and accessible via /docs (FastAPI Swagger UI).
For real-time features, ensure your browser supports WebSockets.

### License
This project is licensed under the MIT License.
