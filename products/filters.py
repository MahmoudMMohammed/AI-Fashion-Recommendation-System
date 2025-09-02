from django_filters import rest_framework as filters
from .models import Product


class ProductFilter(filters.FilterSet):
    """
    Custom filterset for the Product model.
    Enables filtering by category, gender, and a simple search across multiple fields.
    """
    category = filters.CharFilter(field_name='categories__name', lookup_expr='iexact')
    size = filters.CharFilter(field_name='sizes__label', lookup_expr='iexact')

    class Meta:
        model = Product
        fields = {
            'gender': ['iexact'],  # e.g., /?gender=Female
        }
