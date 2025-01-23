from abc import ABC, abstractmethod
from decimal import Decimal
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from .models import Package, PackageType


class PackageRepositoryInterface(ABC):
    @abstractmethod
    def create_package(
        self,
        user_session: str,
        name: str,
        weight: float,
        package_type: "PackageType",
        declared_value: Decimal,
        delivery_cost: Decimal,
    ) -> "Package":
        pass

    @abstractmethod
    def get_packages_for_user(self, user_session: str) -> "QuerySet[Package]":
        """
        Возвращает QuerySet с пакетами для указанного пользователя.
        """
        pass

    @abstractmethod
    def get_package_details(self, user_session: str, package_id: int) -> "Package":
        """
        Возвращает объект Package для указанного пользователя и ID пакета.
        """
        pass


class DeliveryCostCalculatorInterface(ABC):
    @abstractmethod
    def calculate(
        self, weight: Decimal, package_type_name: str, declared_value: Decimal
    ) -> Tuple[Decimal, str]:
        pass


class SessionManagerInterface(ABC):
    @abstractmethod
    def get_user_session(self, request) -> str:
        pass


class CacheInvalidatorInterface(ABC):
    @abstractmethod
    def invalidate_package_type_cache(self):
        pass
