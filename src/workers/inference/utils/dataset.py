import os
from typing import Any, List

import cv2
from torch.utils.data import Dataset


class ImagesDataset(Dataset):
    def __init__(
        self,
        images: List[str],
        images_folder: str,
        transforms: Any = None,
        device: str = "gpu",
    ):
        self._images = images
        self._images_folder = images_folder
        self._transforms = transforms
        self._device = device

    def __len__(self) -> int:
        return len(self._images)

    def __getitem__(self, idx: int) -> dict:
        image_name = self._images[idx]

        image = cv2.imread(os.path.join(self._images_folder, image_name))

        if self._transforms:
            image = self._transforms(image=image)["image"]

        return image.to(self._device)
