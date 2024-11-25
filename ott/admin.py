from django.contrib import admin
from .models import Movie, Season, Video,Subscription,Feedback


class VideoInline(admin.TabularInline):  # Inline for videos
    model = Video
    extra = 1
    fields = ('title', 'episode_number', 'file')


class SeasonInline(admin.TabularInline):  # Inline for seasons
    model = Season
    extra = 1
    fields = ('season_number', 'title')


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'age_limit')
    inlines = [SeasonInline]  # Add seasons inline


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('title', 'movie', 'season_number')
    inlines = [VideoInline]  # Add videos inline


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'season', 'episode_number')

admin.site.register(Subscription)
admin.site.register(Feedback)