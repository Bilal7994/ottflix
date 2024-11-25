from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.timezone import now
from datetime import timedelta
from .forms import ProfileForm,FeedbackForm
from .models import Profile, Movie, Video, Subscription
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.mail import send_mail


# Subscription Decorator
def subscription_required(view_func):
    def wrapper(request, *args, **kwargs):
        subscription = Subscription.objects.filter(user=request.user, end_date__gte=now().date()).first()
        if not subscription or not subscription.is_active():
            return redirect('ott:subscription-plan')
        return view_func(request, *args, **kwargs)
    return wrapper


class Home(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('ott:profile-list')
        return render(request, 'index.html')



@method_decorator(login_required, name='dispatch')
class ProfileList(View):
    def get(self, request, *args, **kwargs):
        profiles = request.user.profiles.all()
        return render(request, 'profileList.html', {'profiles': profiles})


@method_decorator(login_required, name='dispatch')
class ProfileCreate(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'profilecreate.html', {'form': ProfileForm()})

    def post(self, request, *args, **kwargs):
        form = ProfileForm(request.POST)
        if form.is_valid():
            profile = Profile.objects.create(**form.cleaned_data)
            request.user.profiles.add(profile)
            return redirect('ott:profile-list')
        return render(request, 'profilecreate.html', {'form': form})


# @method_decorator([login_required, subscription_required], name='dispatch')
@method_decorator(login_required, name='dispatch')
class MovieList(View):
    def get(self, request, profile_id, *args, **kwargs):
        profile = get_object_or_404(Profile, uuid=profile_id)
        if profile not in request.user.profiles.all():
            return redirect('ott:profile-list')
        
        query = request.GET.get('q')
        page_number = request.GET.get('page', 1)
        
        # Base query based on age limit
        if profile.age_limit == 'All':
            movies = Movie.objects.all().order_by('-created')
            p ='All'
        else:
            movies = Movie.objects.filter(age_limit=profile.age_limit).order_by('-created')
            p = 'kids'
        
        if query:
            movies = movies.filter(Q(title__icontains=query) | Q(description__icontains=query))
        
        # Separate queries for Movie types
        popular_movies = movies.order_by('-created')  # Popular movies by creation date (or any other metric)
        single_movies = movies.filter(type='single')
        kids_animations = movies.filter(age_limit='Kids')  # Filter for kids animations
        seasonal_movies = movies.filter(type='seasonal')

        # Paginate each movie list
        paginator_popular = Paginator(popular_movies, 4)
        paginator_single = Paginator(single_movies, 4)
        paginator_kids = Paginator(kids_animations, 4)
        paginator_seasonal = Paginator(seasonal_movies, 4)

        popular_movies_page = paginator_popular.get_page(page_number)
        single_movies_page = paginator_single.get_page(page_number)
        kids_animations_page = paginator_kids.get_page(page_number)
        seasonal_movies_page = paginator_seasonal.get_page(page_number)
        
        # Respond to AJAX request with partial templates
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            popular_movies_html = render_to_string('partials/movie_list.html', {'movies': popular_movies_page}, request)
            single_movies_html = render_to_string('partials/movie_list.html', {'movies': single_movies_page}, request)
            kids_animations_html = render_to_string('partials/movie_list.html', {'movies': kids_animations_page}, request)
            seasonal_movies_html = render_to_string('partials/movie_list.html', {'movies': seasonal_movies_page}, request)
            
            pagination_html_popular = render_to_string('partials/pagination.html', {'movies': popular_movies_page}, request)
            pagination_html_single = render_to_string('partials/pagination.html', {'movies': single_movies_page}, request)
            pagination_html_kids = render_to_string('partials/pagination.html', {'movies': kids_animations_page}, request)
            pagination_html_seasonal = render_to_string('partials/pagination.html', {'movies': seasonal_movies_page}, request)

            return JsonResponse({
                'popular_movies_html': popular_movies_html,
                'single_movies_html': single_movies_html,
                'kids_animations_html': kids_animations_html,
                'seasonal_movies_html': seasonal_movies_html,
                'pagination_html_popular': pagination_html_popular,
                'pagination_html_single': pagination_html_single,
                'pagination_html_kids': pagination_html_kids,
                'pagination_html_seasonal': pagination_html_seasonal,
            })

        # For standard requests, render the full template
        context = {
            'popular_movies': popular_movies_page,
            'single_movies': single_movies_page,
            'kids_animations': kids_animations_page,
            'seasonal_movies': seasonal_movies_page,
            'query': query,
            'p':p,
        }
        return render(request, 'movieList.html', context)
    
    
@login_required
@subscription_required
def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, uuid=movie_id)
    context = {
        "movie": movie,
        "videos": movie.videos.all() if movie.type == "single" else None,
        "seasons": movie.seasons.all() if movie.type != "single" else None,
    }
    return render(request, 'movieDetail.html', context)


def play_movie(request, movie_id):
    movie = get_object_or_404(Movie, uuid=movie_id)
    videos = Video.objects.filter(season__in=movie.seasons.all())
    context = {"movie": [{"title": v.title, "file": request.build_absolute_uri(v.file.url), "episode_number": v.episode_number} for v in videos]}
    return render(request, 'showMovie.html', context)


