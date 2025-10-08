from enum import Enum
import cloudinary.uploader
from dotenv import load_dotenv
import cv2
import os
import cloudinary
from datetime import datetime
import random
from constants.cloudinary import CloudinaryFolders, CloudinaryResourceType

load_dotenv()

# utils.py
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