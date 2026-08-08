from django.urls import path

from .views import (PackageDetail, PackageRegistration, PackageTypeList,
                    UserPackageList)

urlpatterns = [
    path("register/", PackageRegistration.as_view(), name="package-registration"),
    path("types/", PackageTypeList.as_view(), name="package-types"),
    path("my-packages/", UserPackageList.as_view(), name="user-packages"),
    path("package/<int:id>/", PackageDetail.as_view(), name="package-detail"),
]
