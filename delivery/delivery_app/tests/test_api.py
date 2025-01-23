import logging
from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from delivery_app.models import Package, PackageType

logger = logging.getLogger(__name__)


class PackageTypeListViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("package-types")
        self.package_type_electronics = PackageType.objects.get(name="Electronics")
        self.package_type_clothes = PackageType.objects.get(name="Clothes")
        self.package_type_other = PackageType.objects.get(name="Other")

    def test_get_package_types(self):
        logger.info("Running test_get_package_types")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)
        self.assertEqual(response.data["results"][0]["name"], "Electronics")
        self.assertEqual(response.data["results"][1]["name"], "Clothes")
        self.assertEqual(response.data["results"][2]["name"], "Other")

    def test_package_types_cached(self):
        cache.delete("package_types")
        self.client.get(self.url)
        self.assertIsNotNone(cache.get("package_types"))

        with self.assertNumQueries(0):
            self.client.get(self.url)


class PackageRegistrationViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("package-registration")

        self.package_type_electronics = PackageType.objects.get(name="Electronics")
        self.package_type_clothes = PackageType.objects.get(name="Clothes")
        self.package_type_other = PackageType.objects.get(name="Other")

        self.valid_payload = {
            "name": "Test Package",
            "weight": 1.5,
            "package_type_name": self.package_type_electronics.name,
            "declared_value": "100",
        }

    @patch("delivery_app.tasks.register_package_task.delay")
    def test_register_package_valid_data(self, mock_task):
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("session_key", response.data)
        self.assertEqual(response.data["message"], "Package registration initiated.")

        mock_task.assert_called_once()

    def test_register_package_invalid_data(self):
        invalid_payload = {
            "name": "",
            "weight": "abc",
            "package_type_name": self.package_type_electronics.name,
            "declared_value": "100",
        }
        response = self.client.post(self.url, invalid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
        self.assertIn("weight", response.data)

    def test_register_package_creates_session(self):
        self.assertIsNotNone(self.client.session.session_key)


class UserPackageListViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("user-packages")

        self.package_type_electronics = PackageType.objects.get(name="Electronics")
        self.package_type_clothes = PackageType.objects.get(name="Clothes")
        self.package_type_other = PackageType.objects.get(name="Other")

        self.session = self.client.session
        self.session.save()

    def create_package(self, session_key, package_type, delivery_cost=None):
        package = Package.objects.create(
            name="Test Package",
            weight=1.5,
            package_type=package_type,
            declared_value=100,
            delivery_cost=delivery_cost,
            user_session=session_key,
        )
        return package

    def test_get_packages_without_session(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_get_packages_with_session(self):
        session_key = self.session.session_key
        package1 = self.create_package(session_key, self.package_type_clothes)
        package2 = self.create_package(session_key, self.package_type_electronics)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["results"][0]["id"], package2.id)
        self.assertEqual(response.data["results"][1]["id"], package1.id)

    def test_filter_by_type(self):
        session_key = self.session.session_key
        self.create_package(session_key, self.package_type_electronics)

        response = self.client.get(
            self.url, {"type": self.package_type_electronics.name}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["package_type_name"], "Electronics"
        )

    def test_filter_by_delivery_cost_calculated(self):
        session_key = self.session.session_key
        self.create_package(
            session_key, self.package_type_clothes, delivery_cost=Decimal("5.0")
        )
        self.create_package(session_key, self.package_type_electronics)

        response = self.client.get(self.url, {"is_calculated": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIsNotNone(response.data["results"][0]["delivery_cost"])

        response = self.client.get(self.url, {"is_calculated": "false"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIsNone(response.data["results"][0]["delivery_cost"])

    def test_pagination(self):
        session_key = self.session.session_key

        for _ in range(15):
            self.create_package(session_key, self.package_type_clothes)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data["next"])


class PackageDetailViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.package_type_electronics = PackageType.objects.get(name="Electronics")
        self.package_type_clothes = PackageType.objects.get(name="Clothes")
        self.package_type_other = PackageType.objects.get(name="Other")

        self.session = self.client.session
        self.session.save()
        self.session_key = self.session.session_key

    def create_package(self, session_key, package_type, delivery_cost=None):
        package = Package.objects.create(
            name="Test Package",
            weight=1.5,
            package_type=package_type,
            declared_value=100,
            delivery_cost=delivery_cost,
            user_session=session_key,
        )
        return package

    def test_get_package_detail_without_session(self):
        package = self.create_package("test_session", self.package_type_electronics)
        self.client.session.flush()
        url = reverse("package-detail", kwargs={"id": package.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_package_detail_with_session(self):
        package = self.create_package(
            self.session_key,
            self.package_type_electronics,
            delivery_cost=Decimal("5.0"),
        )
        url = reverse("package-detail", kwargs={"id": package.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], package.id)
        self.assertEqual(response.data["name"], "Test Package")
        self.assertEqual(response.data["weight"], 1.5)
        self.assertEqual(response.data["package_type_name"], "Electronics")
        self.assertEqual(response.data["declared_value"], "100.00")
        self.assertEqual(response.data["delivery_cost"], "5.00")

    def test_get_package_detail_wrong_session(self):
        self.client.session.flush()
        package = self.create_package("wrong_session", self.package_type_electronics)

        url = reverse("package-detail", kwargs={"id": package.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
