# Digital Analytics Dashboard

## Description

Digital Analytics Dashboard is a full-stack, containerized web application for real-time monitoring and analytics of business events, alerts, and service metrics. It features secure JWT authentication, role-based access, and a modern, interactive dashboard for operational intelligence and business insights.

The platform supports real-time data updates via WebSockets, powered by a Kafka message bus, enabling live streaming of metrics and alerts to the frontend. Data is ingested and processed through Kafka producers and consumers, with persistent storage in a SQL database. Users can customize their dashboard views and preferences for a tailored analytics experience.

The backend is built with FastAPI and integrates with Kafka and SQL databases, while the frontend is a responsive HTML/CSS/JS application using Chart.js for visualizations. The entire stack is dockerized for easy deployment, and CI/CD pipelines are included for automated testing and code quality.

---

## Features

- **User Authentication** (JWT-based)
- **Role-based Access Control** (Admin/User)
- **Real-time Alerts & Notifications**
- **Batch & Severity-based Alert Summaries**
- **Interactive Charts & Visualizations** (Chart.js)
- **User Preferences & Customization**
- **RESTful API Endpoints**
- **Responsive Frontend** (Bootstrap 5)
- **Dockerized Deployment**
- **CI/CD with GitHub Actions**
- **Kafka-based Data Ingestion and Streaming**
- **Real-time Data Updates via WebSockets**

---

## Tools & Technologies

- **Database:** Microsoft SQL Server
- **Backend:** FastAPI, SQLAlchemy, PyODBC, Pydantic, PyJWT, Confluent-Kafka
- **Frontend:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Chart.js
- **Real-Time:** Kafka, WebSocket (FastAPI)
- **Authentication:** JWT (JSON Web Tokens)
- **Database:** SQL Server (or compatible, via ODBC)
- **Testing:** Pytest, FastAPI TestClient
- **Linting/Formatting:** Flake8, Black, Prettier, ESLint, Stylelint
- **Containerization:** Docker, Docker Compose
- **CI/CD:** GitHub Actions

---

## Getting Started
### Prerequisites

- [Docker](https://www.docker.com/get-started) & [Docker Compose](https://docs.docker.com/compose/)
- (Optional for local dev) Python 3.10+ and pip

### Installation

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
   ```
3. **Build and Run with Docker**

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




### Additional Notes
All API endpoints are documented and accessible via /docs (FastAPI Swagger UI).
For real-time features, ensure your browser supports WebSockets.

### License
This project is licensed under the MIT License.
