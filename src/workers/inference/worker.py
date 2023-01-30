import os
import json
from typing import Any, Dict
import tempfile

import s3fs
from celery import Celery
from celery.utils.log import get_logger

import torch
from torch.utils.data import DataLoader

import albumentations as A
from albumentations.pytorch import ToTensorV2

from utils.dataset import ImagesDataset
from model.deepfashion import FashionNetVgg16NoBn


logger = get_logger(__name__)
inference = Celery(
    "inference", broker=os.getenv("BROKER_URL"), backend=os.getenv("REDIS_URL")
)

model = FashionNetVgg16NoBn()

# pose network needs to be trained from scratch? i guess?
for k in model.state_dict().keys():
    if 'conv5_pose' in k and 'weight' in k:
        torch.nn.init.xavier_normal_(model.state_dict()[k])
        print('filling xavier {}'.format(k))

for k in model.state_dict().keys():
    if 'conv5_global' in k and 'weight' in k:
        torch.nn.init.xavier_normal_(model.state_dict()[k])
        print('filling xavier {}'.format(k))
model.eval()

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

    val_transform = A.Compose(
        [A.Resize(224, 224), A.Normalize(mean=(0.485, 0.456, 0.406), 
        std=(0.229, 0.224, 0.225)), ToTensorV2()]
    )
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
