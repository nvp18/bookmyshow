from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import SalesAppUser

admin.site.register(SalesAppUser, UserAdmin)
