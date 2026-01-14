from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Professional


class ProfessionalModelTests(TestCase):
    """Tests for the Professional model."""

    def test_create_professional(self):
        """Test creating a professional with valid data."""
        professional = Professional.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+14155551234",
            source="direct",
            company_name="Acme Inc",
            job_title="Engineer",
        )
        self.assertEqual(professional.first_name, "John")
        self.assertEqual(professional.last_name, "Doe")
        self.assertEqual(professional.email, "john@example.com")
        self.assertEqual(professional.source, "direct")
        self.assertEqual(professional.full_name, "John Doe")

    def test_phone_empty_converts_to_null(self):
        """Test that empty phone string is converted to None."""
        professional = Professional.objects.create(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone="",
            source="partner",
        )
        self.assertIsNone(professional.phone)

    def test_multiple_null_phones_allowed(self):
        """Test that multiple professionals can have null phones."""
        Professional.objects.create(
            first_name="User",
            last_name="One",
            email="user1@example.com",
            phone=None,
            source="direct",
        )
        Professional.objects.create(
            first_name="User",
            last_name="Two",
            email="user2@example.com",
            phone=None,
            source="direct",
        )
        self.assertEqual(Professional.objects.count(), 2)


class ProfessionalAPITests(APITestCase):
    """Tests for the Professional API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.list_create_url = reverse("professional-list-create")
        self.bulk_url = reverse("professional-bulk-create")

        self.valid_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+14155551234",
            "source": "direct",
            "company_name": "Acme Inc",
            "job_title": "Engineer",
        }

    # ============== POST /api/professionals/ Tests ==============

    def test_create_professional_success(self):
        """Test successful professional creation."""
        response = self.client.post(
            self.list_create_url, self.valid_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["first_name"], "John")
        self.assertEqual(response.data["last_name"], "Doe")
        self.assertEqual(response.data["email"], "john@example.com")
        self.assertEqual(Professional.objects.count(), 1)

    def test_create_professional_without_phone(self):
        """Test creating professional without optional phone."""
        data = self.valid_data.copy()
        del data["phone"]
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["phone"])

    def test_create_professional_duplicate_email(self):
        """Test that duplicate email is rejected."""
        self.client.post(self.list_create_url, self.valid_data, format="json")

        duplicate_data = self.valid_data.copy()
        duplicate_data["phone"] = "+14155559999"
        response = self.client.post(self.list_create_url, duplicate_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_create_professional_duplicate_phone(self):
        """Test that duplicate phone is rejected."""
        self.client.post(self.list_create_url, self.valid_data, format="json")

        duplicate_data = self.valid_data.copy()
        duplicate_data["email"] = "other@example.com"
        response = self.client.post(self.list_create_url, duplicate_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", response.data)

    def test_create_professional_invalid_source(self):
        """Test that invalid source is rejected."""
        data = self.valid_data.copy()
        data["source"] = "invalid"
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("source", response.data)

    def test_create_professional_invalid_phone_format(self):
        """Test that invalid phone format is rejected."""
        data = self.valid_data.copy()
        data["phone"] = "not-a-phone"
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", response.data)

    def test_create_professional_missing_required_fields(self):
        """Test that missing required fields are rejected."""
        # Missing first_name
        data = {"last_name": "Doe", "email": "test@example.com", "source": "direct"}
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("first_name", response.data)

        # Missing last_name
        data = {"first_name": "Test", "email": "test@example.com", "source": "direct"}
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("last_name", response.data)

        # Missing email
        data = {"first_name": "Test", "last_name": "User", "source": "direct"}
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

        # Missing source
        data = {"first_name": "Test", "last_name": "User", "email": "test@example.com"}
        response = self.client.post(self.list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("source", response.data)

    # ============== GET /api/professionals/ Tests ==============

    def test_list_professionals_empty(self):
        """Test listing professionals when none exist."""
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_professionals(self):
        """Test listing all professionals."""
        Professional.objects.create(
            first_name="User",
            last_name="One",
            email="user1@example.com",
            source="direct",
        )
        Professional.objects.create(
            first_name="User",
            last_name="Two",
            email="user2@example.com",
            source="partner",
        )

        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_professionals_filter_by_source(self):
        """Test filtering professionals by source."""
        Professional.objects.create(
            first_name="Direct",
            last_name="User",
            email="direct@example.com",
            source="direct",
        )
        Professional.objects.create(
            first_name="Partner",
            last_name="User",
            email="partner@example.com",
            source="partner",
        )
        Professional.objects.create(
            first_name="Internal",
            last_name="User",
            email="internal@example.com",
            source="internal",
        )

        # Filter by direct
        response = self.client.get(f"{self.list_create_url}?source=direct")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["source"], "direct")

        # Filter by partner
        response = self.client.get(f"{self.list_create_url}?source=partner")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["source"], "partner")

    def test_list_professionals_search(self):
        """Test searching professionals."""
        Professional.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            source="direct",
        )
        Professional.objects.create(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            source="partner",
        )

        # Search by first name
        response = self.client.get(f"{self.list_create_url}?search=John")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["first_name"], "John")

        # Search by email
        response = self.client.get(f"{self.list_create_url}?search=jane@")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["email"], "jane@example.com")

    def test_list_professionals_invalid_source_filter(self):
        """Test that invalid source filter returns error."""
        response = self.client.get(f"{self.list_create_url}?source=invalid")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ============== POST /api/professionals/bulk/ Tests ==============

    def test_bulk_create_success(self):
        """Test successful bulk creation."""
        data = [
            {
                "first_name": "User",
                "last_name": "One",
                "email": "user1@example.com",
                "source": "direct",
            },
            {
                "first_name": "User",
                "last_name": "Two",
                "email": "user2@example.com",
                "source": "partner",
            },
        ]
        response = self.client.post(self.bulk_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"]["created"], 2)
        self.assertEqual(response.data["summary"]["failed"], 0)
        self.assertEqual(Professional.objects.count(), 2)

    def test_bulk_update_by_email(self):
        """Test bulk update using email as unique key."""
        # Create existing professional
        Professional.objects.create(
            first_name="Original",
            last_name="Name",
            email="test@example.com",
            source="direct",
        )

        # Update via bulk endpoint
        data = [
            {
                "first_name": "Updated",
                "last_name": "Person",
                "email": "test@example.com",
                "source": "partner",
                "company_name": "New Company",
            }
        ]
        response = self.client.post(self.bulk_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"]["updated"], 1)
        self.assertEqual(response.data["summary"]["created"], 0)

        # Verify update
        professional = Professional.objects.get(email="test@example.com")
        self.assertEqual(professional.first_name, "Updated")
        self.assertEqual(professional.source, "partner")
        self.assertEqual(professional.company_name, "New Company")

    def test_bulk_partial_success(self):
        """Test bulk operation with partial success."""
        data = [
            {
                "first_name": "New",
                "last_name": "User",
                "email": "new@example.com",
                "source": "direct",
            },
            {
                "first_name": "Missing",
                "last_name": "Email",
                # Missing required email field
                "source": "partner",
            },
            {
                "first_name": "Invalid",
                "last_name": "Source",
                "email": "invalid@example.com",
                "source": "invalid_source",  # Invalid source
            },
        ]
        response = self.client.post(self.bulk_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertEqual(response.data["summary"]["created"], 1)
        self.assertEqual(response.data["summary"]["failed"], 2)

        # Verify results have proper structure
        results = response.data["results"]
        self.assertEqual(results[0]["success"], True)
        self.assertEqual(results[1]["success"], False)
        self.assertEqual(results[2]["success"], False)

    def test_bulk_empty_list(self):
        """Test bulk with empty list returns error."""
        response = self.client.post(self.bulk_url, [], format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_non_list_input(self):
        """Test bulk with non-list input returns error."""
        response = self.client.post(
            self.bulk_url, {"first_name": "Test"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_all_failures(self):
        """Test bulk where all records fail returns 400."""
        data = [
            {
                "first_name": "Test",
                "last_name": "User",
                "source": "invalid",
            },  # Invalid source
            {
                "first_name": "Test",
                "email": "test@example.com",
                "source": "direct",
            },  # Missing last_name
        ]
        response = self.client.post(self.bulk_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["summary"]["failed"], 2)
