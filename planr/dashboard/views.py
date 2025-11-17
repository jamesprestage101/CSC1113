# Generic
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView
from django.http import JsonResponse
# Validation
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
# Authentication
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.signals import user_logged_in
# Time
from django.utils import timezone
from datetime import timedelta
# Other Files
from .models import *
from .forms import * 
from .utils import *
# LLM
import json

# Check User Subscription status
@receiver(user_logged_in)
def on_login_check_subscription(sender, user, request, **kwargs):
    check_and_update_subscription(user)

# Home Page / Chat Interface
def index(request):
    return render(request, 'index.html')

def chat(request):
    return render(request, 'chat.html')

@csrf_exempt  # Remove in production, restore proper CSRF for logged-in users
def chat_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '').strip()
            if not query:
                return JsonResponse({'error': 'No query submitted.'}, status=400)
            answer = ollama_dcc_response(query)
            return JsonResponse({'answer': answer, 'sources': []})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'POST only'}, status=405)

# User Registration / Login / Logout system (leveraging lecture notes)
class UserSignupView(CreateView):
    model = User
    form_class = UserSignupForm
    template_name = 'registration/user_signup.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('chat')

class UserLoginView(LoginView):
    template_name='registration/login.html'

def logout_user(request):
    logout(request)
    return redirect("/")

# Display and Edit user profiles
@login_required
def profile_view(request):
    return render(request, 'registration/profile.html')

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile)
    return render(request, 'registration/edit_profile.html', {'form': form})

# Handle premium subscription and dummy payment submissions
@login_required
def subscribe(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        card = request.POST.get("card_number")
        expiry = request.POST.get("expiry")
        cvv = request.POST.get("cvv")
        if card and expiry and cvv:
            profile.member_status = "premium"
            profile.save()
            SubscriptionTransaction.objects.create(
                user=request.user,
                amount=100.00,
                valid_until=timezone.now().date() + timedelta(days=30)
            )
            return redirect("profile")
        else:
            error = "Please fill in all required fields."
            return render(request, "registration/subscribe.html", {"error": error})
    return render(request, "registration/subscribe.html")

# Display past subscription payments
@login_required
def subscription_history(request):
    transactions = SubscriptionTransaction.objects.filter(user=request.user).order_by('-transaction_date')
    return render(request, 'registration/subscription_history.html', {'transactions': transactions})

# Allow users to submit feedback
@login_required
def submit_feedback(request):
    feedback_submitted = False
    if request.method == "POST":
        form = FeedbackForm(request.POST, request.FILES)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            feedback_submitted = True
            form = FeedbackForm()
    else:
        form = FeedbackForm()
    return render(request, 'feedback/feedback.html', {'form': form, 'feedback_submitted': feedback_submitted})

@login_required
def feedback_tracker(request):
    feedback_type = request.GET.get('type', '')
    if request.user.is_staff:
        feedbacks = Feedback.objects.select_related('user').order_by('-created_at')
        if feedback_type and feedback_type in dict(Feedback.FEEDBACK_TYPE_CHOICES):
            feedbacks = feedbacks.filter(feedback_type=feedback_type)
    else:
        feedbacks = Feedback.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'feedback/feedback_tracker.html', {
        'feedbacks': feedbacks,
        'feedback_type': feedback_type,
        'FEEDBACK_TYPE_CHOICES': Feedback.FEEDBACK_TYPE_CHOICES,
    })

@require_POST
@login_required
def feedback_status_update(request, feedback_id):
    if not request.user.is_staff:
        return redirect('feedback_tracker')
    feedback = get_object_or_404(Feedback, id=feedback_id)
    status = request.POST.get('status', '')
    if status in dict(Feedback.STATUS_CHOICES):
        feedback.status = status
        feedback.save()
    return redirect('feedback_tracker')

@require_POST
@login_required
def feedback_response(request, feedback_id):
    if not request.user.is_staff:
        return redirect('feedback_tracker')
    feedback = get_object_or_404(Feedback, id=feedback_id)
    feedback.admin_response = request.POST.get('response', '').strip()
    feedback.save()
    return redirect('feedback_tracker')
