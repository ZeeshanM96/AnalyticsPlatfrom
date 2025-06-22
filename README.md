# Digital Analytics Dashboard

## Description

Digital Analytics Dashboard is a full-stack web application for real-time monitoring and analytics of business events, alerts, and service metrics. It features secure JWT authentication, role-based access, and a modern, interactive dashboard for operational intelligence and business insights. The platform supports real-time data updates via WebSockets, customizable views, and user preferences for a tailored analytics experience. The backend is powered by FastAPI and connects to a SQL database, while the frontend is a responsive HTML/CSS/JS application.

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

---

## Tools & Technologies

- **Database:** Microsoft SQL Server
- **Backend:** FastAPI, SQLAlchemy, PyODBC, Pydantic, PyJWT
- **Frontend:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Chart.js
- **Real-Time:** WebSocket (FastAPI)
- **Authentication:** JWT (JSON Web Tokens)
- **Database:** SQL Server (or compatible, via ODBC)
- **Testing:** Pytest, FastAPI TestClient
- **Linting/Formatting:** Flake8, Black
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
   DB_SERVER=host.docker.internal,1433
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
![Screenshot 2025-06-14 020859](https://github.com/user-attachments/assets/d11b00c2-409d-47e4-b4c8-440ca9e8b40c)


### Additional Notes
All API endpoints are documented and accessible via /docs (FastAPI Swagger UI).
For real-time features, ensure your browser supports WebSockets.

### License
This project is licensed under the MIT License.
