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

    # Convert search query to lowercase
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

def capture_image(save_dir="captured_images"):
    # Create the directory to save images if it doesn't exist (optional, as we're uploading to Cloudinary)
    os.makedirs(save_dir, exist_ok=True)
    
    # Open the webcam
    cap = cv2.VideoCapture(0)

    # Check if the webcam is opened correctly
    if not cap.isOpened():
        return None, "Error: Could not access the camera."

    # Capture a frame
    ret, frame = cap.read()
    if ret:
        # Save the image temporarily to upload to Cloudinary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(save_dir, f"capture_{timestamp}.jpg")
        cv2.imwrite(filename, frame)  # Save image locally for temporary upload

        try:
            upload_result = cloudinary.uploader.upload(
                filename,
                folder="capture_images"  # Specify the folder name on Cloudinary
            )
            cloudinary_url = upload_result['secure_url']  # Get the URL of the uploaded image
            os.remove(filename)  # Remove the temporary file after upload

            return cloudinary_url, None

        except Exception as e:
            os.remove(filename)  # Ensure the temporary file is deleted if an error occurs
            return None, f"Error uploading image to Cloudinary: {str(e)}"

    cap.release()
    return None, "Error: Failed to capture image."
