from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# User profile extension (status + profile picture)
class UserProfile(models.Model):
    STATUS_CHOICES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    member_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='free')
    profile_pic = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg', blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"

# Automatically create a profile when a new user is registered (Ref: Django official documentation on Signals)
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# Record subscription payments for premium users
class SubscriptionTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    transaction_date = models.DateField(auto_now_add=True)
    valid_until = models.DateField()

# Record feedback cases for users
class Feedback(models.Model):
    FEEDBACK_TYPE_CHOICES = [
        ('bug', 'Bug or Error'),
        ('suggestion', 'Feature Suggestion'),
        ('prompt', 'Prompt Issue'),
        ('ui', 'UI/UX Issue'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback_type = models.CharField(
        max_length=15,
        choices=FEEDBACK_TYPE_CHOICES
    )
    llm_prompt = models.TextField(blank=True, help_text="Paste the prompt you used, if relevant.")
    llm_response = models.TextField(blank=True, help_text="Paste or describe the LLM's response, if relevant.")
    description = models.TextField(help_text="Describe your feedback in detail.")
    rating = models.PositiveSmallIntegerField(default=0, help_text="Rate your experience (1 - worst, 5 - best).")
    screenshot = models.ImageField(upload_to='feedback/', blank=True, null=True)
    transcript = models.FileField(upload_to='transcripts/', blank=True, null=True, help_text="Upload your chat transcript (TXT). Do not upload sensitive information.")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress'
    )
    admin_response = models.TextField(blank=True, null=True, help_text="Admin/staff response to feedback (if any).")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback ({self.get_feedback_type_display()}) by {self.user.username}"
