import os
import uuid
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ..api.models.handlers import router

app = FastAPI()
app.include_router(router)
calculate_status = {}

INPUT_FOLDER = "input_test"
OUTPUT_FOLDER = "output_test"

os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def clear_status():
    """Очистить статус перед каждым тестом."""
    calculate_status.clear()


@patch("app.backend.api.models.handlers.calculate_recomendations")
def test_start_calculate(mock_calculate, client):

    base_file_content = b"Test base file content"
    base_file_name = "test_base.txt"

    response = client.post(
        "/calculate/",
        files={"base_file": (base_file_name, base_file_content)},
        data={"use_secondary_file": "false", "N": 5},
    )

    assert response.status_code == 200
    assert "calculate_id" in response.json()


def test_get_calculate_status(client):
    calculate_id = str(uuid.uuid4())
    calculate_status[calculate_id] = "in_progress"

    response = client.get(f"/check-calculate-status/{calculate_id}")
    assert response.status_code == 200

    calculate_status[calculate_id] = "completed"

    response = client.get(f"/check-calculate-status/{calculate_id}")
    assert response.status_code == 200


def test_download_file(client):

    calculate_id = str(uuid.uuid4())
    test_file_path = os.path.join(OUTPUT_FOLDER, f"result_{calculate_id}.txt")
    with open(test_file_path, "w") as f:
        f.write("Test result content")

    response = client.get(f"/download-result/{calculate_id}")
    assert response.status_code == 200

    os.remove(test_file_path)
