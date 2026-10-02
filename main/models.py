import uuid
from django.db import models
from django.contrib.auth.models import User


class Experience(models.Model):
    EXPERIENCE_CHOICES = [
        ('internship', 'Internship'),
        ('research', 'Research'),
        ('volunteer', 'Volunteer'),
        ('part-time', 'Part-Time'),
        ('full-time', 'Full-Time'),
        ('freelance', 'Freelance'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=EXPERIENCE_CHOICES,
        default='full-time'
    )
    thumbnail = models.URLField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title

    @property
    def is_ongoing(self):
        return self.ended_at is None


class PortfolioItem(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, default='featured')
    link = models.URLField(blank=True, null=True)
    tech_stack = models.CharField(max_length=255, blank=True, default='')
    project_url = models.URLField(blank=True, null=True)
    project_image_url = models.URLField(blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0, db_index=True)
    starred_by = models.ManyToManyField(
        User,
        related_name="starred_projects",
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title


class UserProfile(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    profile_image = models.ImageField(upload_to="profiles/", blank=True)
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.full_name or self.user.username


class UserConnection(models.Model):
    PLATFORM_CHOICES = [
        ("youtube", "YouTube"),
        ("instagram", "Instagram"),
        ("tiktok", "TikTok"),
        ("roblox", "Roblox"),
        ("spotify", "Spotify"),
        ("twitch", "Twitch"),
        ("github", "GitHub"),
        ("linkedin", "LinkedIn"),
        ("website", "Website"),
        ("other", "Other"),
    ]

    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="connections")
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    label = models.CharField(max_length=80, blank=True)
    url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.label or self.get_platform_display()


class ChatMessage(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_messages")
    body = models.CharField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: {self.body[:60]}"


class ProjectComment(models.Model):
    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(PortfolioItem, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="project_comments")
    body = models.CharField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.title}: {self.body[:60]}"


class ProjectSubmission(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50)
    estimated_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_featured = models.BooleanField(default=False)
    submission_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title