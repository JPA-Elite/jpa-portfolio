from app.Repositories.BaseRepository import BaseRepository
from app.Repositories.Interfaces.IGalleryCommentRepository import IGalleryCommentRepository
from app.constants.db_collections import MongoCollections as mc
from bson import ObjectId
from app.Models.GalleryComment import GalleryComment

class GalleryCommentRepository(IGalleryCommentRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.GALLERY_COMMENTS)

    def find_comments_by_gallery(self, gallery_id: str):
        return self.find({"gallery_id": gallery_id})

    def find__paginate_comments_by_gallery(self, gallery_id: str, page: int, limit: int):
        skip = (page - 1) * limit
        return self.find(
            {"gallery_id": gallery_id},
            sort=[("created_at", -1)],
            skip=skip,
            limit=limit,
        )

    def count_comments_by_gallery(self, gallery_id: str):
        return self.count_documents({"gallery_id": gallery_id})

    def add_comment(self, comment: GalleryComment):
        result = self.insert_one(comment.to_dict())
        return str(result.inserted_id)

    def find_by_id(self, comment_id: str):
        return self.find_one({"_id": ObjectId(comment_id)})

    def update_comment(self, comment):
        return self.update_one(
            {"_id": ObjectId(comment["_id"])},
            {"$set": comment},
        )
