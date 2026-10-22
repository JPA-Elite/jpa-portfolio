from app.Repositories.Interfaces.IVisitRepository import IVisitRepository
from app.Models.SystemInfo import SystemInfo
from app.configurations import SortOrder
from app.constants.messages import DISPLAY_RECORDS_DELETE_MSG
from app.utils import delete_image_from_cloudinary

class VisitService:
    def __init__(self, repository: IVisitRepository):
        self.repository = repository

    def get_paginated_system_info(self, page, per_page, order: SortOrder = SortOrder.DESC, search: str = ""):
        documents, total_docs = self.repository.get_paginated_documents(page, per_page, order, search)
        system_info_list = [SystemInfo(**doc) for doc in documents]
        return system_info_list, total_docs

    def delete_page_system_info(self, records):
        try:
            for record in records:
                record_id = record.get("_id")
                image_url = record.get("image_capture")

                self.repository.delete_system_info_by_id(str(record_id))

                if image_url:
                    delete_image_from_cloudinary(image_url)

            return {"message": DISPLAY_RECORDS_DELETE_MSG, "status": "success"}

        except Exception as e:
            return {"message": str(e), "status": "error"}

    def count_visits(self, where_condition: dict = None):
        return self.repository.count_visits(where_condition)

    def delete_all_visitors(self):
        try:
            image_urls = self.repository.find_all_image_captures()
            result = self.repository.delete_all_visitors()

            if not isinstance(result, dict):
                cleared = bool(result)
                result = {
                    "status": "success" if cleared else "error",
                    "message": "All visitor records cleared." if cleared else "Failed to clear visitor records.",
                }

            if result.get("status") == "success":
                for url in image_urls:
                    if url:
                        delete_image_from_cloudinary(url)

            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

