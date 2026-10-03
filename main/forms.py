import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import CharField, ChoiceField, ModelForm, TextInput, Textarea, URLInput, inlineformset_factory
from django.utils.html import strip_tags

from main.models import PortfolioItem, ProjectSubmission, UserConnection, UserProfile


class RegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=150, label="Full name")
    email = forms.EmailField(label="Email")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(("full_name", "username", "email", "password1", "password2"))

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class AccountDetailsForm(ModelForm):
    class Meta:
        model = User
        fields = ("username", "email")
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }


class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ("profile_image", "full_name", "phone", "date_of_birth", "bio")
        labels = {
            "profile_image": "Profile picture",
            "full_name": "Full name",
            "phone": "Phone (optional)",
            "date_of_birth": "Date of birth",
            "bio": "Bio (optional)",
        }
        widgets = {
            "profile_image": forms.FileInput(attrs={"accept": "image/*"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "bio": Textarea(attrs={"rows": 4, "placeholder": "Tell us a little about yourself"}),
        }

    def clean_profile_image(self):
        image = self.cleaned_data.get("profile_image")
        if image and image.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Profile picture must be 5 MB or smaller.")
        return image

    def clean_bio(self):
        return strip_tags(self.cleaned_data.get("bio", ""))


class UserConnectionForm(ModelForm):
    platform = ChoiceField(
        choices=UserConnection.PLATFORM_CHOICES,
        label="Platform",
    )

    custom_platform = CharField(
        label="Platform name",
        required=False,
        max_length=50,
        widget=TextInput(
            attrs={
                "placeholder": "e.g. Discord",
            }
        ),
    )

    class Meta:
        model = UserConnection
        fields = ("platform", "custom_platform", "label", "url")
        labels = {
            "platform": "Platform",
            "custom_platform": "Platform name",
            "label": "Display name",
            "url": "Profile link",
        }
        widgets = {
            "label": TextInput(
                attrs={
                    "placeholder": "e.g. Bang Toon",
                }
            ),
            "url": URLInput(
                attrs={
                    "placeholder": "https://...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            choices = dict(UserConnection.PLATFORM_CHOICES)

            if self.instance.platform not in choices:
                self.initial["platform"] = "other"
                self.initial["custom_platform"] = self.instance.platform

    def clean(self):
        cleaned_data = super().clean()

        platform = cleaned_data.get("platform")
        custom_platform = cleaned_data.get(
            "custom_platform", ""
        ).strip()

        if platform == "other" and not custom_platform:
            self.add_error(
                "custom_platform",
                "Please enter the platform name.",
            )

        cleaned_data["custom_platform"] = custom_platform

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        platform = self.cleaned_data.get("platform")
        custom_platform = self.cleaned_data.get(
            "custom_platform", ""
        ).strip()

        if platform == "other" and custom_platform:
            instance.platform = custom_platform

        if commit:
            instance.save()
            self.save_m2m()

        return instance


UserConnectionFormSet = inlineformset_factory(
    UserProfile,
    UserConnection,
    form=UserConnectionForm,
    extra=1,
    can_delete=True,
    max_num=20,
    validate_max=True,
)


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
