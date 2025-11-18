from django.contrib import admin
from .models import *

admin.site.register(UserProfile)
admin.site.register(SubscriptionTransaction)
admin.site.register(Feedback)
admin.site.register(Organisation)
admin.site.register(OrganisationMembership)