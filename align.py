# Alineamiento de telegramas y fotos
# Gissio

import os
import sys
from pathlib import Path
from typing import Optional

project_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_dir / "src"))

import cv2

import gdown
import torch
import tqdm
import yaml
from einops import rearrange

from inv3d_model.models import model_factory
from inv3d_util.image import scale_image
from inv3d_util.load import load_image, save_image, save_npz
from inv3d_util.mapping import apply_map_torch
from inv3d_util.misc import to_numpy_image, to_numpy_map
from inv3d_util.path import list_dirs

import boto3

# Configuración

image_width = 1700  # Ancho de la imagen alineada
image_height = 2800  # Alto de la imagen alineada

# Si es False, almacena las imagenes en la carpeta local `output`.
s3_upload = False

aws_access_key_id = "your_access_key_id"
aws_secret_access_key = "your_secret_access_key"
aws_account_region = "your_region"
s3_bucket_name = "your_bucket_name"


# S3


def upload_to_s3(path, s3_filename):
    global aws_access_key_id, aws_secret_access_key, aws_account_region, s3_bucket_name

    with open(path, "rb") as f:
        data = f.read()

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_account_region,
    )

    s3_client.put_object(Body=data, Bucket=s3_bucket_name, Key=s3_filename)


# Alineamiento

cv2.setNumThreads(0)

model_sources = yaml.safe_load((project_dir / "models.yaml").read_text())


def align_images(image_paths, template_path):
    global image_width, image_height, s3_upload

    model_name = "geotr_template_large@inv3d"
    output_shape = (image_height, image_width)

    model_url = model_sources[model_name]
    model_path = Path(
        gdown.cached_download(
            url=model_url, path=project_dir / f"models/{model_name}.ckpt"
        )
    )

    model = model_factory.load_from_checkpoint(model_name.split("@")[0], model_path)
    model.to("cuda")
    model.eval()

    if not isinstance(image_paths, list):
        image_paths = [Path(image_paths)]

    # Plantilla

    template_original = load_image(project_dir / template_path)
    template = scale_image(
        template_original, resolution=model.dataset_options["resolution"]
    )
    template = rearrange(template, "h w c -> () c h w")
    template = template.astype("float32") / 255
    template = torch.from_numpy(template)
    template = template.to("cuda")

    # Modelo

    model_kwargs = {"template": template}

    output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)

    result_paths = []

    for image_path in tqdm.tqdm(image_paths, "Unwarping images"):
        # Pre-procesamiento

        image_original = load_image(image_path)
        image = scale_image(
            image_original, resolution=model.dataset_options["resolution"]
        )
        image = rearrange(image, "h w c -> () c h w")
        image = image.astype("float32") / 255
        image = torch.from_numpy(image)
        image = image.to("cuda")

        model_kwargs["image"] = image

        # Inferencia

        out_bm = model(**model_kwargs).detach().cpu()

        # Unwarping

        image_original = rearrange(image_original, "h w c -> () c h w")
        image_original = image_original.astype("float32") / 255
        image_original = torch.from_numpy(image_original)

        norm_image = apply_map_torch(
            image=image_original, bm=out_bm, resolution=output_shape
        )

        # Exportación

        if s3_upload:
            output_path = output_dir / "image.jpg"
            result_path = image_path.stem + ".jpg"

            save_image(
                output_path,
                to_numpy_image(norm_image),
                override=True,
            )

            upload_to_s3(output_path, result_path)

            result_paths.append(result_path)

        else:
            output_path = output_dir / f"{image_path.stem}.jpg"

            save_image(
                output_path,
                to_numpy_image(norm_image),
                override=True,
            )

            result_paths.append(output_path)

    return result_paths
