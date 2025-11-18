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
# This can be done by an individual or on their behalf by an organisation admin
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

# Allow users to view their feedback and allows admins to respond to feedback
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

# Allows users to create/join/manage organisations
@login_required
def create_organisation(request):
    if OrganisationMembership.objects.filter(user=request.user).exists():
        return redirect('profile')
    if request.method == 'POST':
        form = OrganisationCreateForm(request.POST)
        if form.is_valid():
            org = form.save(commit=False)
            org.created_by = request.user
            org.save()
            OrganisationMembership.objects.create(user=request.user, organisation=org, role='admin')
            return redirect('organisation_dashboard', org.id)
    else:
        form = OrganisationCreateForm()
    return render(request, 'organisations/create_org.html', {'form': form})

@login_required
def join_organisation(request):
    if OrganisationMembership.objects.filter(user=request.user).exists():
        return redirect('profile')
    if request.method == 'POST':
        form = OrganisationJoinForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code'].strip().upper()
            try:
                org = Organisation.objects.get(code=code)
                OrganisationMembership.objects.create(user=request.user, organisation=org, role='member')
                return redirect('organisation_dashboard', org.id)
            except Organisation.DoesNotExist:
                form.add_error('code', 'Invalid code.')
            except Exception:
                form.add_error('code', 'You are already a member of an organisation.')
    else:
        form = OrganisationJoinForm()
    return render(request, 'organisations/join_org.html', {'form': form})

@login_required
def organisation_dashboard(request, org_id):
    org = get_object_or_404(Organisation, id=org_id)
    try:
        user_membership = OrganisationMembership.objects.get(user=request.user)
        if user_membership.organisation.id != org.id:
            return redirect('profile')
    except OrganisationMembership.DoesNotExist:
        return redirect('profile')
    memberships = OrganisationMembership.objects.filter(organisation=org).select_related('user', 'user__userprofile')
    return render(request, 'organisations/org_dashboard.html', {
        'organisation': org,
        'memberships': memberships,
        'user_membership': user_membership,
    })

@login_required
def remove_member(request, org_id, user_id):
    org = get_object_or_404(Organisation, id=org_id)
    admin_membership = get_object_or_404(OrganisationMembership, user=request.user, organisation=org, role='admin')
    target_member = get_object_or_404(OrganisationMembership, organisation=org, user__id=user_id)
    if target_member.user != request.user:
        target_member.delete()
    return redirect('organisation_dashboard', org_id)

@login_required
def subscribe(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    error = message = None
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
            message = "You have been upgraded to premium!"
        else:
            error = "Please fill in all required fields."
    return render(request, "registration/subscribe.html", {
        "error": error,
        "message": message,
        "member": None,
        "admin_upgrading": False
    })

@login_required
def admin_subscribe_member(request, org_id, user_id):
    org = get_object_or_404(Organisation, id=org_id)
    admin_membership = get_object_or_404(OrganisationMembership, user=request.user, organisation=org, role='admin')
    member = get_object_or_404(User, id=user_id)
    member_profile = get_object_or_404(UserProfile, user=member)
    if member == request.user:
        return redirect('subscribe')
    message = error = None
    if request.method == "POST":
        card = request.POST.get("card_number")
        expiry = request.POST.get("expiry")
        cvv = request.POST.get("cvv")
        if card and expiry and cvv:
            member_profile.member_status = "premium"
            member_profile.save()
            SubscriptionTransaction.objects.create(
                user=member,
                amount=100.00,
                valid_until=timezone.now().date() + timedelta(days=30)
            )
            message = f"{member.username} has been upgraded to premium."
        else:
            error = "Please fill in all required fields."
    return render(request, "registration/subscribe.html", {
        "error": error,
        "message": message,
        "member": member,
        "admin_upgrading": True,
    })