from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from .forms import *
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import *
from .tokens import account_activation_token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib import messages
from typing import Protocol
from django.contrib.sites.shortcuts import get_current_site
from django.http import JsonResponse
from .decorators import *
import json
import logging
from .validators import *
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def customerHome(request):
    try:
        logger.debug('Entered customer home..')
        logger.debug(f'Logged in user {request.user.username}')
        logger.debug(f'Fetching movies')
        movies_list = Movies.get_current_movies()
        data = {
            "movies_list": movies_list
        }
        logger.debug(f'Movies list {movies_list}')
    except Exception as e:
        logger.debug("Error during fetching movies")
    return render(request, 'customer/customer_home.html', data)

@login_required(login_url='/salesapp/login/')
@csrf_exempt
def genericHome(request):
    try:
        user = request.user
        if user.role == 1: return redirect("/salesapp/customerhome")
        elif user.role == 2: return redirect("/salesapp/theatrehome")
        elif user.role == 3: return redirect("/salesapp/viewtheatres")
    except Exception as e:
        raise e

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def getTheatres(request):
    data = {}
    data["status"] = True
    data["msg"] = ""
    try:
        logger.debug('Entered getTheatres')
        logger.debug(f'Logged in user {request.user.username}')
        logger.debug(f'Fetching Theatres')
        if request.method == 'POST':
            movie_id = request.POST["movie_id"]
            data["dates"] = MovieTheatreStore.get_theatres(movie_id)
            logger.debug(f'Theatres list {data["dates"]}')
    except Exception as e:
        data["status"] = False
        data["msg"] = str(e)
        logger.debug("Error during fetching theatres")
    return JsonResponse(data)

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def theatreHome(request):
    try:
        logger.debug('Entered theatreHome')
        logger.debug(f'Logged in user {request.user.username}')
        logger.debug(f'Fetching Theatres')
        user = request.user
        theatre_added = Theatres.user_theatre_exists(user)
        movies_list = []
        time_slots = []
        theatre_name = ""
        if theatre_added:
            movies_list = Movies.get_all_movies()
            time_slots = MovieTimeSlots.get_all_timeslots()
            theatre_name = Theatres.get_theatre_by_user(user).theatre_name
        data = {
            "theatre_added": theatre_added,
            "movies_list": movies_list,
            "time_slots": time_slots,
            "theatre_name": theatre_name
        }
        logger.debug(f'Sending data to browser {data}')
    except Exception as e:
        logger.debug("Error during formatting the movies and theatres list")
    return render(request, 'theatre/theatre_home.html', data)

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def addTheatre(request):
    try:
        logger.debug('Entered addTheatre')
        logger.debug(f'Logged in user {request.user.username}')
        user = request.user
        if request.method == "POST":
            theatrename = request.POST["theatrename"]
            validate_field(theatrename, "Theatre Name")
            totalseats = request.POST["totalseats"]
            validate_number_field(totalseats, "Total Seats")
            Theatres.add_theatre(theatrename, user, totalseats)
            logger.debug('Theatre added successfully.')
            messages.success(request, f'Theatre added successfully.')
    except ValidationError as e:
        logger.debug(f"Invalid characters found. {str(e)}")
        messages.error(request, f'{str(e)}')
    except Exception as e:
        logger.debug(f"Problem adding the theatre. {str(e)}")
        messages.error(request, f'Problem adding the theatre.')
    return redirect('/salesapp/theatrehome')

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def addMovieShow(request):
    try:
        logger.debug('Entered addMovieShow')
        logger.debug(f'Logged in user {request.user.username}')
        user = request.user
        is_theatre_owner = SalesAppUser.check_if_user_is_theatre_owner(user)
        if not is_theatre_owner: raise Exception
        elif request.method == "POST":
            movieSelected = request.POST["movieSelected"]
            validate_field(movieSelected, "Theatre Name")
            dateSelected = request.POST["dateSelected"]
            validate_date(dateSelected)
            timeSelected = request.POST.getlist('timeSelected')
            validate_number_field(''.join(timeSelected), "Time", "Please select a time from the options")
            data = {
                "movieSelected": movieSelected,
                "dateSelected": dateSelected,
                "timeSelected": timeSelected,
                "user": user,
            }
            MovieTheatreStore.add_movie_show(data)
            logger.debug('Movie Show Added')
            messages.success(request, "Movie Show Added")
    except ValidationError as e:
        logger.debug(f"Invalid characters found. {str(e)}")
        messages.error(request, f'{str(e)}')
    except Exception as e:
        logger.debug(f"Unable to movie show. {str(e)}")
        messages.error(request, "Unable to movie show. Movie show may have been already added in the date and atleast one time given.")
    return redirect('/salesapp/theatrehome')

