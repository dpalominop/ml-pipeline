import os

from celery import Celery, states
from fastapi import FastAPI
from starlette.responses import JSONResponse

from app import models

app = FastAPI()
tasks = Celery(broker=os.getenv("BROKER_URL"), backend=os.getenv("REDIS_URL"))


@app.post("/filter", status_code=201)
async def upload_images(data: models.FilterProductsModel):
    """
    Endpoint to query the database and upload the results to S3.
    Args:
        data (models.FilterProductsModel): Input parameters.
    Return:
        str: Id of task.
    """
    task = tasks.send_task(name="filter", kwargs=data.dict(), queue="imagery")
    return {"task_id": task.id}


@app.post("/predict", status_code=201)
async def predict_images(data: models.InferenceModel):
    """
    Endpoint to run inference task on images.
    Args:
        data (models.InferenceModel): Input parameters.
    Return:
        str: Id of task.
    """
    task = tasks.send_task(name="model", kwargs=data.dict(), queue="inference")
    return {"task_id": task.id}


@app.get("/task/{task_id}", status_code=200)
def get_task_result(task_id: str):
    """
    Endpoint to check the status of a task.
    Args:
        task_id (str): Id of task.
    Return:
        JSONResponse: TaskResult in json format.
    """
    result = tasks.AsyncResult(task_id)

    output = models.TaskResult(
        id=task_id,
        status=result.state,
        error=str(result.info) if result.failed() else None,
        result=result.get() if result.state == states.SUCCESS else None,
    )

    return JSONResponse(content=output.dict())
