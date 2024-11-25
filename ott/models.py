from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.conf import settings  
from django.db import models
from django.utils.timezone import now
from datetime import timedelta

AGE_CHOICES = (
    ('All', 'All'),
    ('Kids', 'Kids'),
)

MOVIE_CHOICES = (
    ('seasonal', 'Seasonal'),
    ('single', 'Single'),
)

class CustomUser(AbstractUser):
    profiles = models.ManyToManyField('Profile', blank=True)

class Profile(models.Model):
    name = models.CharField(max_length=1000)
    age_limit = models.CharField(choices=AGE_CHOICES, max_length=10)
    uuid = models.UUIDField(default=uuid.uuid4)

    def __str__(self):
        return self.name

class Movie(models.Model):
    title = models.CharField(max_length=1000)
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(default=uuid.uuid4)
    type = models.CharField(choices=MOVIE_CHOICES, max_length=10)
    age_limit = models.CharField(choices=AGE_CHOICES, max_length=10)
    image = models.ImageField(upload_to='covers')

    # Link to videos for single movies
    videos = models.ManyToManyField('Video', blank=True, related_name='single_movies')

    def __str__(self):
        return self.title


class Video(models.Model):
    title = models.CharField(max_length=1000)
    file = models.FileField(upload_to='movies')
    season = models.ForeignKey(
        'Season', related_name='videos', on_delete=models.CASCADE, blank=True, null=True
    )
    episode_number = models.PositiveIntegerField(blank=True, null=True)  # Optional for ordering episodes

    def __str__(self):
        return self.title


class Season(models.Model):
    movie = models.ForeignKey(
        Movie, related_name='seasons', on_delete=models.CASCADE
    )
    season_number = models.PositiveIntegerField()
    title = models.CharField(max_length=1000)

    def __str__(self):
        return f"Season {self.season_number} of {self.movie.title}"






class Subscription(models.Model):
    PLAN_CHOICES = [
        ('monthly', 'Monthly'),
        ('six_month', '6-Month'),
        ('yearly', 'Yearly'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    payment_id = models.CharField(max_length=255, blank=True, null=True)

    def is_active(self):
        """
        Check if the subscription is active based on the current date.
        """
        return self.end_date and self.end_date >= now().date()

    def save(self, *args, **kwargs):
        """
        Calculate the subscription end date based on the selected plan.
        """
        if not self.start_date:
            self.start_date = now().date()

        if self.plan == 'monthly':
            self.end_date = self.start_date + timedelta(days=30)
        elif self.plan == 'six_month':
            self.end_date = self.start_date + timedelta(days=180)
        elif self.plan == 'yearly':
            self.end_date = self.start_date + timedelta(days=365)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.plan}"
    
    

class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.user.username}: {self.title}"



