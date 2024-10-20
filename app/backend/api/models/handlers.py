import os
import uuid

from fastapi import APIRouter, BackgroundTasks, File, Form, Response, UploadFile
from fastapi.responses import FileResponse

from api.constants import INPUT_FOLDER, OUTPUT_FOLDER
from logic.recomendation_model import get_N_recommendation, get_probability

router = APIRouter(tags=["Models"])
calculate_status = {}


def calculate_recomendations(
    calculate_id: str,
    base_file_path: str,
    use_secondary_file: bool,
    secondary_file_path: str = None,
    N: int = None,
) -> None:
    """
    Calculates friend recommendations based on input data and saves the results to a file.

    This function retrieves friend recommendations for a given user based on the provided
    base file and an optional secondary file containing additional user data. The results
    are saved to a text file, including the calculated probability of friendship if a
    secondary file is used.

    Parameters:
    - calculate_id (str): A unique identifier for the calculation task.
    - base_file_path (str): The file path to the base data file containing user friendships.
    - use_secondary_file (bool): A flag indicating whether to use a secondary file for
      additional user information.
    - secondary_file_path (str, optional): The file path to the secondary data file.
      Defaults to None if not provided.
    - N (int, optional): The number of top recommendations to generate. If None, all
      recommendations will be considered.

    Returns:
    - None: This function does not return a value. It writes the recommendations to a
      file named 'result_{calculate_id}.txt' in the OUTPUT_FOLDER directory.

    The function updates the global `calculate_status` dictionary to reflect the
    current status of the calculation ('in_progress' or 'completed') and handles
    potential friendship probabilities when a secondary file is provided.
    """
    calculate_status[calculate_id] = "in_progress"
    result_recommendations = get_N_recommendation(base_file_path=base_file_path, N=N)
    if secondary_file_path and use_secondary_file:
        result_recommendations = get_probability(
            top_n_recommendations=result_recommendations,
            secondary_file_path=secondary_file_path,
        )

    collected_data = result_recommendations.collect()
    result_file = os.path.join(OUTPUT_FOLDER, f"result_{calculate_id}.txt")

    with open(result_file, "w") as f:
        for row in collected_data:
            if secondary_file_path and use_secondary_file:
                f.write(f"{row['user']} {row['fof']}, {row['probability']}\n")
            else:
                f.write(f"{row['user']} {row['fof']}\n")
        calculate_status[calculate_id] = "completed"


@router.post("/calculate/",
             response_model=dict,
             responses={
                 200: {
                     "description": "Calculation started successfully.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "calculate_id": "some-unique-id"
                             }
                         }
                     }
                 },
                 404: {
                     "description": "File not found or upload error.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "error": "File not found"
                             }
                         }
                     }
                 }
             })
async def start_calculate(
    background_tasks: BackgroundTasks,
    base_file: UploadFile = File(...),
    secondary_file: UploadFile = File(None),
    use_secondary_file: bool = Form(...),
    N: int = 1,
) -> Response:
    """
    Start the calculation of friend recommendations.

    This endpoint processes the provided base and optional secondary files,
    triggers the recommendation calculation in the background,
    and returns a unique calculation ID.

    - **Parameters:**
        - `base_file`: The main file with user friendship data (required).
        - `secondary_file`: Additional file with user demographic information (optional).
        - `use_secondary_file`: Boolean indicating whether to use the secondary file.
        - `N`: Number of top recommendations to return (default is 1).

    - **Response:**
        - Returns a dictionary containing the `calculate_id`.
    """
    calculate_id = str(uuid.uuid4())
    calculate_status[calculate_id] = "pending"

    base_file_path = os.path.join(
        INPUT_FOLDER, f"base_file_{calculate_id}_{base_file.filename}"
    )
    with open(base_file_path, "wb") as buffer:
        buffer.write(await base_file.read())

    secondary_file_path = None
    if use_secondary_file and secondary_file:
        secondary_file_path = os.path.join(
            INPUT_FOLDER, f"secondary_file_{calculate_id}_{secondary_file.filename}"
        )
        with open(secondary_file_path, "wb") as buffer:
            buffer.write(await secondary_file.read())

    background_tasks.add_task(
        calculate_recomendations,
        calculate_id,
        base_file_path,
        use_secondary_file,
        secondary_file_path,
        N,
    )

    return {"calculate_id": calculate_id}


@router.get("/check-calculate-status/{calculate_id}",
            response_model=dict,
            responses={
                200: {
                    "description": "Status retrieved successfully.",
                    "content": {
                        "application/json": {
                            "example": {
                                "task_id": "some-unique-id",
                                "status": "completed",
                                "file_url": "/output/some-unique-id"
                            }
                        }
                    }
                },
                404: {
                    "description": "Calculation ID not found.",
                    "content": {
                        "application/json": {
                            "example": {
                                "task_id": "some-unique-id",
                                "status": "not_found"
                            }
                        }
                    }
                }
            })
async def get_calculate_status(calculate_id: str) -> Response:
    """
    Check the status of a calculation by its ID.

    This endpoint retrieves the current status of the calculation
    associated with the provided `calculate_id`.

    - **Parameters:**
        - `calculate_id`: The unique ID of the calculation.

    - **Response:**
        - Returns a dictionary containing the `task_id`, `status`, and optionally a `file_url`
          if the task is completed.
    """
    status = calculate_status.get(calculate_id, "not_found")
    if status == "completed":
        file_url = f"/output/{calculate_id}"
        return {"task_id": calculate_id, "status": status, "file_url": file_url}
    return {"task_id": calculate_id, "status": status}


@router.get("/download-result/{calculate_id}",
            responses={
                200: {
                    "description": "File downloaded successfully.",
                    "content": {
                        "application/octet-stream": {
                            "example": "Binary file data here."
                        }
                    }
                },
                404: {
                    "description": "File not found.",
                    "content": {
                        "application/json": {
                            "example": {
                                "error": "File not found"
                            }
                        }
                    }
                }
            })
async def download_file(calculate_id: str) -> Response:
    """
    Download the result of a completed calculation.

    This endpoint provides the ability to download the results
    of the calculations based on the `calculate_id`.

    - **Parameters:**
        - `calculate_id`: The unique ID of the completed calculation.

    - **Response:**
        - Returns the result file if found, otherwise returns an error message.
    """
    file_path = os.path.join(OUTPUT_FOLDER, f"result_{calculate_id}.txt")
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=f"result_{calculate_id}.txt")
    return {"error": "File not found"}
