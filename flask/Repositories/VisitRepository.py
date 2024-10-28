from Repositories.BaseRepository import BaseRepository


class VisitRepository(BaseRepository):
    def __init__(self):
        super().__init__()  # Call the constructor of the base class

    def get_paginated_documents(self, page, per_page):
        skip = (page - 1) * per_page
        documents = (
            self.collection.find().sort("timestamp", -1).skip(skip).limit(per_page)
        )
        total_docs = self.collection.count_documents({})
        return list(documents), total_docs
