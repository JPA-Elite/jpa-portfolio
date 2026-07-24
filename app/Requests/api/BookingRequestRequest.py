from flask import request
from app.Requests.api.BaseRequest import BaseRequest
from app.configurations import SortOrder, SortOrderStr

class BookingRequestRequest(BaseRequest):
    def validated(self):
        route = request.endpoint or ""
        if "delete" in route:
            return self._success_response({})
        return self._validate_list()

    def _validate_list(self):
        page = self._get_int("page", 1)
        per_page = self._get_int("per_page", 10)
        search_query = str(self._get_args("search", "")).strip()
        order = (
            SortOrder.DESC
            if str(self._get_args("order", "desc")).upper() == SortOrderStr.DESC
            else SortOrder.ASC
        )
        return self._success_response({
            "page": page,
            "per_page": per_page,
            "search_query": search_query,
            "order": order,
        })