@csrf_exempt
def userLogin(request):
    try:
        username = request.POST['username']
        password = request.POST['password']
        logger.debug('Entered login')
        logger.debug(f'Given username {username}')
        user = SalesAppUser.get_user_by_username(username)
        if not user:
            logger.debug(f'User not found during login. Username: {username}')
            messages.error(request, "User doesn't exist. Please create an account.")
            return redirect('/salesapp/login/')
        logger.debug(f'User found during login. Username: {username}')
        if user.is_email_verified:
            logger.debug(f'User email address is verified. Proceeding with authentication. Username: {username}')
            check_auth = authenticate(request, username=username, password=password)
            if check_auth:
                logger.debug(f'Given user credentials are correct. Creating session for user with username: {username}')
                login(request, user)
                if user.role == 2: return redirect('/salesapp/theatrehome')
                if user.role == 3: return redirect('/salesapp/viewtheatres')
                return redirect('/salesapp')
            else:
                logger.debug(f'Given user credentials are incorrect. Username: {username}')
                messages.error(request, "Username and Password combination is incorrect. Please try again!")
                return redirect('/salesapp/login/')
        else:
            logger.debug(f'User email address is not verified. Blocking the user from login. Username: {username}')
            messages.error(request, "Please verify your email before sign in.")
            return redirect('/salesapp/login/')
    except Exception as e:
        logger.debug(f'Error during login. Application might be down. Trying to redirect to login page...')
        messages.error(request, "Error during login.")
        return redirect('/salesapp/login/')

@csrf_exempt
def userSignUp(request):
    try:
        logger.debug('Entered signup')
        if request.method == "POST":
            form = RegisterForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.set_password(request.POST["password"])
                user.is_email_verified = True
                user.save()
                # activateEmail(request, user, form.cleaned_data.get('email'))
                return redirect('/salesapp/login/')
        else:
            form = RegisterForm()
    except ValidationError as e:
        logger.debug("Error during signup.")
        messages.error(request, "Please correct the errors in form.")
    except Exception as e:
        messages.error(request, "Error during signup.")
        logger.debug(f"Error during user sign up {str(e)}")
    return render(request, 'registration/sign_up.html', {"form": form})

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def changeUserProfile(request):
    try:
        logger.debug("Entered change user profile")
        if request.method == "POST":
            form = UpdateUserForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                form = UpdateUserForm(instance=request.user)
                messages.success(request, "Profile Updated Successfully!!")
        else:    
            form = UpdateUserForm(instance=request.user)
    except Exception as e:
        logger.debug(f"Error during fetch user details {str(e)}")
        messages.error(request, "Unable to fetch user details. Please try again!")
    return render(request, 'updateProfile.html', {"form": form})

def activateEmail(request, user, to_email):
    try:
        logger.debug("Entered activate email")
        mail_subject = "Activate your user account."
        message = render_to_string("registration/activate_account.html", {
            'user': user.username,
            'domain': get_current_site(request).domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
            "protocol": 'https' if request.is_secure() else 'http'
        })
        email = EmailMessage(mail_subject, message, to=[to_email])
        if email.send():
            messages.success(request, f'Dear <b>{user}</b>, please go to you email <b>{to_email}</b> inbox and click on \
                    received activation link to confirm and complete the registration. <b>Note:</b> Check your spam folder.')
        else:
            messages.error(request, f'Problem sending email to {to_email}, check if you typed it correctly.')
    except Exception as e:
        logger.debug(f"Error during processing email activation {str(e)}")

