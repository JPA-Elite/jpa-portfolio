from abc import ABC, abstractmethod

from configurations import SortOrder
from Models.CompanyRoadmap import CompanyRoadmap


class ICompanyRoadmapRepository(ABC):
    @abstractmethod
    def get_company_roadmap_by_id(self, roadmap_id: str):
        pass

    @abstractmethod
    def get_paginated_company_roadmaps(self, page: int, per_page: int, order: SortOrder):
        pass

    @abstractmethod
    def get_active_company_roadmaps(self):
        pass

    @abstractmethod
    def count_company_roadmaps(self):
        pass

    @abstractmethod
    def add_company_roadmap(self, roadmap: CompanyRoadmap):
        pass

    @abstractmethod
    def add_many_company_roadmaps(self, roadmaps: list[CompanyRoadmap]):
        pass

    @abstractmethod
    def update_company_roadmap(self, roadmap_id: str, roadmap: CompanyRoadmap):
        pass

    @abstractmethod
    def delete_company_roadmap(self, roadmap_id: str):
        pass
