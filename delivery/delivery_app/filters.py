from django_filters import rest_framework as filters

from .models import Package, PackageType


class PackageFilter(filters.FilterSet):
    type = filters.ModelChoiceFilter(
        field_name="package_type",
        queryset=PackageType.objects.all(),
        to_field_name="name",
        lookup_expr="iexact",
    )
    delivery_cost_calculated = filters.BooleanFilter(
        field_name="delivery_cost", lookup_expr="isnull", exclude=True
    )

    class Meta:
        model = Package
        fields = ["type", "delivery_cost_calculated"]
