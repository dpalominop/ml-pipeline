import os
import json
from typing import Any, Dict

import s3fs
from celery import Celery
from celery.utils.log import get_logger


logger = get_logger(__name__)
inference = Celery(
    "inference", broker=os.getenv("BROKER_URL"), backend=os.getenv("REDIS_URL")
)


@inference.task(bind=True, name="model")
def inference_task(self, **kwargs) -> Dict[str, Any]:
    """
    TODO: run inference here
    """
    logger.info(f"Start executing task {kwargs}")

    # NOTE: example location to store results
    s3_target = self.request.kwargs["s3_target"]
    s3 = s3fs.S3FileSystem(
        client_kwargs={"endpoint_url": f'http://{os.getenv("S3_HOST")}:4566'}
    )

    with s3.open(f"{s3_target}/predictions.json", "w") as dump_f:
        json.dump(results, dump_f)

