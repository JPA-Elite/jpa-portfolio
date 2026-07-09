from app.Repositories.BaseRepository import BaseRepository
from app.Repositories.Interfaces.IVlogCommentRepository import IVlogCommentRepository
from app.constants.db_collections import MongoCollections as mc
from bson import ObjectId
from app.Models.VlogComment import VlogComment

class VlogCommentRepository(IVlogCommentRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.VIDEO_COMMENTS)

    def find_comments_by_vlog(self, vlog_id: str):
        return self.find({"vlog_id": vlog_id})

    def find__paginate_comments_by_vlog(self, vlog_id: str, page: int, limit: int):
        skip = (page - 1) * limit
        return self.find(
            {"vlog_id": vlog_id},
            sort=[("created_at", -1)],
            skip=skip,
            limit=limit,
        )

    def count_comments_by_vlog(self, vlog_id: str):
        return self.count_documents({"vlog_id": vlog_id})

    def count_comments_by_vlog_ids(self, vlog_ids: list[str]):
        if not vlog_ids:
            return {}

        pipeline = [
            {
                "$match": {
                    "vlog_id": {"$in": vlog_ids}
                }
            },
            {
                "$group": {
                    "_id": "$vlog_id",
                    "count": {"$sum": 1}
                }
            }
        ]

        return {
            str(item["_id"]): int(item.get("count", 0))
            for item in self.aggregate(pipeline)
        }

    def add_comment(self, comment: VlogComment):
        result = self.insert_one(comment.to_dict())
        return str(result.inserted_id)

    def find_by_id(self, comment_id: str):
        return self.find_one({"_id": ObjectId(comment_id)})

    def update_comment(self, comment):
        return self.update_one(
            {"_id": ObjectId(comment["_id"])},
            {"$set": comment}
        )