def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is not None:
        if user.is_email_verified:
            return render(request, 'registration/email_confirmation.html', {"msg": "Token is invalid and already used for verification"})
        elif account_activation_token.check_token(user, token):
            user.is_email_verified = True
            user.save()
            return render(request, 'registration/email_confirmation.html', {"msg": "Thank you for your email confirmation. Now you can login to your account."})
        else:
            return render(request, 'registration/email_confirmation.html', {"msg": "Token is invalid."})
    else:
        return render(request, 'registration/email_confirmation.html', {"msg": "Token is invalid."})

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def getAvailableSeats(request):
    seats_availability_data = {}
    try:
        logger.debug("Entered getAvailableSeats")
        data = {}
        if request.method == 'POST':
            data["theatre_name"] = request.POST["theatreName"]
            data["date"] = request.POST["date"]
            data["time"] = request.POST["time_slot"]
            seats_availability_data = BookingStatus.get_available_seats(data)
    except Exception as e:
        logger.debug(f"Error while processing request {str(e)}")
    return JsonResponse(seats_availability_data)

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def initiateBooking(request):
    json_rep = {"status": True, "msg": ""}
    try:
        booking_data = json.loads(request.POST["booking_data"])
        if not UserPaymentInformation.payment_details_exist(request.user):
            json_rep["status"] = False
            json_rep["msg"] = "Payment details. Please update payment details from Payment Information page"
        else:
            data={
                "movieName": booking_data["movieName"],
                "theatreName": booking_data["theatreName"],
                "date": booking_data["date"],
                "selected_seats": booking_data["selected_seats"],
                "time_slot": booking_data["time_slot"],
                "ticket_price": ApplicationSettings.get_ticket_price() * len(booking_data["selected_seats"]),
                "user": request.user
            }
            booking_status = BookingStatus.create_booking_status(data)
            json_rep["booking_status_id"] = booking_status.booking_id
    except Exception as e:
        logger.debug("Error during initiate booking")
        json_rep["status"] = False
        json_rep["msg"] = "Error while booking the seats. Please try again"
    return JsonResponse(json_rep)

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def bookingSummary(request, bookingid):
    logger.debug("Entered booking summary")
    booking_details = {}
    try:
        user = request.user
        logger.debug(f"Booking seats for user {user.username}")
        booking_details = BookingStatus.get_booking_details(bookingid, user)
        logger.debug(f"Fetched booking details {booking_details}")
        if booking_details["booking_status"] == 2:
            booking_details = {}
            booking_details["booking_status"] = 2
        else:
            booking_details["time_slot__slot_timing"] = booking_details["time_slot__slot_timing"].strftime("%I:%M %p")
            booking_details["date"] = booking_details["date"].strftime("%d %b %Y")
            seats_booked_list = json.loads(booking_details["seats_booked"])
            booking_details["seats_booked"] = ",".join(str(x) for x in seats_booked_list)
            booking_details["bookingid"] = bookingid
        logger.debug(f"Returning response for booking summary {booking_details}")
    except Exception as e:
        logger.debug(f"Error during booking summary. Error: {str(e)}")
    return render(request, 'customer/booking_summary.html', booking_details)

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def confirmBooking(request):
    try:
        logger.debug("Entered confirmBooking")
        bookingid = request.POST["bookingid"]
        BookingStatus.confirm_booking(bookingid)
        logger.debug(f"Confirmed booking for booking ID {bookingid}")
        status = True
        message = "Ticket Booked!"
    except Exception as e:
        status = False
        message = str(e)
        logger.debug(f"An error encountered while confirming the booking. {str(e)}")
    return JsonResponse({"status": status, "message": message})

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def purchasehistory(request):
    try:
        logger.debug("Entered purchasehistory")
        username = request.POST.get("username", None)
        template = request.POST.get("template", 'customer/booking_history.html')
        user = request.user
        if username: user = SalesAppUser.get_user_by_username(username)
        history_details = BookingStatus.purchase_history(user)
    except Exception as e:
        messages.error(request, str(e))
        logger.debug(f"An error encountered while fetching purchase history. {str(e)}")
    return render(request, template, history_details)

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def userPaymentInfo(request):
    try:
        logger.debug("Entered the method userPaymentInfo")
        data = {"payment_details_exist": False}
        if request.method == "POST":
            form = UserPaymentDetails(request.POST, instance=request.user)
            data["form"] = form
            if form.is_valid():
                UserPaymentInformation.create_payment_info(form.cleaned_data, form.instance)
                messages.success(request, "Payment information saved")
                return redirect('/salesapp/customerhome')
        else:
            if UserPaymentInformation.payment_details_exist(request.user):
                data["payment_details_exist"] = True
                data["payment_details"] = UserPaymentInformation.get_payment_details(request.user)
            else:
                data["form"] = UserPaymentDetails()
    except Exception as e:
        logger.debug(f"An error encountered while userPaymentInfo. {str(e)}")
    return render(request, 'customer/user_payment_info.html', data)

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def viewticketsales(request):
    try:
        # Theatre owner can only access
        data = {}
        theatre = Theatres.get_theatre_by_user(request.user)
        data["current_day_sales"], data["current_day_total_seats_booked"] = Theatres.get_total_sales_for_day(theatre)
        data["total_sales"], data["total_seats_booked"] = Theatres.get_total_sales(theatre)
    except Theatres.DoesNotExist:
        messages.error(request, f'Theatre is not added.')
    except Exception as e:
        messages.error(request, f'Unable to fetch sales data. Please try again!')
    return render(request, 'theatre/total_sales.html', data)

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def viewticketsalesondate(request):
    # Theatre owner can only access
    date_selected = request.POST["date_selected"]
    data = {}
    theatre = Theatres.get_theatre_by_user(request.user)
    date_selected = datetime.datetime.strptime(date_selected, "%m/%d/%Y")
    data["current_day_sales"], data["current_day_total_seats_booked"] = Theatres.get_total_sales_for_day(theatre, date_selected)
    data["total_sales"], data["total_seats_booked"] = Theatres.get_total_sales(theatre)
    return JsonResponse(data)

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def viewtheatres(request):
    # Admin user can only access
    user = request.user
    theatres_list = Theatres.get_all_theatres()
    return render(request, 'admin/admin_home.html', {"theatres_list": theatres_list})

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def viewticketsalesadmin(request):
    # Admin user can only access
    date_selected = request.POST["date_selected"]
    theatre_name = request.POST["theatre_name"]
    data = {}
    theatre = Theatres.get_theatre(theatre_name)
    date_selected = datetime.datetime.strptime(date_selected, "%m/%d/%Y")
    data["current_day_sales"], data["current_day_total_seats_booked"] = Theatres.get_total_sales_for_day(theatre, date_selected)
    data["total_sales"], data["total_seats_booked"] = Theatres.get_total_sales(theatre)
    return JsonResponse(data)

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def viewcustomers(request):
    # Admin user can only access
    data = {}
    data["users"] = list(SalesAppUser.get_all_users())
    return render(request, 'admin/customer_list.html', data)

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def appsettings(request):
    if request.method == "POST":
        form = ApplicationSettingsForm(request.POST)
        if form.is_valid():
            ApplicationSettings.save_settings(form.cleaned_data)
            messages.success(request, "Settings saved!")
            form = ApplicationSettingsForm()
    else:
        form = ApplicationSettingsForm()
    return render(request, 'admin/app_settings.html', {"form": form})


