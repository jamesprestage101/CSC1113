from django.contrib import sitemaps
from django.contrib.sitemaps.views import sitemap
from django.urls import path
from . import views
from .views import *

# Our sitemap using Django sitemap framework
class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return [
            'chat',
            'register',
            'login',
            'logout',
            'profile',
            'edit_profile',
            'subscribe',
            'subscription_history',
            'feedback',
            'feedback_tracker',
        ]

    def location(self, item):
        from django.urls import reverse
        return reverse(item)

sitemaps_dict = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('', views.index, name='index'),
    path('chat/', views.chat, name='chat'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('register/', UserSignupView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', logout_user, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('edit-profile/', edit_profile, name='edit_profile'),
    path('subscribe/', subscribe, name='subscribe'),
    path('subscription_history/', subscription_history, name='subscription_history'),
    path('feedback/', views.submit_feedback, name='feedback'),
    path('feedback-tracker/', views.feedback_tracker, name='feedback_tracker'),
    path('feedback/update-status/<int:feedback_id>/', views.feedback_status_update, name='feedback_status_update'),
    path('feedback/response/<int:feedback_id>/', views.feedback_response, name='feedback_response'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps_dict}, name='django.contrib.sitemaps.views.sitemap'),
]