from rest_framework import serializers

from .models import Package, PackageType


class PackageTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageType
        fields = ["id", "name"]


class PackageSerializer(serializers.ModelSerializer):
    package_type_name = serializers.ReadOnlyField(source="package_type.name")

    class Meta:
        model = Package
        fields = [
            "id",
            "name",
            "weight",
            "package_type",
            "package_type_name",
            "declared_value",
            "delivery_cost",
            "user_session",
        ]
        read_only_fields = ["user_session"]


class PackageRegistrationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    weight = serializers.FloatField()
    package_type_name = serializers.CharField(max_length=100)
    declared_value = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_package_type_name(self, value):
        try:
            PackageType.objects.get(name=value)
        except PackageType.DoesNotExist:
            raise serializers.ValidationError("Invalid package type name.")
        return value
