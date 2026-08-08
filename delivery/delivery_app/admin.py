from django.contrib import admin

from .models import Package, PackageType


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_session",
        "name",
        "weight",
        "package_type",
        "declared_value",
        "delivery_cost",
    )
    list_filter = ("package_type", "delivery_cost")
    search_fields = ("name", "user_session")


@admin.register(PackageType)
class PackageTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
