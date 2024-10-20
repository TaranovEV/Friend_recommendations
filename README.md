# Friend Recommendations Application

This application provides a friend recommendation system utilizing FastAPI for the backend API, Apache Spark for data processing, and Streamlit for the interactive frontend. The system calculates potential friendships based on user demographics and existing friend relationships.

## Technologies Used

- **FastAPI**: A modern web framework for building APIs with Python 3.7+.
- **Apache Spark**: A unified analytics engine for big data processing, with built-in modules for streaming, SQL, machine learning, and graph processing.
- **Streamlit**: A framework for building interactive web applications in Python.

## Prerequisites

Make sure you have the following installed:

- Docker
- Docker Compose
- Make (optional but recommended)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd friend_recommendations
   ```
2. **Rename .evn.example to .env**

3. **Build the containers**:  
   This project uses a Makefile to simplify the setup.
   ```
   make app
   ```
   Another way run
   ```
   docker compose -f docker_compose/app.yaml --env-file .env up --build -d
   ```
This command will build and start both the backend and frontend containers.
## Running the Application
Access the FastAPI documentation: After the containers are up, you can access the FastAPI documentation by navigating to:

```bash
http://localhost:8000/api/docs
```
Access the Streamlit application: You can run the Streamlit frontend by navigating to:
```bash
http://localhost:8501
```
## Usage
Examples input files located in directory:  
``` /app/backend/input_file_examples```

**Frontend (Streamlit)**  
The Streamlit frontend allows users to upload files containing friend relationships and demographic data. After uploading, users can trigger the friend recommendation calculations, and the results will be displayed interactively.

**Backend (FastAPI)**  
The FastAPI backend handles the API requests, processing the uploaded data using Apache Spark. The backend provides endpoints to:

* Calculate friend recommendations based on uploaded data.
* Check the status of ongoing calculations.
* Download the results as a text file.  
! Result files add to folder: 
``` /app/backend/output```  
! Input files save in folder: 
``` /app/backend/input```

## API Endpoints
```POST /calculate/
Description: Starts the calculation of friend recommendations.
Request:
Files: Base file (required), secondary file (optional).
Form: Use secondary file (boolean), N (integer).
Response: Returns a calculation ID.
```
```
GET /check-calculate-status/{calculate_id}
Description: Checks the status of a specific calculation.
Response: Returns the task status and file URL if completed.
```
```
GET /download-result/{calculate_id}
Description: Downloads the result of the calculation.
Response: Returns the result file.
```

## Development
To develop or debug the backend or frontend, you can modify the files directly in the backend and frontend directories. 
Changes will take effect upon restarting the respective services.
