from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.hashers import make_password
import datetime
from django.utils.crypto import get_random_string
import json
import hashlib
from django.core.validators import MinLengthValidator
from django.db.models import Sum
from .constants import *
from .validators import *
from django.core.exceptions import PermissionDenied

class SalesAppUser(AbstractUser):
    CUSTOMER = 1
    THEATRE_OWNER = 2
    ROLES_CHOICES = (
        (CUSTOMER, 'Customer'),
        (THEATRE_OWNER, 'Theatre Owner'),
    )
    email = models.EmailField(verbose_name='Email Address', max_length=255, validators=[validate_email])
    username = models.CharField(max_length=50, unique=True, verbose_name='Username', validators=[validate_field_nospace])
    full_name = models.CharField(max_length=100, verbose_name='Full Name', validators=[validate_field])
    is_active = models.BooleanField(default=True)
    role = models.IntegerField(choices=ROLES_CHOICES, default=CUSTOMER, verbose_name='Account type')
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ["full_name"]

    def get_full_name(self):
        return self.full_name

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        if self.role == 1:
            if not perm in customer_perm: return False
        elif self.role == 2:
            if not perm in theatre_perm: return False
        elif self.role == 3:
            if not perm in admin_perm: return False
        return True
    
    @classmethod
    def get_all_users(cls):
        return cls.objects.filter(is_active=True, role=1, is_email_verified=True).values("full_name", "username")

    @classmethod
    def get_user_by_username(cls, username):
        try:
            user = cls.objects.get(username=username)
        except SalesAppUser.DoesNotExist:
            return False
        return user

    @classmethod
    def check_if_user_is_theatre_owner(cls, user):
        if user.role == 2: return True
        return False

    @classmethod
    def archiveuser(cls, username):
        try:
            user = cls.get_user_by_username(username)
            user.is_active = False
            user.save()
        except Exception as e:
            raise e

class Theatres(models.Model):
    theatre_name = models.CharField(max_length=50, unique=True, verbose_name='Theatre Name', validators=[validate_field])
    owner = models.ForeignKey(SalesAppUser, on_delete=models.CASCADE)
    ticket_price = models.PositiveIntegerField()
    total_seats = models.PositiveIntegerField()

    def __str__(self):
        return self.theatre_name

    @classmethod
    def get_all_theatres(cls):
        return list(cls.objects.filter(owner__is_active=True).values("theatre_name", "owner__username", "id"))

    @classmethod
    def user_theatre_exists(cls, user):
        try:
            cls.get_theatre_by_user(user)
        except Theatres.DoesNotExist:
            return False
        return True

    @classmethod
    def get_theatre_by_user(cls, user):
        return cls.objects.get(owner=user)

    @classmethod
    def add_theatre(cls, theatrename, user, totalseats):
        min_seats = ApplicationSettings.get_min_seats()
        max_seats = ApplicationSettings.get_max_seats()
        ticket_price = ApplicationSettings.get_ticket_price()
        if not ((min_seats <= int(totalseats)) and (max_seats >= int(totalseats))):
            raise ValidationError(f"Total Seats must be between {min_seats} and {max_seats}")
        cls.objects.create(theatre_name=theatrename, owner=user, ticket_price=ticket_price, total_seats=totalseats)

    @classmethod
    def get_theatre(cls, theatrename):
        try:
            return cls.objects.get(theatre_name=theatrename)
        except Exception as e:
            print(e)

    @classmethod
    def get_total_sales_for_day(cls, theatre, date=None):
        if date is None: date = datetime.datetime.today()
        qs = BookingStatus.objects.filter(theatre=theatre, date = date, booking_status=2)
        total_sales = qs.aggregate(Sum('total_price'))
        total_seats_booked = qs.aggregate(Sum('total_seats_booked'))
        return total_sales["total_price__sum"], total_seats_booked["total_seats_booked__sum"]

    @classmethod
    def get_total_sales(cls, theatre):
        qs = BookingStatus.objects.filter(theatre=theatre, booking_status=2)
        total_sales = qs.aggregate(Sum('total_price'))
        total_seats_booked = qs.aggregate(Sum('total_seats_booked'))
        return total_sales["total_price__sum"], total_seats_booked["total_seats_booked__sum"]


