import re
from rest_framework import serializers
from .models import Professional


class ProfessionalSerializer(serializers.ModelSerializer):
    """
    Serializer for Professional model with validation.
    """

    phone = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=17
    )
    company_name = serializers.CharField(
        required=False, allow_blank=True, max_length=255, default=""
    )
    job_title = serializers.CharField(
        required=False, allow_blank=True, max_length=255, default=""
    )
    # Read-only computed field for full name
    full_name = serializers.SerializerMethodField()
    # Resume URL for downloads
    resume_url = serializers.SerializerMethodField()

    class Meta:
        model = Professional
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "source",
            "company_name",
            "job_title",
            "resume",
            "resume_url",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "full_name", "resume_url"]

    def get_full_name(self, obj):
        """Return concatenated full name."""
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_resume_url(self, obj):
        """Return the URL of the resume file if it exists."""
        if obj.resume:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.resume.url)
            return obj.resume.url
        return None

    def validate_phone(self, value):
        """
        Validate phone format and uniqueness.
        Normalizes phone to E.164 format.
        Returns None for empty values to allow proper uniqueness handling.
        """
        # Convert empty string to None
        if not value or value.strip() == "":
            return None

        value = value.strip()

        # Remove all non-digit characters except leading +
        if value.startswith("+"):
            digits = "+" + re.sub(r"\D", "", value[1:])
        else:
            digits = re.sub(r"\D", "", value)

        # Normalize to E.164 format
        # If it's a 10-digit US number, add +1
        if len(digits) == 10:
            digits = "+1" + digits
        # If it's 11 digits starting with 1, add +
        elif len(digits) == 11 and digits.startswith("1"):
            digits = "+" + digits
        # If it doesn't start with +, add it
        elif not digits.startswith("+"):
            digits = "+" + digits

        # Validate E.164 format (+ followed by 10-15 digits)
        if not re.match(r"^\+\d{10,15}$", digits):
            raise serializers.ValidationError(
                "Phone must be in E.164 format (e.g., +14155551234)"
            )

        # Check uniqueness (exclude current instance on update)
        queryset = Professional.objects.filter(phone=digits)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Phone number already exists.")

        return digits

    def validate_email(self, value):
        """
        Validate email uniqueness.
        """
        if not value:
            raise serializers.ValidationError("Email is required.")

        value = value.lower().strip()

        # Check uniqueness (exclude current instance on update)
        queryset = Professional.objects.filter(email=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Email already exists.")

        return value

    def validate_source(self, value):
        """
        Validate source is one of the allowed choices.
        """
        valid_sources = ["direct", "partner", "internal"]
        if value not in valid_sources:
            raise serializers.ValidationError(
                f"Source must be one of: {', '.join(valid_sources)}"
            )
        return value

    def validate_first_name(self, value):
        """
        Validate first_name is not empty.
        """
        if not value or value.strip() == "":
            raise serializers.ValidationError("First name is required.")
        return value.strip()

    def validate_last_name(self, value):
        """
        Validate last_name is not empty.
        """
        if not value or value.strip() == "":
            raise serializers.ValidationError("Last name is required.")
        return value.strip()


class BulkProfessionalSerializer(serializers.Serializer):
    """
    Serializer for validating bulk professional data.
    Used to parse and validate input before individual processing.
    """

    professionals = serializers.ListField(
        child=serializers.DictField(), allow_empty=False
    )

    def validate_professionals(self, value):
        if not value:
            raise serializers.ValidationError("At least one professional is required.")
        return value
