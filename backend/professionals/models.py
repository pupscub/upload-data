from django.db import models
from django.core.validators import RegexValidator


class Professional(models.Model):
    """
    Model representing a professional sign-up from various sources.
    """

    SOURCE_CHOICES = [
        ("direct", "Direct"),
        ("partner", "Partner"),
        ("internal", "Internal"),
    ]

    # Phone validator for E.164 format
    phone_validator = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone must be in E.164 format (e.g., +14155551234)",
    )

    first_name = models.CharField(max_length=127)
    last_name = models.CharField(max_length=127)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=17,
        blank=True,
        null=True,
        unique=True,
        validators=[phone_validator],
        help_text="Phone number in E.164 format (e.g., +14155551234)",
    )
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    company_name = models.CharField(max_length=255, blank=True, default="")
    job_title = models.CharField(max_length=255, blank=True, default="")
    resume = models.FileField(
        upload_to="resumes/",
        blank=True,
        null=True,
        help_text="PDF resume file",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Professional"
        verbose_name_plural = "Professionals"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        """Return full name for convenience."""
        return f"{self.first_name} {self.last_name}".strip()

    def clean(self):
        """Convert empty phone string to None for proper uniqueness handling."""
        super().clean()
        if self.phone == "":
            self.phone = None

    def save(self, *args, **kwargs):
        """Ensure clean() is called before save."""
        if self.phone == "":
            self.phone = None
        super().save(*args, **kwargs)
