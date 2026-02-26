class CompanyRoadmap:
    def __init__(
        self,
        id,
        company_name,
        role_title,
        period,
        employment_type="experience",
        location="",
        role_title_i18n=None,
        definition="",
        definition_i18n=None,
        summary="",
        summary_i18n=None,
        highlights=None,
        highlights_i18n=None,
        cover_image_url=None,
        activities=None,
        accent_color="#2962ff",
        sort_order=0,
        is_active=True,
        _id=None,
    ):
        self._id = _id
        self.id = id
        self.company_name = company_name or ""
        self.role_title = role_title or ""
        self.period = period or ""
        self.employment_type = employment_type or "experience"
        self.location = location or ""
        self.role_title_i18n = role_title_i18n if isinstance(role_title_i18n, dict) else None
        self.definition = definition or ""
        self.definition_i18n = definition_i18n if isinstance(definition_i18n, dict) else None
        self.summary = summary or ""
        self.summary_i18n = summary_i18n if isinstance(summary_i18n, dict) else None
        self.highlights = [str(x).strip() for x in (highlights or []) if str(x).strip()]
        self.highlights_i18n = highlights_i18n if isinstance(highlights_i18n, dict) else None
        self.cover_image_url = cover_image_url
        self.activities = activities or []
        self.accent_color = accent_color or "#2962ff"
        self.sort_order = int(sort_order or 0)
        self.is_active = bool(is_active)

    def to_dict(self):
        data = {
            "id": self.id,
            "company_name": self.company_name,
            "role_title": self.role_title,
            "period": self.period,
            "employment_type": self.employment_type,
            "location": self.location,
            "role_title_i18n": self.role_title_i18n,
            "definition": self.definition,
            "definition_i18n": self.definition_i18n,
            "summary": self.summary,
            "summary_i18n": self.summary_i18n,
            "highlights": self.highlights,
            "highlights_i18n": self.highlights_i18n,
            "cover_image_url": self.cover_image_url,
            "activities": self.activities,
            "accent_color": self.accent_color,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
        }

        if self._id is not None:
            data["_id"] = str(self._id)

        return data

    @staticmethod
    def from_dict(data):
        _id = data.get("_id")
        if isinstance(_id, dict) and "$oid" in _id:
            _id = str(_id["$oid"])

        return CompanyRoadmap(
            _id=_id,
            id=data.get("id"),
            company_name=data.get("company_name", ""),
            role_title=data.get("role_title", ""),
            period=data.get("period", ""),
            employment_type=data.get("employment_type", "experience"),
            location=data.get("location", ""),
            role_title_i18n=data.get("role_title_i18n"),
            definition=data.get("definition", ""),
            definition_i18n=data.get("definition_i18n"),
            summary=data.get("summary", ""),
            summary_i18n=data.get("summary_i18n"),
            highlights=data.get("highlights", []),
            highlights_i18n=data.get("highlights_i18n"),
            cover_image_url=data.get("cover_image_url"),
            activities=data.get("activities", []),
            accent_color=data.get("accent_color", "#2962ff"),
            sort_order=data.get("sort_order", 0),
            is_active=data.get("is_active", True),
        )
