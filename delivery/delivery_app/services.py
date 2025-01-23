from decimal import Decimal
from typing import Tuple

from django.core.cache import cache

from .interfaces import (CacheInvalidatorInterface,
                         DeliveryCostCalculatorInterface,
                         SessionManagerInterface)


class DeliveryCostCalculator(DeliveryCostCalculatorInterface):
    def calculate(
        self, weight: Decimal, package_type_name: str, declared_value: Decimal
    ) -> Tuple[Decimal, str]:
        """
        Calculates the delivery cost based on weight, type, and declared value.
        Returns a tuple: (delivery_cost, warning_message or None).
        """
        base_cost = Decimal("10")
        weight_factor = Decimal("2")
        type_factor = Decimal("1")
        value_factor = Decimal("0.01")
        warning = None

        if package_type_name == "Electronics":
            type_factor = Decimal("2.5")
        elif package_type_name == "Clothes":
            type_factor = Decimal("1.5")
        else:
            warning = (
                f"Unknown package type: {package_type_name}. Using default type factor."
            )

        delivery_cost = (
            base_cost + (weight * weight_factor) + (declared_value * value_factor)
        )
        delivery_cost *= type_factor

        return delivery_cost, warning


class SessionManager(SessionManagerInterface):
    def get_user_session(self, request) -> str:
        user_session_key = request.session.session_key
        if not user_session_key:
            request.session.save()
            user_session_key = request.session.session_key
        return user_session_key


class CacheInvalidator(CacheInvalidatorInterface):
    def invalidate_package_type_cache(self):
        from delivery_app.views import PackageTypeList

        cache.delete(PackageTypeList.cache_key)