class Movies(models.Model):
    movie_name = models.CharField(max_length=50, unique=True, verbose_name='Movie Name', validators=[validate_field])

    def __str__(self):
        return self.movie_name
    
    @classmethod
    def get_current_movies(cls):
        movie_ids = MovieTheatreStore.get_movies_currently_running()
        movies_list = [{"movie": movie["movie_name"], "id": movie["id"]} for movie in cls.objects.filter(id__in=movie_ids).values("movie_name", "id")]
        return movies_list

    @classmethod
    def get_all_movies(cls):
        # movie_ids = MovieTheatreStore.get_movies_currently_running()
        movies_list = [{"movie": movie["movie_name"], "id": movie["id"]} for movie in cls.objects.values("movie_name", "id")]
        return movies_list

    @classmethod
    def get_movie(cls, movie_name):
        return cls.objects.get(movie_name=movie_name)

class MovieTimeSlots(models.Model):
    slot_timing = models.TimeField()

    @classmethod
    def get_all_timeslots(cls):
        times_list = [{"time": slot["slot_timing"].strftime('%I:%H %p'), "id": slot["id"]} for slot in cls.objects.values("slot_timing", "id")]
        return times_list

    def save(self, *args, **kwargs):
        super(MovieTimeSlots, self).save(*args, **kwargs)


class MovieTheatreStore(models.Model):
    theatre = models.ForeignKey(Theatres, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movies, on_delete=models.CASCADE)
    date = models.DateField()
    time_slots = models.ManyToManyField(MovieTimeSlots)

    @classmethod
    def get_movie_shows(cls, theatre):
        shows_data = {}
        shows = cls.objects.filter(theatre=theatre).order_by("date").values("movie__movie_name", "theatre__theatre_name", "time_slots__slot_timing", "date")
        for show in shows:
            date = show['date'].strftime('%d %b %Y')
            movie_data = {"movie_name": show["movie__movie_name"], 
                          "time": show["time_slots__slot_timing"].strftime('%I:%M %p')}
            if date not in shows_data: shows_data[date] = []
            shows_data[date].append(movie_data)
        return shows_data

    @classmethod
    def cancelShow(cls, theatre, movie_name, date, time):
        show_cancelled = False
        date = datetime.datetime.strptime(date, "%d %b %Y")
        time = datetime.datetime.strptime(time, "%I:%M %p")
        movie = Movies.objects.get(movie_name=movie_name)
        time_slot = MovieTimeSlots.objects.get(slot_timing=time)
        qs = BookingStatus.objects.filter(theatre=theatre, date=date, movie=movie, time_slot=time_slot)
        if not qs:
            show = cls.objects.get(theatre=theatre, movie=movie, date=date)
            show.time_slots.remove(time_slot)
            if not len(show.time_slots.all()): show.delete()
            show_cancelled = True
        return show_cancelled

    @classmethod
    def add_movie_show(cls, data):
        theatre = Theatres.objects.get(owner=data['user'])
        date = datetime.datetime.strptime(data['dateSelected'], '%m/%d/%Y')
        time_slots = MovieTimeSlots.objects.filter(id__in=data['timeSelected'])
        is_present = cls.objects.filter(theatre=theatre, date=date, time_slots__in=time_slots)
        if is_present:
            raise Exception(f"Movie show is already added in the date and atleast one time given.")
        created_show = cls.objects.create(theatre=theatre, date=date, movie_id=data['movieSelected'])
        created_show.time_slots.set(time_slots)
        created_show.save()

    @classmethod
    def get_movies_currently_running(cls):
        return list(cls.objects.values_list("movie_id", flat=True))

    @classmethod
    def get_theatres(cls, movie_id):
        try:
            theatre_json = {}
            today = datetime.datetime.today()
            endDate = today + datetime.timedelta(days=30) # TODO: Change to 5
            qs = MovieTheatreStore.objects.filter(date__range=[today, endDate],movie_id = movie_id).order_by("date").values("theatre__theatre_name", "time_slots__slot_timing", "date")
            for entry in qs:
                date = entry['date'].strftime('%d %b %Y')
                if not date in theatre_json: 
                    theatre_json[date] = {entry["theatre__theatre_name"]: [entry["time_slots__slot_timing"].strftime('%I:%M %p')]}
                else:
                    if entry["theatre__theatre_name"] not in theatre_json[date]:
                        theatre_json[date][entry["theatre__theatre_name"]] = [entry["time_slots__slot_timing"].strftime('%I:%M %p')]
                    else:
                        theatre_json[date][entry["theatre__theatre_name"]].append(entry["time_slots__slot_timing"].strftime('%I:%M %p'))
            return theatre_json
        except Exception as e:
            raise e
        

    def __str__(self):
        return f'{self.movie.movie_name} -> {self.theatre.theatre_name}'

