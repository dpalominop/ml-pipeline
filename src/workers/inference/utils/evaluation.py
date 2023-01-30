import torch
import torch.nn as nn
import albumentations as A
from albumentations.pytorch import ToTensorV2


def set_val_model(model: nn.Module):
    """
    Function to set evaluation mode on a model.

    Args:
        model (nn.Module): Input model for evaluation.
        
    Return:
        nn.Module: model setted for evaluation.
    """
    for k in model.state_dict().keys():
        if 'conv5_pose' in k and 'weight' in k:
            torch.nn.init.xavier_normal_(model.state_dict()[k])
            print('filling xavier {}'.format(k))

    for k in model.state_dict().keys():
        if 'conv5_global' in k and 'weight' in k:
            torch.nn.init.xavier_normal_(model.state_dict()[k])
            print('filling xavier {}'.format(k))
    model.eval()
    
    return model

# Basic transformations for evaluation
val_transform = A.Compose(
        [A.Resize(224, 224), 
         A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)), 
         ToTensorV2()]
    )
