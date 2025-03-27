import cloudinary.uploader
from dotenv import load_dotenv
import cv2
import os
import cloudinary
from datetime import datetime

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
    data, getLocale, search_query, title_key="title", description_key="description"
):
    """Filter data based on the search query."""
    if not search_query:
        return data

    search_query = search_query.strip().lower()

    return [
        item
        for item in data
        if search_query in item[title_key][getLocale].lower()
        or search_query in item[description_key][getLocale].lower()
    ]

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