class ApplicationSettings(models.Model):
    ticket_price = models.PositiveIntegerField()
    min_seats = models.PositiveIntegerField()
    max_seats = models.PositiveIntegerField()

    @classmethod
    def get_ticket_price(cls):
        return cls.objects.last().ticket_price

    @classmethod
    def get_min_seats(cls):
        return cls.objects.last().min_seats

    @classmethod
    def get_max_seats(cls):
        return cls.objects.last().max_seats

    @classmethod
    def save_settings(cls, data):
        try:
            settings = cls.objects.last()
            if not settings: raise Exception
            settings.ticket_price = data["ticket_price"]
            settings.min_seats = data["min_seats"]
            settings.max_seats = data["max_seats"]
            settings.save()
        except Exception as e:
            cls.objects.create(ticket_price = data["ticket_price"], min_seats = data["min_seats"], max_seats = data["max_seats"])

class BookingStatus(models.Model):
    IN_PROGRESS = 1
    SUCCESS = 2
    BOOKING_CHOICES = (
        (IN_PROGRESS, 'In Progress'),
        (SUCCESS, 'Success'),
    )
    booking_id = models.CharField(max_length=100, primary_key=True, validators=[validate_field])
    movie = models.ForeignKey(Movies, on_delete=models.CASCADE)
    theatre = models.ForeignKey(Theatres, on_delete=models.CASCADE)
    user = models.ForeignKey(SalesAppUser, on_delete=models.CASCADE)
    booking_status = models.IntegerField(choices=BOOKING_CHOICES, default=IN_PROGRESS)
    total_seats_booked = models.PositiveIntegerField()
    seats_booked = models.CharField(max_length=1000)
    booking_date = models.DateField(auto_now_add=True)
    date = models.DateField()
    time_slot = models.ForeignKey(MovieTimeSlots, on_delete=models.CASCADE)
    total_price = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.theatre.theatre_name} -> {self.user.username}'

    def save(self, *args, **kwargs):
        self.booking_id = get_random_string(length=32)
        return super(BookingStatus, self).save(*args, **kwargs)

    @classmethod
    def get_available_seats(cls, data):
        seat_data = {
            "seates_booked": [],
            "total_seats_available": 0
        }
        theatre = Theatres.get_theatre(data["theatre_name"])
        time_slot = MovieTimeSlots.objects.get(slot_timing=datetime.datetime.strptime(data["time"], "%I:%M %p"))
        date = datetime.datetime.strptime(data["date"], "%d %b %Y")
        qs = cls.objects.filter(theatre=theatre, date=date, time_slot=time_slot, booking_status__in=[1,2])
        seat_data["total_seats_available"] = theatre.total_seats
        if qs:
            for booking in qs:
                seats_booked = json.loads(booking.seats_booked)
                seat_data["seates_booked"] = seat_data["seates_booked"] + seats_booked
        return seat_data

    @classmethod
    def create_booking_status(cls, data):
        movie = Movies.get_movie(data["movieName"])
        theatre = Theatres.objects.get(theatre_name=data["theatreName"])
        total_seats_booked = len(data["selected_seats"])
        time_slot = MovieTimeSlots.objects.get(slot_timing=datetime.datetime.strptime(data["time_slot"], "%I:%M%p"))
        date = datetime.datetime.strptime(data["date"], "%d %b %Y")
        
        return cls.objects.create(movie=movie, theatre=theatre, user=data["user"], booking_status=1, 
        total_seats_booked=total_seats_booked,
        seats_booked=data["selected_seats"], date=date, time_slot=time_slot, total_price=data["ticket_price"])

    @classmethod
    def get_booking_details(cls, bookingid, user):
        booking = cls.objects.get(booking_id=bookingid)
        if(user.id != booking.user.id): raise PermissionDenied
        return BookingStatus.objects.filter(booking_id=bookingid).values("movie__movie_name", "theatre__theatre_name", 
        "seats_booked", "user__username", "date", "time_slot__slot_timing", "total_price", "booking_status")[0]

    @classmethod
    def confirm_booking(cls, bookingid):
        qs = BookingStatus.objects.filter(booking_id=bookingid, booking_status=2)
        if not qs: BookingStatus.objects.filter(booking_id=bookingid).update(booking_status=cls.SUCCESS)
        else: raise Exception("There is a problem while booking ticket. This booking might have already been confirmed. Are you an attacker?")

    @classmethod
    def purchase_history(cls, user):
        current_date = datetime.datetime.today()
        active_tickets = list(cls.objects.filter(date__gte=current_date, user=user).values("movie__movie_name", "theatre__theatre_name", 
        "seats_booked", "user__username", "date", "time_slot__slot_timing", "total_price"))
        past_tickets = list(cls.objects.filter(date__lt=current_date, user=user).values("movie__movie_name", "theatre__theatre_name", 
        "seats_booked", "user__username", "date", "time_slot__slot_timing", "total_price"))

        for ticket in active_tickets:
            ticket["date"] = ticket["date"].strftime('%d %b %Y')
            ticket["time_slot__slot_timing"] = ticket["time_slot__slot_timing"].strftime('%I:%M%p')

        for ticket in past_tickets:
            ticket["date"] = ticket["date"].strftime('%d %b %Y')
            ticket["time_slot__slot_timing"] = ticket["time_slot__slot_timing"].strftime('%I:%M%p')
        return {"active_tickets": active_tickets, "past_tickets": past_tickets}

class UserPaymentInformation(models.Model):
    cardnumber = models.CharField(max_length=16, validators=[MinLengthValidator(16)])
    cvv = models.CharField(max_length=3, validators=[MinLengthValidator(3)])
    expiry = models.CharField(max_length=5, validators=[validate_field])
    user = models.ForeignKey(SalesAppUser, on_delete=models.CASCADE)

    @classmethod
    def get_payment_details(cls, user):
        return cls.objects.filter(user=user).values("cardnumber", "expiry")[0]

    @classmethod
    def payment_details_exist(cls, user):
        try:
            cls.objects.get(user=user)
        except UserPaymentInformation.DoesNotExist:
            return False
        return True

    @classmethod
    def create_payment_info(cls, data, user):
        try:
            cls.objects.get(user=user)
        except UserPaymentInformation.DoesNotExist:
            cardnumber = data['cardnumber'][-4:]
            cvv = hashlib.sha256(data['cvv'].encode('utf-8')).hexdigest()
            expiry = data['expiry']
            UserPaymentInformation.objects.create(cardnumber=cardnumber, cvv=cvv, expiry=expiry, user=user)

        


