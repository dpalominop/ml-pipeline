import os
import json
from typing import Any, Dict
import tempfile

import s3fs
from celery import Celery
from celery.utils.log import get_logger

import torch
from torch.utils.data import DataLoader

from utils.dataset import ImagesDataset
from utils.evaluation import set_val_model, val_transform

from model.deepfashion import FashionNetVgg16NoBn


logger = get_logger(__name__)
inference = Celery(
    "inference", broker=os.getenv("BROKER_URL"), backend=os.getenv("REDIS_URL")
)

model = set_val_model(model=FashionNetVgg16NoBn())


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

    # Create a temporary directory
    tmpdir = tempfile.mkdtemp()

    # Download the directory
    s3.get(f"{s3_target}/images", tmpdir, recursive=True)

    
    dataset = ImagesDataset(images=os.listdir(tmpdir), 
                            images_folder=tmpdir, 
                            transforms=val_transform,
                            device="cpu")
    dataloader = DataLoader(dataset, batch_size=32, shuffle=False)
    
    results = []
    # run inference on the dataset
    with torch.no_grad():
        for images in dataloader:
            features, logits = model(images)
            
            features = features.tolist()
            logits = logits.tolist()
            
            result = [{"massive_attr": feat, "categories": cat} for feat, cat in zip(features, logits)]
            results.extend(result)

    with s3.open(f"{s3_target}/predictions.json", "w") as dump_f:
        json.dump(results, dump_f)

    return {"s3_target": s3_target}
