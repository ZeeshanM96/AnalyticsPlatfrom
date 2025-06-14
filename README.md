# Precis Digital Analytics Dashboard

## Description

Precis Digital Analytics Dashboard is a full-stack web application for real-time monitoring and analytics of business events, alerts, and service metrics. It features secure JWT authentication, role-based access, and a modern, interactive dashboard for operational intelligence and business insights. The platform supports real-time data updates via WebSockets, customizable views, and user preferences for a tailored analytics experience.

---

## Features

- **User Authentication:** Secure JWT-based login and signup with role-based access (Client/Developer).
- **Interactive Dashboard:** Visualize batches, events, alerts, and service metrics with dynamic charts and filters.
- **Real-Time Data:** Live updates for dashboard stats and alerts using WebSockets.
- **Customizable Views:** Users can personalize dashboard cards and preferences.
- **RESTful API:** FastAPI backend with robust validation and efficient SQL aggregation.
- **Responsive Frontend:** Built with Bootstrap 5 and Chart.js for a modern, mobile-friendly UI.

---

## Tools & Technologies

- **Backend:** FastAPI, Pydantic, pyodbc, SQL Server, JWT (PyJWT)
- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript (ES6), Chart.js
- **Real-Time:** WebSocket (FastAPI)
- **Authentication:** JWT (JSON Web Tokens)
- **Database:** Microsoft SQL Server

---

## Getting Started

### Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/ZeeshanM96/AnalyticsPlatfrom.git
   cd AnalyticsPlatfrom
   ```

2. **Create and activate a virtual environment:**
  ```sh
  python -m venv venv
  # On Windows:
  venv\Scripts\activate
  # On macOS/Linux:
  source venv/bin/activate
  ```

2. **Install backend dependencies:**
  ```sh
  pip install -r requirements.txt
  ```
3. **Configure your database connection:**
  Edit backend/db.py with your DB details.

### Running the Application
Start the FastAPI backend:
  ```sh
  uvicorn backend.main:app --reload
  ```
Initiate the real time data script to injest data into your table:
   ```sh
  python insert_data.py
  ```

### Access the application:
- Open your browser and go to: http://localhost:8000
- The dashboard is available after login. Start off by creating your own login.
 
### System Design:

### DB design:
![DBDesign](https://github.com/user-attachments/assets/675db00b-9468-42b6-af57-45e04794b26d)

### Application Design:
![Screenshot 2025-06-14 020859](https://github.com/user-attachments/assets/d11b00c2-409d-47e4-b4c8-440ca9e8b40c)


### Additional Notes
All API endpoints are documented and accessible via /docs (FastAPI Swagger UI).
For real-time features, ensure your browser supports WebSockets.

### License
This project is licensed under the MIT License.
