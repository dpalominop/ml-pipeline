import os
import json
import traceback
from typing import Any, Dict, List

import s3fs
from celery import Celery, states
from celery.exceptions import Ignore
from celery.utils.log import get_logger

from app.database import filter_products
# from app.augmentation import Transformer
# from app.uploader import Uploader

BUCKET_NAME = os.getenv("BUCKET_NAME", "")
DATA_FOLDER = os.getenv("DATA_FOLDER", "")
S3_HOST = os.getenv("S3_HOST", "")

logger = get_logger(__name__)
imagery = Celery(
    "imagery", broker=os.getenv("BROKER_URL"), backend=os.getenv("REDIS_URL")
)


def upload(result: List[dict], s3, s3_target: str):
    logger.info(f"Uploading metadata and images")

    # NOTE: example location to store the images
    with s3.open(f"{s3_target}/metadata.json", "w") as meta_f:
        json.dump(result, meta_f)
        
    for image in result:
        s3.put(f'{DATA_FOLDER}/{image["image_id"]}.jpg', f'{s3_target}/images/{image["image_id"]}.jpg')


def run_augmentations(aug_conf: dict, result: List[dict], s3, s3_target: str):
    """
    TODO: use this function to run augmentations
    """
    logger.info(f"Applying augmentation")


    # NOTE: example location to store the images
    with s3.open(f"{s3_target}/augmentation/{image_name}", "wb") as aug_f:
        aug_f.write(image_aug)


@imagery.task(bind=True, name="filter")
def filter_task(self, **kwargs) -> Dict[str, Any]:
    """
    TODO: use this queue task to process tasks based on sql query
    """
    # NOTE: example for handling files in S3
    s3_target = f"s3://{BUCKET_NAME}/{self.request.id}"
    s3 = s3fs.S3FileSystem(client_kwargs={"endpoint_url": f"http://{S3_HOST}:4566"})
    
    products = filter_products(data_dict=kwargs)
    
    upload(result=products, s3=s3, s3_target=s3_target)

    return {"s3_target": s3_target}
