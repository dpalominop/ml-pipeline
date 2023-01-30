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
    TODO: use a celery task(s) to query the database and upload the results to S3
    """
    
    task = tasks.send_task(name="filter", kwargs=data.dict(), queue="imagery")
    return {"task_id": task.id}


@app.post("/predict", status_code=201)
async def predict_images(data: models.InferenceModel):
    """
    TODO: use a celery task(s) to run inference on images
    """
    task = tasks.send_task(name="model", kwargs=data.dict(), queue="inference")
    return {"task_id": task.id}


@app.get("/task/{task_id}", status_code=200)
def get_task_result(task_id: str):
    """
    Use this endpoint to check the status of a task
    """
    result = tasks.AsyncResult(task_id)

    output = models.TaskResult(
        id=task_id,
        status=result.state,
        error=str(result.info) if result.failed() else None,
        result=result.get() if result.state == states.SUCCESS else None,
    )

    return JSONResponse(content=output.dict())
