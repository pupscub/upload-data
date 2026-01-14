import os
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from django.db.models import Q
from django.conf import settings

from .models import Professional
from .serializers import ProfessionalSerializer
from .services import extract_with_llm, extract_with_python


@api_view(["GET", "POST"])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def professional_list_create(request):
    """
    GET: List all professionals with optional source filter and search.
    POST: Create a single professional (supports file upload for resume).
    """
    if request.method == "GET":
        return list_professionals(request)
    elif request.method == "POST":
        return create_professional(request)


def list_professionals(request):
    """
    List all professionals with optional source filter and search.
    Query params:
        - source: filter by source (direct, partner, internal)
        - search: search across first_name, last_name, email, phone
    """
    queryset = Professional.objects.all()

    # Apply source filter if provided
    source = request.query_params.get("source")
    if source:
        valid_sources = ["direct", "partner", "internal"]
        if source not in valid_sources:
            return Response(
                {
                    "error": f"Invalid source. Must be one of: {', '.join(valid_sources)}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = queryset.filter(source=source)

    # Apply search filter if provided
    search = request.query_params.get("search")
    if search:
        search = search.strip()
        queryset = queryset.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
        )

    serializer = ProfessionalSerializer(
        queryset, many=True, context={"request": request}
    )
    return Response(serializer.data)


def create_professional(request):
    """
    Create a single professional.
    Supports multipart form data for resume upload.
    """
    serializer = ProfessionalSerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def professional_bulk_create(request):
    """
    Bulk create/update professionals.

    Upsert logic:
    - Use email as the unique key for matching existing records.
    - If email is not provided, fall back to phone as the unique key.

    Handles partial success - some records may succeed while others fail.

    Request body: List of professional objects

    Response format:
    {
        "results": [
            {"index": 0, "success": true, "action": "created", "data": {...}},
            {"index": 1, "success": true, "action": "updated", "data": {...}},
            {"index": 2, "success": false, "error": {...}}
        ],
        "summary": {"total": 3, "created": 1, "updated": 1, "failed": 1}
    }
    """
    if not isinstance(request.data, list):
        return Response(
            {"error": "Request body must be a list of professionals"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(request.data) == 0:
        return Response(
            {"error": "At least one professional is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    results = []
    summary = {"total": len(request.data), "created": 0, "updated": 0, "failed": 0}

    for index, item in enumerate(request.data):
        try:
            result = process_single_professional(item, index, request)
            results.append(result)

            if result["success"]:
                if result["action"] == "created":
                    summary["created"] += 1
                else:
                    summary["updated"] += 1
            else:
                summary["failed"] += 1

        except Exception as e:
            results.append(
                {"index": index, "success": False, "error": {"detail": str(e)}}
            )
            summary["failed"] += 1

    # Determine response status
    if summary["failed"] == summary["total"]:
        response_status = status.HTTP_400_BAD_REQUEST
    elif summary["failed"] > 0:
        response_status = status.HTTP_207_MULTI_STATUS
    else:
        response_status = status.HTTP_200_OK

    return Response({"results": results, "summary": summary}, status=response_status)


def process_single_professional(item, index, request):
    """
    Process a single professional for bulk upsert.

    Returns dict with: index, success, action (created/updated), data/error
    """
    # Find existing record by email (primary) or phone (fallback)
    existing = find_existing_professional(item)

    if existing:
        # Update existing record
        serializer = ProfessionalSerializer(
            existing, data=item, partial=True, context={"request": request}
        )
        action = "updated"
    else:
        # Create new record
        serializer = ProfessionalSerializer(data=item, context={"request": request})
        action = "created"

    if serializer.is_valid():
        serializer.save()
        return {
            "index": index,
            "success": True,
            "action": action,
            "data": serializer.data,
        }
    else:
        return {"index": index, "success": False, "error": serializer.errors}


def find_existing_professional(item):
    """
    Find existing professional by email (primary) or phone (fallback).

    Returns Professional instance or None.
    """
    email = item.get("email")
    phone = item.get("phone")

    # Try email first (primary unique key)
    if email:
        match = Professional.objects.filter(email=email.lower().strip()).first()
        if match:
            return match

    # Fallback to phone if provided and no email match
    if phone and phone.strip():
        match = Professional.objects.filter(phone=phone.strip()).first()
        if match:
            return match

    return None


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def extract_resume(request):
    """
    Extract professional data from a PDF resume.

    Request (multipart/form-data):
        - resume: PDF file
        - method: "llm" or "python" (default: "python")
        - openai_key: OpenAI API key (required if method is "llm")

    Response:
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+14155551234",
            "company_name": "Acme Inc",
            "job_title": "Software Engineer"
        }
    """
    resume_file = request.FILES.get("resume")
    if not resume_file:
        return Response(
            {"error": "No resume file provided"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check file type
    if not resume_file.name.lower().endswith(".pdf"):
        return Response(
            {"error": "Only PDF files are supported"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    method = request.data.get("method", "python").lower()

    if method == "llm":
        # Get OpenAI key from request or environment
        openai_key = request.data.get("openai_key") or os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            return Response(
                {
                    "error": "OpenAI API key is required for LLM extraction. Provide 'openai_key' in request or set OPENAI_API_KEY environment variable."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = extract_with_llm(resume_file, openai_key)
    else:
        result = extract_with_python(resume_file)

    if "error" in result:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    return Response(result, status=status.HTTP_200_OK)
