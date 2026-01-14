from django.urls import path
from . import views

urlpatterns = [
    path("", views.professional_list_create, name="professional-list-create"),
    path("<int:pk>/", views.professional_delete, name="professional-delete"),
    path("bulk/", views.professional_bulk_create, name="professional-bulk-create"),
    path(
        "bulk-delete/", views.professional_bulk_delete, name="professional-bulk-delete"
    ),
    path("export-csv/", views.professional_export_csv, name="professional-export-csv"),
    path("extract-resume/", views.extract_resume, name="extract-resume"),
]
