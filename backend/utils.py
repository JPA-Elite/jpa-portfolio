import cloudinary.uploader
from dotenv import load_dotenv
import cv2
import os
import cloudinary
from datetime import datetime
import random
from backend.constants.cloudinary import CloudinaryFolders, CloudinaryResourceType
from werkzeug.urls import url_encode
from backend.extensions import cache
from PIL import Image, ImageOps
import ffmpeg
import sys
import pathlib
import requests

load_dotenv()

HCAPTCHA_VERIFY_URL = "https://hcaptcha.com/siteverify"
HCAPTCHA_SECRET = os.getenv("HCAPTCHA_SECRET_KEY")

def paginate_data(data, page, items_per_page):
    total_items = len(data)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    end = start + items_per_page
    paginated_data = data[start:end]

    return paginated_data, total_pages

def filter_data(
    data, getLocale, search_query, tags=None,
    title_key="title", description_key="description", tags_key="tags", id_key="id"
):
    """Filter data based on the search query and tags."""
    search_query = search_query.strip().lower() if search_query else ''
    tags = set(tags.split('.')) if tags else set()

    filtered_data = []
    seen_ids = set()

    if tags:
        # Step 1: Collect all items that match any of the tags
        for item in data:
            item_tags = set(item.get(tags_key, []))
            if item_tags & tags:  # Check if any tag matches
                item_id = item.get(id_key)
                if item_id not in seen_ids:
                    filtered_data.append(item)
                    seen_ids.add(item_id)

        # Step 2: If search query exists, further filter the result
        if search_query:
            filtered_data = [
                item for item in filtered_data
                if search_query in item[title_key].get(getLocale, "").lower()
                or search_query in item[description_key].get(getLocale, "").lower()
            ]

        return filtered_data

    # If no tags were provided, just use the search query to filter the full dataset
    if search_query:
        return [
            item for item in data
            if search_query in item[title_key].get(getLocale, "").lower()
            or search_query in item[description_key].get(getLocale, "").lower()
        ]

    return data

def get_random_tags(data, tags_length=10):
    unique_tags = set()

    if not data:
        return []

    # Case 1: data contains dicts with 'tags'
    if isinstance(data[0], dict):
        for item in data:
            if "tags" in item and isinstance(item["tags"], list):
                unique_tags.update(item["tags"])
    # Case 2: data is already a list of tag strings
    elif isinstance(data[0], str):
        unique_tags.update(data)

    # Convert to list and shuffle randomly
    unique_tags = list(unique_tags)
    random.shuffle(unique_tags)

    # Return limited number of random tags
    return unique_tags[:tags_length]

def get_cache_data(func_name, args=None, timeout=None, default=None):
    cache_key = f"{func_name}:{url_encode(args)}" if args else f"{func_name}:all"
    cached_data = cache.get(cache_key)

    if cached_data is None and default is not None:
        cache.set(cache_key, default, timeout=timeout)
        cached_data = default

    return cached_data, cache_key


def clear_cache_by_prefix(prefix: str):
    for key in list(cache.cache._cache.keys()):
        if key.startswith(prefix):
            print("Deleting cache key:", key)
            cache.delete(key)


def num_to_alpha_lower(num_str: str) -> str:
    """Convert numeric string to corresponding lowercase alphabet letters (1 → a, 2 → b, ...)."""
    result = ""
    for char in num_str:
        if char.isdigit():
            n = int(char)
            if n == 0:
                result += "z"  # optional: treat 0 as 'z'
            else:
                result += chr(96 + n)  # 1 -> a, 2 -> b, ..., 9 -> i
        else:
            result += char
    return result


def convert_to_webp(input_path: str, quality: int = 80) -> str:
    if input_path.lower().endswith(".webp"):
        return input_path

    webp_path = os.path.splitext(input_path)[0] + ".webp"

    with Image.open(input_path) as img:
        # Auto-rotate image based on EXIF orientation
        img = ImageOps.exif_transpose(img)

        # Convert transparent or palette images to RGB
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Save as WebP
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
        # Only set video_bitrate for VP9
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


# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# Capture an image from the webcam and upload it to Cloudinary
def capture_image(save_dir="captured_images"):
    # Create the directory to save images if it doesn't exist (optional, as we're uploading to Cloudinary)
    os.makedirs(save_dir, exist_ok=True)

    # Open the webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return None, "Error: Could not access the camera."

    ret, frame = cap.read()
    if ret:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(save_dir, f"capture_{timestamp}.jpg")
        cv2.imwrite(filename, frame)
        try:
            upload_result = cloudinary.uploader.upload(
                filename,
                folder="capture_images"
            )
            cloudinary_url = upload_result['secure_url']
            os.remove(filename)  # Remove the temporary file after upload

            return cloudinary_url, None

        except Exception as e:
            os.remove(filename)
            return None, f"Error uploading image to Cloudinary: {str(e)}"

    cap.release()
    return None, "Error: Failed to capture image."


# Delete an image from Cloudinary
def delete_image_from_cloudinary(image_url):
    """
    Deletes an image from Cloudinary using its public ID.

    :param image_url: The full Cloudinary URL of the image to be deleted.
    :return: Success or error message.
    """
    try:
        # Extract public ID from URL (Cloudinary stores images with the folder name)
        parts = image_url.split("/")
        public_id = "/".join(parts[-2:]).split(".")[0]  # Extract folder/filename without extension

        # Delete image from Cloudinary
        result = cloudinary.uploader.destroy(public_id)

        if result.get("result") == "ok":
            return "Image deleted successfully from Cloudinary."
        else:
            return "Failed to delete image from Cloudinary."

    except Exception as e:
        return f"Error deleting image from Cloudinary: {str(e)}"

def delete_file_from_cloudinary(file_url: str, resource_type: CloudinaryResourceType = CloudinaryResourceType.IMAGE):
    """
    Deletes a file from Cloudinary using its public ID.

    :param file_url: The full Cloudinary URL of the file to be deleted.
    :param resource_type: CloudinaryResourceType enum (IMAGE, VIDEO, RAW).
    :return: Success or error message.
    """
    try:
        # Extract public ID from URL
        parts = file_url.split("/")
        public_id = "/".join(parts[-2:]).split(".")[0]  # Extract folder/filename without extension

        # Delete file from Cloudinary
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type.value)

        if result.get("result") == "ok":
            return f"{resource_type.value.capitalize()} deleted successfully from Cloudinary."
        else:
            return f"Failed to delete {resource_type.value} from Cloudinary."

    except Exception as e:
        return f"Error deleting {resource_type.value} from Cloudinary: {str(e)}"

def upload_file_to_cloudinary(file_path: str, resource_type: CloudinaryResourceType = CloudinaryResourceType.RAW, folder: CloudinaryFolders = CloudinaryFolders.DEFAULT):
    """
    Upload a file to Cloudinary.

    :param file_path: Path to the file to be uploaded.
    :param folder: Cloudinary folder to store the file.
    :param resource_type: CloudinaryResourceType enum (IMAGE, VIDEO, RAW).
    :return: Uploaded file URL or error message.
    """
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

# HCAPTCHA CONFIGS
def verify_hcaptcha(token: str, remote_ip: str = None):
    if not token:
        return False, {"error": "missing-token"}

    data = {
        "secret": HCAPTCHA_SECRET,
        "response": token,
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        r = requests.post(HCAPTCHA_VERIFY_URL, data=data, timeout=5)
        r.raise_for_status()
        res = r.json()
        return bool(res.get("success")), res
    except requests.RequestException as e:
        return False, {"error": "request-failed", "exception": str(e)}