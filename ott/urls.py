from django.urls import path
from . import views
from allauth.account.views import LogoutView

app_name = 'ott'

urlpatterns = [
    path('', views.Home.as_view(), name='Home'),  # Home page
    path('subscription-plan/', views.SubscriptionPlan.as_view(), name='subscription-plan'),
    path('profile/', views.ProfileList.as_view(), name='profile-list'),
    path('profile/create/', views.ProfileCreate.as_view(), name='profile-create'),
    path('watch/<str:profile_id>/', views.MovieList.as_view(), name='movie-list'),
    path('movie/<uuid:movie_id>/', views.movie_detail, name='movie-detail'),
    path('play/<uuid:movie_id>/', views.play_movie, name='play-movie'),
    path('accounts/logout/', LogoutView.as_view(), name='account_logout'), 
    path('payment-success/', views.PaymentSuccess.as_view(), name='payment-success'),
    path('payment-cancel/', views.PaymentCancel.as_view(), name='payment-cancel'),
    path('feedback/', views.feedback_view, name='feedback'),
    path('payment-success/', views.PaymentSuccess.as_view(), name='payment-success'),
]
