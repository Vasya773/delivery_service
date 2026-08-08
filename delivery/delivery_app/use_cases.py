from decimal import Decimal

from django.shortcuts import get_object_or_404

from .interfaces import (DeliveryCostCalculatorInterface,
                         PackageRepositoryInterface)
from .models import Package, PackageType


class PackageRegistrationUseCase:
    def __init__(
        self,
        package_repository: PackageRepositoryInterface,
        delivery_cost_calculator: DeliveryCostCalculatorInterface,
    ):
        self.package_repository = package_repository
        self.delivery_cost_calculator = delivery_cost_calculator

    def register_package(
        self,
        user_session: str,
        name: str,
        weight: float,
        package_type_name: str,
        declared_value: Decimal,
    ):
        package_type = self._get_package_type(package_type_name)
        delivery_cost, warning = self.delivery_cost_calculator.calculate(
            Decimal(weight), package_type.name, Decimal(declared_value)
        )
        package = self.package_repository.create_package(
            user_session=user_session,
            name=name,
            weight=weight,
            package_type=package_type,
            declared_value=declared_value,
            delivery_cost=delivery_cost,
        )
        return package, warning

    def _get_package_type(self, package_type_name) -> "PackageType":
        return get_object_or_404(PackageType, name=package_type_name)


class GetPackagesForUserUseCase:
    def __init__(self, package_repository: PackageRepositoryInterface):
        self.package_repository = package_repository

    def execute(self, user_session: str, filters: dict = None):
        """
        Возвращает QuerySet с пакетами для указанного пользователя.

        :param user_session: Сессия пользователя.
        :param filters: Словарь с фильтрами (необязательно).
                        Поддерживаемые фильтры:
                        - type: имя типа пакета
                        - is_calculated: True/False для фильтрации по наличию delivery_cost
        :return: QuerySet[Package]
        """
        queryset = self.package_repository.get_packages_for_user(user_session)

        if filters:
            if "type" in filters:
                queryset = queryset.filter(package_type__name__iexact=filters["type"])
            if "is_calculated" in filters:
                if filters["is_calculated"].lower() == "true":
                    queryset = queryset.filter(delivery_cost__isnull=False)
                elif filters["is_calculated"].lower() == "false":
                    queryset = queryset.filter(delivery_cost__isnull=True)

        return queryset.order_by("-id")


class GetPackageDetailsUseCase:
    def __init__(self, package_repository: PackageRepositoryInterface):
        self.package_repository = package_repository

    def execute(self, user_session: str, package_id: int) -> "Package":
        """
        Возвращает объект Package для указанного пользователя и ID пакета.

        :param user_session: Сессия пользователя.
        :param package_id: ID пакета.
        :return: Package
        :raises: Package.DoesNotExist, если пакет не найден
        """
        return self.package_repository.get_package_details(user_session, package_id)
