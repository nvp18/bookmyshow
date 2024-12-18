from django.core.management.base import BaseCommand, CommandError
from salesapp.models import SalesAppUser

class Command(BaseCommand):
    help = 'Creating Admin user'

    def handle(self, *args, **options):
        print(">>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<")
        print("Creating admin user......")
        username = "admin"
        full_name = "Administrator"
        email="admin@admin.com"

        admin_user = SalesAppUser.objects.create(username=username, email=email, 
        is_email_verified=True, role=3, full_name=full_name)
        admin_user.set_password("")
        admin_user.save()

        print("Admin user created.......")
        print(">>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<")
        
