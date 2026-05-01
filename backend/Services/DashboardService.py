from backend.Repositories.MusicRepository import MusicRepository
from backend.Repositories.GalleryRepository import GalleryRepository
from backend.Repositories.VideoRepository import VideoRepository
from backend.Repositories.KeyProjectRepository import KeyProjectRepository
from backend.Repositories.CompanyRoadmapRepository import CompanyRoadmapRepository
from backend.Repositories.ActivityLogRepository import ActivityLogRepository
from backend.Services.VisitService import VisitService
from backend.Repositories.VisitRepository import VisitRepository
from flask import current_app
import os
import json
from collections import deque


class DashboardService:
    def __init__(self):
        self.music_repo = MusicRepository()
        self.gallery_repo = GalleryRepository()
        self.video_repo = VideoRepository()
        self.key_project_repo = KeyProjectRepository()
        self.company_roadmap_repo = CompanyRoadmapRepository()
        self.activity_repo = ActivityLogRepository()
        self.visit_service = VisitService(repository=VisitRepository())

    def get_summary(self, recent_limit: int = 20):
        try:
            visit_counts = {"visitor_total_count": 0, "bot_total_count": 0}
            try:
                coll = getattr(self.visit_service, "repository", None)
                coll = getattr(coll, "collection", None)
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
                    for entry in agg:
                        if entry.get("_id") == "bot":
                            visit_counts["bot_total_count"] = int(entry.get("count", 0))
                        else:
                            visit_counts["visitor_total_count"] = int(entry.get("count", 0))
                else:
                    try:
                        visit_counts = self.visit_service.count_visits()
                    except Exception:
                        current_app.logger.debug("VisitService.count_visits unavailable; using zero counts")
                        visit_counts = {"visitor_total_count": 0, "bot_total_count": 0}
            except Exception:
                current_app.logger.debug("Visit aggregation failed, falling back to count_documents")
                try:
                    visit_counts = self.visit_service.count_visits()
                except Exception:
                    current_app.logger.debug("VisitService.count_visits unavailable; using zero counts")
                    visit_counts = {"visitor_total_count": 0, "bot_total_count": 0}

            def _safe_count(coll):
                try:
                    if coll is None:
                        return 0
                    if hasattr(coll, "estimated_document_count"):
                        return int(coll.estimated_document_count())
                    if hasattr(coll, "count_documents"):
                        return int(coll.count_documents({}))
                except Exception:
                    current_app.logger.debug("Collection count unavailable for %s", getattr(coll, "name", "<unknown>"))
                return 0

            music_total = _safe_count(getattr(self.music_repo, "collection", None))
            gallery_total = _safe_count(getattr(self.gallery_repo, "collection", None))
            video_total = _safe_count(getattr(self.video_repo, "collection", None))
            key_project_total = _safe_count(getattr(self.key_project_repo, "collection", None))
            company_roadmap_total = _safe_count(getattr(self.company_roadmap_repo, "collection", None))

            recent = []
            try:
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
        """Delete activity log entries by their _id values."""
        try:
            from bson import ObjectId
            from bson.errors import InvalidId
            object_ids = []
            for rid in record_ids:
                try:
                    object_ids.append(ObjectId(rid))
                except InvalidId:
                    pass
            if not object_ids:
                return {"status": "error", "message": "Invalid record IDs."}
            result = self.activity_repo.collection.delete_many({"_id": {"$in": object_ids}})
            return {"status": "success", "message": f"Deleted {result.deleted_count} record(s).", "deleted_count": result.deleted_count}
        except Exception as e:
            current_app.logger.exception("Failed to delete activity logs")
            return {"status": "error", "message": str(e)}

    def get_recent_activity(self, limit: int = 50):
        """Return recent activity entries, with file fallback."""
        try:
            items = []
            cursor = self.activity_repo.collection.find({}, projection={}).sort([("_id", -1)]).limit(limit)
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
