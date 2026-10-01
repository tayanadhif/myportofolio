import re

from django import forms
from django.forms import ModelForm, TextInput, Textarea, URLInput
from django.utils.html import strip_tags

from main.models import PortfolioItem, ProjectSubmission


class PortfolioItemForm(ModelForm):
    def _sanitize_text(self, value, preserve_newlines=False):
        if value is None:
            return value

        cleaned = strip_tags(str(value))
        cleaned = re.sub(r"(?is)<script.*?>.*?</script>", "", cleaned)
        cleaned = re.sub(r"(?is)javascript\s*:", "", cleaned)
        cleaned = re.sub(r"(?is)on\w+\s*=", "", cleaned)
        cleaned = re.sub(r"(?is)alert\s*\([^)]*\)", "", cleaned)
        if preserve_newlines:
            cleaned = "\n".join(
                re.sub(r"[ \t]{2,}", " ", line).strip()
                for line in cleaned.splitlines()
            )
            cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        else:
            cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
        return cleaned

    def clean_title(self):
        return self._sanitize_text(self.cleaned_data.get("title"))

    def clean_description(self):
        return self._sanitize_text(
            self.cleaned_data.get("description"),
            preserve_newlines=True,
        )

    def clean_tech_stack(self):
        return self._sanitize_text(self.cleaned_data.get("tech_stack"))

    def clean_project_url(self):
        value = self.cleaned_data.get("project_url")
        if value is None:
            return value
        return self._sanitize_text(value)

    def clean_project_image_url(self):
        value = self.cleaned_data.get("project_image_url")
        if value is None:
            return value
        return self._sanitize_text(value)

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
            "title": "Judul Project",
            "category": "Kategori",
            "estimated_budget": "Estimasi Biaya",
            "is_featured": "Prioritaskan project ini",
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
