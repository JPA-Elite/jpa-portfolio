from Repositories.VisitRepository import VisitRepository
from Models.SystemInfo import SystemInfo
from config import SortOrder


class VisitService:
    def __init__(self):
        self.repository = VisitRepository()

    def get_paginated_system_info(self, page, per_page, order: SortOrder = SortOrder.DESC):
        documents, total_docs = self.repository.get_paginated_documents(page, per_page, order)
        system_info_list = [SystemInfo(**doc) for doc in documents]
        return system_info_list, total_docs
