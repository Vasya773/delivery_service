from decimal import Decimal

from .interfaces import PackageRepositoryInterface
from .models import Package, PackageType


class PackageRepository(PackageRepositoryInterface):
    def create_package(
        self,
        user_session: str,
        name: str,
        weight: float,
        package_type: "PackageType",
        declared_value: Decimal,
        delivery_cost: Decimal,
    ) -> "Package":
        return Package.objects.create(
            user_session=user_session,
            name=name,
            weight=weight,
            package_type=package_type,
            declared_value=declared_value,
            delivery_cost=delivery_cost,
        )

    def get_packages_for_user(self, user_session: str):
        """
        Возвращает QuerySet с пакетами для указанного пользователя.
        """
        return Package.objects.filter(user_session=user_session).select_related(
            "package_type"
        )

    def get_package_details(self, user_session: str, package_id: int) -> "Package":
        """
        Возвращает объект Package для указанного пользователя и ID пакета.
        """
        return Package.objects.get(user_session=user_session, id=package_id)
