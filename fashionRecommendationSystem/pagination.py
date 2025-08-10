# app/pagination.py
from rest_framework.pagination import PageNumberPagination


class GlobalPageNumberPagination(PageNumberPagination):
    page_size = 20  # default
    page_query_param = "page"  # ?page=2
    page_size_query_param = "page_size"  # ?page_size=50
    max_page_size = 100  # safety cap
