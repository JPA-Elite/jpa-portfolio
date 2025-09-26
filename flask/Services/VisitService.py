from Repositories.Interfaces.IVisitRepository import IVisitRepository
from Models.SystemInfo import SystemInfo
from config import SortOrder
from bson import ObjectId
from utils import delete_image_from_cloudinary

class VisitService:
    def __init__(self, repository: IVisitRepository):
        self.repository = repository


    def get_paginated_system_info(self, page, per_page, order: SortOrder = SortOrder.DESC):
        documents, total_docs = self.repository.get_paginated_documents(page, per_page, order)
        system_info_list = [SystemInfo(**doc) for doc in documents]
        return system_info_list, total_docs


    def delete_page_system_info(self, records):
        """
        Deletes only the records displayed on the current page.
        """
        try:
            for record in records:
                record_id = record.get("_id")
                image_url = record.get("image_capture")

                # Convert string `_id` to MongoDB ObjectId
                object_id = ObjectId(record_id)

                # Delete the corresponding database record
                self.repository.delete_system_info_by_id(object_id)

                # Delete image from Cloudinary if it exists
                if image_url:
                    delete_image_from_cloudinary(image_url)

            return {"message": "Displayed records deleted successfully.", "status": "success"}

        except Exception as e:
            return {"message": str(e), "status": "error"}
