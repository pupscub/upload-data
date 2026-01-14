from django.urls import path
from . import views

urlpatterns = [
    path("", views.professional_list_create, name="professional-list-create"),
    path("bulk/", views.professional_bulk_create, name="professional-bulk-create"),
    path("extract-resume/", views.extract_resume, name="extract-resume"),
]
