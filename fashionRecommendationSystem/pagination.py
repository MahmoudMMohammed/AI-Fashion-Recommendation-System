# app/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param


class GlobalPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_query_param = "page"
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        request = self.request
        base_url = request.build_absolute_uri()

        first_url = replace_query_param(base_url, self.page_query_param, 1)
        last_url = replace_query_param(base_url, self.page_query_param, self.page.paginator.num_pages)

        resp = Response({
            "data": data,
            "count": self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
            "page": self.page.number,
            "page_size": self.get_page_size(request),
            "next": self.get_next_link(),
            "prev": self.get_previous_link(),
            "first": first_url,
            "last": last_url,
        })
        resp._success_message = "OK"
        return resp
