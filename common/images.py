import torch
from PIL import Image
import numpy as np


def tensor2pil(image):
    """
    Convert torch tensor to PIL Image.
    Args:
        image: Torch tensor (H, W, C) or (B, H, W, C)
    Returns:
        PIL Image (RGB or RGBA)
    """
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))


def pil2tensor(image):
    """
    Convert PIL Image to torch tensor.
    Args:
        image: PIL Image
    Returns:
        Torch tensor (B, H, W, C) in range [0, 1]
    """
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)