import os
import pathlib
import sys

import cloudinary
import cloudinary.uploader
import ffmpeg
from dotenv import load_dotenv
from PIL import Image, ImageOps

from app.constants.cloudinary import CloudinaryFolders, CloudinaryResourceType

load_dotenv()


def convert_to_webp(input_path: str, quality: int = 80) -> str:
    if input_path.lower().endswith(".webp"):
        return input_path

    webp_path = os.path.splitext(input_path)[0] + ".webp"

    with Image.open(input_path) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.save(webp_path, "WEBP", quality=quality, method=6)

    return webp_path


def compress_avatar_image(input_path: str, max_dimension: int = 256, max_bytes: int = 2 * 1024 * 1024) -> str:
    webp_path = os.path.splitext(input_path)[0] + ".webp"

    with Image.open(input_path) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        scale = min(1.0, max_dimension / max(img.width, img.height))
        if scale < 1.0:
            new_size = (
                max(1, round(img.width * scale)),
                max(1, round(img.height * scale)),
            )
            img = img.resize(new_size, Image.LANCZOS)

        quality = 85
        img.save(webp_path, "WEBP", quality=quality, method=6)
        while os.path.getsize(webp_path) > max_bytes and quality > 25:
            quality -= 15
            img.save(webp_path, "WEBP", quality=quality, method=6)

    return webp_path


def convert_video(input_path: str, crf: int = 30, bitrate: str = "1M") -> str:
    input_path = str(pathlib.Path(input_path).resolve())

    if sys.platform.startswith("win"):
        output_path = os.path.splitext(input_path)[0] + ".mp4"
        vcodec = "libx264"
        acodec = "aac"
        extra_args = {"preset": "fast", "strict": "experimental"}
    else:
        output_path = os.path.splitext(input_path)[0] + ".webm"
        vcodec = "libvpx-vp9"
        acodec = "libopus"
        extra_args = {"threads": "4"}

    if input_path.lower().endswith(os.path.splitext(output_path)[1]):
        return input_path

    try:
        output_kwargs = {
            "vcodec": vcodec,
            "acodec": acodec,
            "crf": crf,
            **extra_args
        }

        if "libvpx" in vcodec:
            output_kwargs["b:v"] = bitrate

        (
            ffmpeg
            .input(input_path)
            .output(output_path, **output_kwargs)
            .overwrite_output()
            .run(quiet=False)
        )
        return output_path

    except ffmpeg.Error as e:
        print(f"[❌] Failed to convert video: {e}")
        raise e


cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)


def delete_image_from_cloudinary(image_url):
    try:
        parts = image_url.split("/")
        public_id = "/".join(parts[-2:]).split(".")[0]
        result = cloudinary.uploader.destroy(public_id)
        if result.get("result") == "ok":
            return "Image deleted successfully from Cloudinary."
        else:
            return "Failed to delete image from Cloudinary."

    except Exception as e:
        return f"Error deleting image from Cloudinary: {str(e)}"


def delete_file_from_cloudinary(file_url: str, resource_type: CloudinaryResourceType = CloudinaryResourceType.IMAGE):
    try:
        parts = file_url.split("/")
        public_id = "/".join(parts[-2:]).split(".")[0]  # Extract folder/filename without extension
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type.value)
        if result.get("result") == "ok":
            return f"{resource_type.value.capitalize()} deleted successfully from Cloudinary."
        else:
            return f"Failed to delete {resource_type.value} from Cloudinary."

    except Exception as e:
        return f"Error deleting {resource_type.value} from Cloudinary: {str(e)}"


def upload_file_to_cloudinary(file_path: str, resource_type: CloudinaryResourceType = CloudinaryResourceType.RAW, folder: CloudinaryFolders = CloudinaryFolders.DEFAULT):
    try:
        upload_result = cloudinary.uploader.upload(
            file_path,
            folder=folder.value,
            resource_type=resource_type.value
        )
        return upload_result.get("secure_url")
    except Exception as e:
        return f"Error uploading file to Cloudinary: {str(e)}"


def cleanup_uploaded_files(video_url=None, image_url=None, raw_url=None):
    resource_map = {
        video_url: CloudinaryResourceType.AUDIO,
        image_url: CloudinaryResourceType.IMAGE,
        raw_url: CloudinaryResourceType.RAW,
    }

    for url, resource_type in resource_map.items():
        if url:
            delete_file_from_cloudinary(url, resource_type=resource_type)
