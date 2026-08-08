from django.db import models

from .services import CacheInvalidator


class PackageType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache_invalidator = CacheInvalidator()
        cache_invalidator.invalidate_package_type_cache()


class Package(models.Model):
    user_session = models.CharField(max_length=40, db_index=True)
    name = models.CharField(max_length=255)
    weight = models.FloatField()
    package_type = models.ForeignKey(PackageType, on_delete=models.PROTECT)
    declared_value = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    def __str__(self):
        return f"{self.name} ({self.user_session})"
