from django import forms
from django.forms import ModelForm, TextInput, Textarea, URLInput

from main.models import PortfolioItem, ProjectSubmission


class PortfolioItemForm(ModelForm):
    class Meta:
        model = PortfolioItem
        fields = [
            "title",
            "description",
            "tech_stack",
            "project_url",
            "project_image_url",
        ]
        labels = {
            "title": "Judul",
            "description": "Deskripsi",
            "tech_stack": "Teknologi yang Digunakan",
            "project_url": "Project URL",
            "project_image_url": "Project Image URL",
        }
        widgets = {
            "title": TextInput(
                attrs={
                    "placeholder": "Portfolio Website",
                    "maxlength": 255,
                }
            ),
            "description": Textarea(
                attrs={
                    "placeholder": "Ceritakan portofolio kamu",
                    "rows": 4,
                }
            ),
            "tech_stack": TextInput(
                attrs={
                    "placeholder": "Django, Python, HTML, CSS",
                }
            ),
            "project_url": URLInput(
                attrs={
                    "placeholder": "https://example.com",
                }
            ),
            "project_image_url": URLInput(
                attrs={
                    "placeholder": "https://drive.google.com/thumbnail?id=...&sz=w1000",
                }
            ),
        }


class ProjectSubmissionForm(ModelForm):
    class Meta:
        model = ProjectSubmission
        fields = [
            "title",
            "category",
            "estimated_budget",
            "is_featured",
        ]
        labels = {
            "title": "Judul Proyek",
            "category": "Kategori",
            "estimated_budget": "Estimasi Biaya",
            "is_featured": "Prioritaskan proyek ini",
        }
        widgets = {
            "title": TextInput(
                attrs={
                    "placeholder": "Website Portofolio",
                    "maxlength": 255,
                }
            ),
            "category": TextInput(
                attrs={
                    "placeholder": "Featured / Web / Mobile",
                    "maxlength": 50,
                }
            ),
            "estimated_budget": forms.NumberInput(
                attrs={
                    "placeholder": "5000000",
                    "step": "1000",
                }
            ),
            "is_featured": forms.CheckboxInput(),
        }


ProjectForm = PortfolioItemForm
