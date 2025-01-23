import logging

from celery import shared_task

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

    except Exception as e:
        logger.error(f"Error registering package: {e}")
        self.retry(exc=e)
