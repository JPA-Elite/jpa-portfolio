from Repositories.Interfaces.IMusicRepository import IMusicRepository
from Repositories.BaseRepository import BaseRepository
from config import SortOrder
from constants.db_collections import MongoCollections as mc


class MusicRepository(IMusicRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.MUSIC)  # use "music" collection

    def get_paginated_music_list(self, page: int, per_page: int, order: SortOrder):
        # Mongo sort order by _id
        sort_order = -1 if order == SortOrder.DESC else 1

        # Use MongoDB skip + limit for pagination
        cursor = (
            self.collection.find()
            .sort("_id", sort_order)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )

        data = list(cursor)
        total_data = self.collection.count_documents({})

        return data, total_data
