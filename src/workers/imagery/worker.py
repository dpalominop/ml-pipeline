import os
import json
import traceback
from typing import Any, Dict, List

import s3fs
from celery import Celery, states
from celery.exceptions import Ignore
from celery.utils.log import get_logger

import albumentations as A
import cv2

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
        
    for metadata in result:
        s3.put(f'{DATA_FOLDER}/{metadata["image_id"]}.jpg', f'{s3_target}/images/{metadata["image_id"]}.jpg')


def run_augmentations(aug_conf: dict, result: List[dict], s3, s3_target: str):
    """
    TODO: use this function to run augmentations
    payload = {
    "gender": "Men", 
    "sub_category": "Shoes", 
    "start_year": YEAR,
    "limit": LIMIT,
    "augmentation_config": {'albumentation': {
        'input_image': {'width': 60, 'height': 80}, 
        'cropping': {'height': {'min': 10, 'max': 70}}, 
        'resize': {'width': 256, 'height': 256}}}
    }
    """
    logger.info(f"Applying augmentation")

    transform = A.Compose([
        A.Crop (x_min=0,
                x_max=aug_conf["input_image"]["width"], 
                y_min=aug_conf["cropping"]["height"]["min"],
                y_max=aug_conf["cropping"]["height"]["max"],
                always_apply=True),
        A.Resize(height=aug_conf["resize"]["height"],
                 width=aug_conf["resize"]["width"], 
                 always_apply=True)
    ])

    for metadata in result:
        image = cv2.imread(f'{DATA_FOLDER}/{metadata["image_id"]}.jpg')
        image_aug = transform(image=image)["image"]

        # NOTE: example location to store the images
        with s3.open(f'{s3_target}/augmentation/{metadata["image_id"]}.jpg', "wb") as aug_f:
            aug_f.write(cv2.imencode('.jpg', image_aug)[1].tobytes())


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

    if kwargs["augmentation_config"] and "albumentation" in kwargs["augmentation_config"]:
        aug_conf = kwargs["augmentation_config"]["albumentation"]
        
        run_augmentations(aug_conf=aug_conf, result=products, s3=s3, s3_target=s3_target)

    return {"s3_target": s3_target}
