from backend.Repositories.BaseRepository import BaseRepository
from backend.constants.db_collections import MongoCollections as mc
from bson import ObjectId
from backend.Models.VlogComment import VlogComment

class VlogCommentRepository(BaseRepository):
    def __init__(self):
        super().__init__(mc.VIDEO_COMMENTS)

    def find_comments_by_vlog(self, vlog_id: str):
        return list(self.get_documents({"vlog_id": vlog_id}))

    def find__paginate_comments_by_vlog(self, vlog_id: str, page: int, limit: int):
        skip = (page - 1) * limit
        return list(self.collection.find({"vlog_id": vlog_id}).sort("created_at", -1).skip(skip).limit(limit))

    def count_comments_by_vlog(self, vlog_id: str):
        return self.count({"vlog_id": vlog_id})

    def add_comment(self, comment: VlogComment):
        result = self.insert_document(comment.to_dict())
        return str(result.inserted_id)

    def find_by_id(self, comment_id: str):
        return self.get_document({"_id": ObjectId(comment_id)})

    def update_comment(self, comment):
        return self.update_document_by_id(ObjectId(comment["_id"]), comment)
