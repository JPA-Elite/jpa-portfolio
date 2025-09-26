from Repositories.Interfaces.IMusicRepository import IMusicRepository
from Models.Music import Music
from config import SortOrder

class MusicService:
    def __init__(self, repository: IMusicRepository):
        self.repository = repository


    def get_paginated_music_list(self, page, per_page, order: SortOrder = SortOrder.DESC):
        data, total_data = self.repository.get_paginated_music_list(page, per_page, order)
        system_info_list = [Music(**music) for music in data]
        return system_info_list, total_data

