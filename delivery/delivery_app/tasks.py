import logging

from celery import shared_task
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import DatabaseError

from .repositories import PackageRepository
from .services import DeliveryCostCalculator
from .use_cases import PackageRegistrationUseCase

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def register_package_task(self, package_data):
    """
    Task to asynchronously register a package and calculate its delivery cost.
    """
    try:
        package_registration_use_case = PackageRegistrationUseCase(
            package_repository=PackageRepository(),
            delivery_cost_calculator=DeliveryCostCalculator(),
        )
        package, warning = package_registration_use_case.register_package(
            user_session=package_data["user_session"],
            name=package_data["name"],
            weight=package_data["weight"],
            package_type_name=package_data["package_type_name"],
            declared_value=package_data["declared_value"],
        )

        if warning:
            logger.warning(warning)

        logger.info(f"Package {package.id} registered and delivery cost calculated.")

    except ObjectDoesNotExist as e:
        logger.error(f"Package type not found: {e}")
    except ValidationError as e:
        logger.error(f"Data validation error: {e}")
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        self.retry(exc=e)
    except TypeError as e:
        logger.error(f"Type error: {e}")
        self.retry(exc=e)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        self.retry(exc=e)
