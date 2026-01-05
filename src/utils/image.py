from pathlib import Path

import numpy as np
from PIL import Image


def images_equal(img1_path: Path, img2_path: Path) -> bool:
    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)

    if img1.size != img2.size or img1.mode != img2.mode:
        return False

    return np.array_equal(np.array(img1), np.array(img2))
