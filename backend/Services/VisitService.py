from backend.Repositories.Interfaces.IVisitRepository import IVisitRepository
from backend.Models.SystemInfo import SystemInfo
from backend.configurations import SortOrder
from bson import ObjectId
from backend.constants.messages import DISPLAY_RECORDS_DELETE_MSG
from backend.utils import delete_image_from_cloudinary

class VisitService:
    def __init__(self, repository: IVisitRepository):
        self.repository = repository

    def get_paginated_system_info(self, page, per_page, order: SortOrder = SortOrder.DESC):
        documents, total_docs = self.repository.get_paginated_documents(page, per_page, order)
        system_info_list = [SystemInfo(**doc) for doc in documents]
        return system_info_list, total_docs

    def delete_page_system_info(self, records):
        try:
            for record in records:
                record_id = record.get("_id")
                image_url = record.get("image_capture")

                object_id = ObjectId(record_id)

                self.repository.delete_system_info_by_id(object_id)

                if image_url:
                    delete_image_from_cloudinary(image_url)

            return {"message": DISPLAY_RECORDS_DELETE_MSG, "status": "success"}

        except Exception as e:
            return {"message": str(e), "status": "error"}

    def count_visits(self, where_condition: dict = None):
        return self.repository.count_visits(where_condition)

    def delete_all_visitors(self) -> dict:
        try:
            all_docs = list(self.repository.collection.find({})) if hasattr(self.repository, 'collection') else []
            image_urls = [doc.get("image_capture") for doc in all_docs if doc.get("image_capture")]
            result = self.repository.delete_all_visitors()
            for url in image_urls:
                if url:
                    delete_image_from_cloudinary(url)
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

