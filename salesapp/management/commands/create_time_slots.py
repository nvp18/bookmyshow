from django.core.management.base import BaseCommand, CommandError
from salesapp.models import MovieTimeSlots
import datetime

class Command(BaseCommand):
    help = 'Creating Time slots for movies'

    def handle(self, *args, **options):
        print(">>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<")
        print("Creating time slots for movies......")


        slot_1 = datetime.datetime.strptime("12:00 AM", "%I:%M %p")
        slot_2 = datetime.datetime.strptime("03:00 PM", "%I:%M %p")
        slot_3 = datetime.datetime.strptime("06:00 PM", "%I:%M %p")
        slot_4 = datetime.datetime.strptime("09:00 PM", "%I:%M %p")
        MovieTimeSlots.objects.create(slot_timing=slot_1)
        MovieTimeSlots.objects.create(slot_timing=slot_2)
        MovieTimeSlots.objects.create(slot_timing=slot_3)
        MovieTimeSlots.objects.create(slot_timing=slot_4)

        print("Movie time slots created.......")
        print(">>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<")
        