@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def viewshows(request):
    shows = {}
    try:
        user = request.user
        theatre = Theatres.get_theatre_by_user(user)
        shows = MovieTheatreStore.get_movie_shows(theatre)
    except Theatres.DoesNotExist:
        messages.error(request, f'Please add a theatre')
        logger.debug("Theatre is not added but user is viewing shows")
    except Exception as e:
        messages.error(request, f'Unable to get the current shows. Please try again!')
        logger.debug(f"Unable to process request viewshows {str(e)}")
    return render(request, 'theatre/view_shows.html', {"shows": shows}) 

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def cancelshow(request):
    isShowCancelled = False
    try:
        logger.debug("Entered cancelshow")
        logger.debug(f"Logged in user {request.user.username}")
        user = request.user
        movie_name = request.POST["movie_name"]
        time = request.POST["time"]
        date = request.POST["date"]
        theatre = Theatres.get_theatre_by_user(user)
        isShowCancelled = MovieTheatreStore.cancelShow(theatre, movie_name, date, time)
        if not isShowCancelled: 
            logger.debug(f'Cannot cancel the show as the seats are already booked!')
    except Exception as e:
        logger.debug(f'Cannot cancel the show! {str(e)}')
    return JsonResponse({"isShowCancelled": isShowCancelled})

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def addmovie(request):
    if request.method == "POST":
        form = AddMovieForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Movie Added successfully!")
    else:
        form = AddMovieForm()
    return render(request, 'admin/add_movie.html', {"form": form})

@login_required(login_url='/salesapp/login/')
@check_perm
@csrf_exempt
def archiveuser(request):
    try:
        logger.debug("Entered archiveuser method")
        logger.debug(f"User accessed: {request.user.username}")
        data = {}
        data["status"] = True
        data["msg"] = ""
        if request.method == "POST":
            username = request.POST["username"]
            SalesAppUser.archiveuser(username)
            data["msg"] = f"User {username} is archived successfully!"
        else:
            data["status"] = False
            data["msg"] = f"Unable to archive the user {username}"
            logger.debug(f"Unable to archive the user {username}. Reason: Request not a post method")
    except Exception as e:
        data["status"] = False
        data["msg"] = f"Unable to archive the user {username}"
        logger.debug(f"Unable to archive the user {username}. Reason: {str(e)}")
    return JsonResponse(data)

def csrf_failure(request, reason=""):
    ctx = {'message': 'Another user is already logged in.'}
    return render(request, 'csrf_failure.html', {"ctx": ctx}) 
    

