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

BUCKET_NAME = os.getenv("BUCKET_NAME", "")
DATA_FOLDER = os.getenv("DATA_FOLDER", "")
S3_HOST = os.getenv("S3_HOST", "")

logger = get_logger(__name__)
imagery = Celery(
    "imagery", broker=os.getenv("BROKER_URL"), backend=os.getenv("REDIS_URL")
)


def upload(result: List[dict], s3, s3_target: str):
    """
    Uploading metadata and images to s3 path.
    Args:
        results (List[dict]): Metadata of list of filtered products.
        s3: S3 handler.
        s3_target: s3 path.
    """
    logger.info(f"Uploading metadata and images")

    # saving metadata on s3 path
    with s3.open(f"{s3_target}/metadata.json", "w") as meta_f:
        json.dump(result, meta_f)
        
    # saving images on s3 path
    for metadata in result:
        s3.put(f'{DATA_FOLDER}/{metadata["image_id"]}.jpg', f'{s3_target}/images/{metadata["image_id"]}.jpg')


def run_augmentations(aug_conf: dict, result: List[dict], s3, s3_target: str):
    """
    Run data augmentation on filtered products.
    Args:
        aug_conf (dict): Parameters to run augmentation.
        result (List[dict]): Metadata of list of filtered products.
        s3: S3 handler.
        s3_target: s3 path.
    """
    logger.info(f"Applying augmentation")

    # defining augmentation process
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
        # loading image in memory
        image = cv2.imread(f'{DATA_FOLDER}/{metadata["image_id"]}.jpg')
        # executing transformation/augmentation
        image_aug = transform(image=image)["image"]

        # saving new image to s3 path
        with s3.open(f'{s3_target}/augmentation/{metadata["image_id"]}.jpg', "wb") as aug_f:
            aug_f.write(cv2.imencode('.jpg', image_aug)[1].tobytes())


@imagery.task(bind=True, name="filter")
def filter_task(self, **kwargs) -> Dict[str, Any]:
    """
    Run filtering task based on input parameters.
    Args:
        kwargs: Input parameter (e.g.: filter params, augmentation_config, etc)
    Return:
        dict: Dictionary including s3_target.
    """
    # defining s3 path and handler
    s3_target = f"s3://{BUCKET_NAME}/{self.request.id}"
    s3 = s3fs.S3FileSystem(client_kwargs={"endpoint_url": f"http://{S3_HOST}:4566"})
    # applying filter to products
    products = filter_products(data_dict=kwargs)

    # uploading filtered product to s3
    upload(result=products, s3=s3, s3_target=s3_target)

    #  checking if augmentation config exists
    if kwargs["augmentation_config"] and "albumentation" in kwargs["augmentation_config"]:
        # getting augmentation config
        aug_conf = kwargs["augmentation_config"]["albumentation"]
        #  running augmentation
        run_augmentations(aug_conf=aug_conf, result=products, s3=s3, s3_target=s3_target)

    return {"s3_target": s3_target}
