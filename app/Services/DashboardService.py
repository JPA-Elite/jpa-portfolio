from app.Repositories.MusicRepository import MusicRepository
from app.Repositories.GalleryRepository import GalleryRepository
from app.Repositories.VideoRepository import VideoRepository
from app.Repositories.KeyProjectRepository import KeyProjectRepository
from app.Repositories.CompanyRoadmapRepository import CompanyRoadmapRepository
from app.Repositories.ActivityLogRepository import ActivityLogRepository
from app.Repositories.Interfaces.IMusicRepository import IMusicRepository
from app.Repositories.Interfaces.IGalleryRepository import IGalleryRepository
from app.Repositories.Interfaces.IVideoRepository import IVideoRepository
from app.Repositories.Interfaces.IKeyProjectRepository import IKeyProjectRepository
from app.Repositories.Interfaces.ICompanyRoadmapRepository import ICompanyRoadmapRepository
from app.Repositories.Interfaces.IActivityLogRepository import IActivityLogRepository
from app.Services.VisitService import VisitService
from app.Repositories.VisitRepository import VisitRepository
from app.configurations import SortOrder
from flask import current_app
import os
import json
import re
from collections import deque

class DashboardService:
    def __init__(
        self,
        music_repo: IMusicRepository = None,
        gallery_repo: IGalleryRepository = None,
        video_repo: IVideoRepository = None,
        key_project_repo: IKeyProjectRepository = None,
        company_roadmap_repo: ICompanyRoadmapRepository = None,
        activity_repo: IActivityLogRepository = None,
        visit_service: VisitService = None,
    ):
        self._music_repo = music_repo
        self._gallery_repo = gallery_repo
        self._video_repo = video_repo
        self._key_project_repo = key_project_repo
        self._company_roadmap_repo = company_roadmap_repo
        self._activity_repo = activity_repo
        self._visit_service = visit_service

    @property
    def music_repo(self):
        if self._music_repo is None:
            self._music_repo = MusicRepository()
        return self._music_repo

    @music_repo.setter
    def music_repo(self, value):
        self._music_repo = value

    @property
    def gallery_repo(self):
        if self._gallery_repo is None:
            self._gallery_repo = GalleryRepository()
        return self._gallery_repo

    @gallery_repo.setter
    def gallery_repo(self, value):
        self._gallery_repo = value

    @property
    def video_repo(self):
        if self._video_repo is None:
            self._video_repo = VideoRepository()
        return self._video_repo

    @video_repo.setter
    def video_repo(self, value):
        self._video_repo = value

    @property
    def key_project_repo(self):
        if self._key_project_repo is None:
            self._key_project_repo = KeyProjectRepository()
        return self._key_project_repo

    @key_project_repo.setter
    def key_project_repo(self, value):
        self._key_project_repo = value

    @property
    def company_roadmap_repo(self):
        if self._company_roadmap_repo is None:
            self._company_roadmap_repo = CompanyRoadmapRepository()
        return self._company_roadmap_repo

    @company_roadmap_repo.setter
    def company_roadmap_repo(self, value):
        self._company_roadmap_repo = value

    @property
    def activity_repo(self):
        if self._activity_repo is None:
            self._activity_repo = ActivityLogRepository()
        return self._activity_repo

    @activity_repo.setter
    def activity_repo(self, value):
        self._activity_repo = value

    @property
    def visit_service(self):
        if self._visit_service is None:
            self._visit_service = VisitService(repository=VisitRepository())
        return self._visit_service

    @visit_service.setter
    def visit_service(self, value):
        self._visit_service = value

    def _safe_repo_count(self, repo):
        count_fn = getattr(repo, "count_documents", None)
        if callable(count_fn):
            try:
                return int(count_fn({}))
            except Exception:
                pass
        try:
            coll = getattr(repo, "collection", None)
            if coll is None:
                return 0
            if hasattr(coll, "estimated_document_count"):
                return int(coll.estimated_document_count())
            if hasattr(coll, "count_documents"):
                return int(coll.count_documents({}))
        except Exception:
            current_app.logger.debug("Collection count unavailable for %s", getattr(coll, "name", "<unknown>"))
        return 0

    def _visit_type_counts(self):
        visit_repo = getattr(self.visit_service, "repository", None)
        aggregate_fn = getattr(visit_repo, "get_visit_type_counts", None)
        if callable(aggregate_fn):
            try:
                return aggregate_fn()
            except Exception:
                pass
        try:
            coll = getattr(visit_repo, "collection", None)
            if coll is not None and hasattr(coll, "aggregate"):
                pipeline = [
                    {
                        "$group": {
                            "_id": {
                                "$cond": [
                                    {"$eq": [{"$toLower": "$os"}, "other"]},
                                    "bot",
                                    "visitor",
                                ]
                            },
                            "count": {"$sum": 1},
                        }
                    }
                ]
                agg = list(coll.aggregate(pipeline))
                counts = {"visitor_total_count": 0, "bot_total_count": 0}
                for entry in agg:
                    if entry.get("_id") == "bot":
                        counts["bot_total_count"] = int(entry.get("count", 0))
                    else:
                        counts["visitor_total_count"] = int(entry.get("count", 0))
                return counts
        except Exception:
            current_app.logger.debug("Visit aggregation failed, falling back to count_visits")
        try:
            return self.visit_service.count_visits()
        except Exception:
            current_app.logger.debug("VisitService.count_visits unavailable; using zero counts")
            return {"visitor_total_count": 0, "bot_total_count": 0}

    def get_summary(self, recent_limit: int = 0):
        try:
            try:
                recent_limit = int(recent_limit)
            except (TypeError, ValueError):
                recent_limit = 0
            recent_limit = max(0, min(recent_limit, 100))
            visit_counts = self._visit_type_counts()

            music_total = self._safe_repo_count(self.music_repo)
            gallery_total = self._safe_repo_count(self.gallery_repo)
            video_total = self._safe_repo_count(self.video_repo)
            key_project_total = self._safe_repo_count(self.key_project_repo)
            company_roadmap_total = self._safe_repo_count(self.company_roadmap_repo)

            recent = []
            try:
                if recent_limit > 0:
                    find_recent_fn = getattr(self.activity_repo, "find_recent", None)
                    if callable(find_recent_fn):
                        try:
                            recent = find_recent_fn(recent_limit)
                        except TypeError:
                            recent = find_recent_fn()
                    else:
                        coll = getattr(self.activity_repo, "collection", None)
                        if coll is not None and hasattr(coll, "find"):
                            proj = {"method": 1, "path": 1, "status_code": 1, "user_id": 1, "user": 1, "timestamp": 1, "body": 1}
                            cursor = coll.find({}, projection=proj).sort([("_id", -1)]).limit(recent_limit)
                            for doc in cursor:
                                doc["_id"] = str(doc.get("_id"))
                                recent.append(doc)
                        else:
                            current_app.logger.debug("Activity collection not available; skipping DB read for recent activity")
            except Exception:
                current_app.logger.exception("Failed to read activity_logs collection in DashboardService")

            return {
                "visitor_total_count": visit_counts.get("visitor_total_count", 0),
                "bot_total_count": visit_counts.get("bot_total_count", 0),
                "total_count": visit_counts.get("visitor_total_count", 0) + visit_counts.get("bot_total_count", 0),
                "total_music": int(music_total),
                "total_gallery": int(gallery_total),
                "total_video": int(video_total),
                "total_projects": int(key_project_total),
                "total_roadmaps": int(company_roadmap_total),
                "recent_activity": recent,
            }
        except Exception:
            current_app.logger.exception("Failed to build dashboard summary in DashboardService")
            raise

    def delete_activity_logs(self, record_ids: list) -> dict:
        try:
            delete_fn = getattr(self.activity_repo, "delete_by_ids", None)
            if callable(delete_fn):
                result = delete_fn(list(record_ids or []))
                if isinstance(result, dict) and result.get("status") == "success":
                    deleted = int(result.get("deleted_count", 0))
                    if record_ids and not deleted:
                        return {"status": "error", "message": "Activity record not found."}
                    return {"status": "success", "message": f"Deleted {deleted} record(s).", "deleted_count": deleted}
                return {"status": "error", "message": result.get("message", "Invalid record IDs.") if isinstance(result, dict) else "Invalid record IDs."}
            coll = getattr(self.activity_repo, "collection", None)
            if coll is None:
                return {"status": "error", "message": "Activity repository unavailable."}
            from bson import ObjectId
            from bson.errors import InvalidId
            if not record_ids:
                result = coll.delete_many({})
                return {"status": "success", "message": f"Deleted {result.deleted_count} record(s).", "deleted_count": result.deleted_count}
            object_ids = []
            for rid in record_ids:
                try:
                    object_ids.append(ObjectId(rid))
                except InvalidId:
                    pass
            if not object_ids:
                return {"status": "error", "message": "Invalid record IDs."}
            result = coll.delete_many({"_id": {"$in": object_ids}})
            if not result.deleted_count:
                return {"status": "error", "message": "Activity record not found."}
            return {"status": "success", "message": f"Deleted {result.deleted_count} record(s).", "deleted_count": result.deleted_count}
        except Exception as e:
            current_app.logger.exception("Failed to delete activity logs")
            return {"status": "error", "message": str(e)}

    def get_paginated_recent_activity(self, page: int = 1, per_page: int = 10, order: SortOrder = SortOrder.DESC, search: str = ""):
        paginated_fn = getattr(self.activity_repo, "get_paginated", None)
        if callable(paginated_fn):
            try:
                return paginated_fn(page, per_page, order, search)
            except Exception:
                current_app.logger.exception("Failed to read paginated activity_logs from DB in DashboardService")
                return [], 0
        try:
            try:
                page = max(1, int(page))
            except (TypeError, ValueError):
                page = 1
            try:
                per_page = int(per_page)
            except (TypeError, ValueError):
                per_page = 10
            per_page = max(1, min(per_page, 100))
            collection = getattr(self.activity_repo, "collection", None)
            if collection is None or not hasattr(collection, "find"):
                return [], 0
            query = {}
            needle = str(search or "").strip()
            if needle:
                pattern = re.escape(needle)
                query = {
                    "$or": [
                        {"method": {"$regex": pattern, "$options": "i"}},
                        {"path": {"$regex": pattern, "$options": "i"}},
                        {"user_id": {"$regex": pattern, "$options": "i"}},
                        {"remote_addr": {"$regex": pattern, "$options": "i"}},
                        {"timestamp": {"$regex": pattern, "$options": "i"}},
                    ]
                }

            total = int(collection.count_documents(query))
            if total == 0:
                return [], 0
            sort_direction = -1 if order == SortOrder.DESC else 1
            skip = (page - 1) * per_page
            projection = {"method": 1, "path": 1, "status_code": 1, "user_id": 1, "user": 1, "timestamp": 1, "body": 1, "remote_addr": 1}
            cursor = (
                collection.find(query, projection=projection)
                .sort([("_id", sort_direction)])
                .skip(skip)
                .limit(per_page)
            )

            items = []
            for doc in cursor:
                doc["_id"] = str(doc.get("_id"))
                items.append(doc)
            return items, total
        except Exception:
            current_app.logger.exception("Failed to read paginated activity_logs from DB in DashboardService")
            return [], 0

    def get_recent_activity(self, limit: int = 50):
        find_recent_fn = getattr(self.activity_repo, "find_recent", None)
        if callable(find_recent_fn):
            try:
                return find_recent_fn(limit)
            except Exception:
                pass
        try:
            items = []
            coll = getattr(self.activity_repo, "collection", None)
            if coll is None:
                raise AttributeError("activity collection unavailable")
            cursor = coll.find({}, projection={}).sort([("_id", -1)]).limit(limit)
            for doc in cursor:
                doc["_id"] = str(doc.get("_id"))
                items.append(doc)
            return items
        except Exception:
            current_app.logger.exception("Failed to read activity_logs from DB in DashboardService, falling back to file")
            try:
                logs_dir = os.path.join(os.path.dirname(__file__), "..")
            except Exception:
                logs_dir = None
            logfile = None
            if logs_dir:
                candidate = os.path.join(os.path.dirname(__file__), "..", "logs", "recent_activity.jsonl")
                logfile = os.path.abspath(candidate)
            if not logfile or not os.path.exists(logfile):
                logfile = os.path.join(os.path.dirname(__file__), "..", "logs", "recent_activity.jsonl")

                try:
                    dq = deque(maxlen=limit)
                    if not logfile or not os.path.exists(logfile):
                        current_app.logger.debug("Recent activity logfile not found: %s", logfile)
                        return []
                    with open(logfile, "r", encoding="utf-8") as fh:
                        for line in fh:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                dq.append(json.loads(line))
                            except Exception:
                                continue
                    items = list(dq)[-limit:][::-1]
                    return items
                except Exception:
                    current_app.logger.exception("Failed to read recent activity log file in DashboardService")
                    return []