class SubscriptionPlan(View):
    def get(self, request, *args, **kwargs):
        plan_details = {
            'monthly': {'price': '10.00', 'description': 'Monthly Subscription'},
            'six_month': {'price': '50.00', 'description': '6-Month Subscription'},
            'yearly': {'price': '90.00', 'description': 'Yearly Subscription'},
        }
        return render(request, 'subscription_plan.html', {"PAYPAL_CLIENT_ID": settings.PAYPAL_CLIENT_ID, "plan_details": plan_details})










# class PaymentSuccess(View):
#     def get(self, request, *args, **kwargs):
#         subscription_plan = request.GET.get('plan')  # Get the subscription plan from the URL
#         payment_id = request.GET.get('paymentId')  # Get the payment ID from the URL

#         # Validate the plan
#         if subscription_plan not in dict(Subscription.PLAN_CHOICES):
#             messages.error(request, "Invalid subscription plan selected.")
#             return redirect('ott:subscription-plan')

#         # Get or create the subscription for the user
#         subscription, created = Subscription.objects.get_or_create(user=request.user)

#         # Update the subscription details
#         subscription.plan = subscription_plan
#         subscription.payment_id = payment_id
#         subscription.start_date = now().date()  # Set the current date as the start date

#         # Calculate the end date manually
#         if subscription.plan == 'monthly':
#             subscription.end_date = subscription.start_date + timedelta(days=30)
#         elif subscription.plan == 'six_month':
#             subscription.end_date = subscription.start_date + timedelta(days=180)
#         elif subscription.plan == 'yearly':
#             subscription.end_date = subscription.start_date + timedelta(days=365)

#         subscription.save()  # Save the subscription

#         # Compose the email
#         subject = "Payment Successful: Subscription Updated"
#         message = (
#             f"Dear {request.user.first_name},\n\n"
#             f"Thank you for your payment! Your subscription has been successfully updated.\n\n"
#             f"Subscription Plan: {subscription.plan.capitalize()}\n"
#             f"Start Date: {subscription.start_date}\n"
#             f"End Date: {subscription.end_date}\n\n"
#             f"We hope you enjoy our services!\n\n"
#             f"Best regards,\n"
#             f"The OTTFLIX"
#         )
#         recipient_email = request.user.email
#         from_email = "ottplatform7994@gmail.com"  

#         # Send the email
#         try:
#             send_mail(subject, message, from_email, [recipient_email], fail_silently=False)
#         except Exception as e:
#             messages.warning(request, "Payment successful, but we couldn't send an email. Please contact support if needed.")

#         messages.success(request, "Payment successful! Subscription updated.")
#         return redirect('ott:profile-list')




class PaymentSuccess(View):
    def get(self, request, *args, **kwargs):
        subscription_plan = request.GET.get('plan')  # Get the subscription plan from the URL
        payment_id = request.GET.get('paymentId')  # Get the payment ID from the URL

        # Validate the plan
        if subscription_plan not in dict(Subscription.PLAN_CHOICES):
            messages.error(request, "Invalid subscription plan selected.")
            return redirect('ott:subscription-plan')

        # Get or create the subscription for the user
        subscription, created = Subscription.objects.get_or_create(user=request.user)

        # Update the subscription details
        subscription.plan = subscription_plan
        subscription.payment_id = payment_id
        subscription.start_date = now().date()  # Set the current date as the start date

        # Calculate the end date manually
        if subscription.plan == 'monthly':
            subscription.end_date = subscription.start_date + timedelta(days=30)
        elif subscription.plan == 'six_month':
            subscription.end_date = subscription.start_date + timedelta(days=180)
        elif subscription.plan == 'yearly':
            subscription.end_date = subscription.start_date + timedelta(days=365)

        subscription.save()  # Save the subscription

        # Send success email
        subject = "Payment Successful: Subscription Updated"
        message = (
            f"Dear {request.user.first_name},\n\n"
            f"Thank you for your payment! Your subscription has been successfully updated.\n\n"
            f"Subscription Plan: {subscription.plan.capitalize()}\n"
            f"Start Date: {subscription.start_date}\n"
            f"End Date: {subscription.end_date}\n\n"
            f"We hope you enjoy our services!\n\n"
            f"Best regards,\n"
            f"The OTT Team"
        )
        recipient_email = request.user.email
        from_email = "ottplatform7994@gmail.com"  # Replace with your actual support email

        try:
            send_mail(subject, message, from_email, [recipient_email], fail_silently=False)
        except Exception as e:
            messages.warning(request, "Payment successful, but we couldn't send an email. Please contact support if needed.")

        # Prepare context for the success page
        context = {
            "plan": subscription.plan.capitalize(),
            "start_date": subscription.start_date,
            "end_date": subscription.end_date,
        }

        return render(request, 'payment_success.html', context)



class PaymentCancel(View):
    def get(self, request, *args, **kwargs):
        messages.error(request, "Payment was cancelled. Please try again.")
        return redirect('ott:subscription-plan')


@login_required
def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            return redirect('ott:Home')  # Replace with your home page or success page
    else:
        form = FeedbackForm()
    return render(request, 'feedback.html', {'form': form})