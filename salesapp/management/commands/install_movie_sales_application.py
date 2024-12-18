from django.core.management.base import BaseCommand, CommandError
from salesapp.models import *

from django.core.management import call_command

class Command(BaseCommand):
    help = 'Creating Admin user'

    def handle(self, *args, **options):

        print("Installing MovieTicketSalesApplication.......")

        print("Creating Database Tables....")

        print("Applying Migrations")

        call_command('migrate')

        print("Completed creating DB Tables")

        call_command('create_admin_user')

        call_command('create_time_slots')
        