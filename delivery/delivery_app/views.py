import logging

from django.conf import settings
from django.core.cache import cache
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import PackageFilter
from .models import Package, PackageType
from .repositories import PackageRepository
from .serializers import (PackageRegistrationSerializer, PackageSerializer,
                          PackageTypeSerializer)
from .services import DeliveryCostCalculator, SessionManager
from .tasks import register_package_task
from .use_cases import (GetPackageDetailsUseCase, GetPackagesForUserUseCase,
                        PackageRegistrationUseCase)

logger = logging.getLogger(__name__)


class PackageTypeList(generics.ListAPIView):
    """
    API endpoint to retrieve all package types.
    """

    queryset = PackageType.objects.all()
    serializer_class = PackageTypeSerializer
    permission_classes = [AllowAny]
    cache_key = "package_types"

    @extend_schema(
        responses={200: PackageTypeSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = cache.get(self.cache_key)
        if queryset is None:
            queryset = PackageType.objects.all().order_by("id")
            cache.set(self.cache_key, queryset, settings.CACHE_TTL)
        return queryset



class PackageRegistration(APIView):
    """
    API endpoint to register a new package.
    """

    permission_classes = [AllowAny]
    serializer_class = PackageRegistrationSerializer

    @extend_schema(
        request=PackageRegistrationSerializer,
        responses={
            202: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
    )
    def post(self, request):
        serializer = PackageRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            session_manager = SessionManager()
            user_session_key = session_manager.get_user_session(request)

            package_data = serializer.validated_data
            package_data["user_session"] = user_session_key

            register_package_task.delay(package_data)

            return Response(
                {
                    "session_key": user_session_key,
                    "message": "Package registration initiated.",
                },
                status=status.HTTP_202_ACCEPTED,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserPackageList(generics.ListAPIView):
    """
    API endpoint to retrieve a list of packages for the current user.
    Supports filtering by type and delivery_app cost calculation status.
    """

    serializer_class = PackageSerializer
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination
    filterset_class = PackageFilter

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter packages by type (e.g., Electronics, Clothes, Other)",
                required=False,
            ),
            OpenApiParameter(
                name="is_calculated",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter packages by delivery cost calculation status (true/false)",
                required=False,
            ),
        ],
        responses={200: PackageSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        session_manager = SessionManager()
        user_session_key = session_manager.get_user_session(request)

        if not user_session_key:
            return Response([], status=status.HTTP_200_OK)

        use_case = GetPackagesForUserUseCase(package_repository=PackageRepository())
        queryset = use_case.execute(user_session_key, request.query_params.dict())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PackageDetail(generics.RetrieveAPIView):
    """
    API endpoint to retrieve details of a specific package.
    """

    serializer_class = PackageSerializer
    permission_classes = [AllowAny]
    lookup_field = "id"

    @extend_schema(
        responses={200: PackageSerializer},
    )
    def get(self, request, *args, **kwargs):
        session_manager = SessionManager()
        user_session_key = session_manager.get_user_session(request)

        if not user_session_key:
            return Response(status=status.HTTP_404_NOT_FOUND)

        package_id = kwargs["id"]

        use_case = GetPackageDetailsUseCase(package_repository=PackageRepository())
        try:
            package = use_case.execute(user_session_key, package_id)
        except Package.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(package)
        return Response(serializer.data)
