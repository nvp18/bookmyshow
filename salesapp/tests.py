from django.test import SimpleTestCase
from django.urls import reverse, resolve
from .views import *
from django.test import TestCase, Client
from .models import *
import json
import random, string
 
class TestUrls(SimpleTestCase):
 
    # Checking if urls are hitting the current view method
    def test_customerHome_url_is_resolved(self):
        url = reverse('customerHome')
        self.assertEquals(resolve(url).func, customerHome)
 
    def test_theatrehome_url_is_resolved(self):
        url = reverse('theatreHome')
        self.assertEquals(resolve(url).func, theatreHome)
 
    def test_changeUserProfile_url_is_resolved(self):
        url = reverse('changeUserProfile')
        self.assertEquals(resolve(url).func, changeUserProfile)

    def test_addTheatre_url_is_resolved(self):
        url = reverse('addTheatre')
        self.assertEquals(resolve(url).func, addTheatre)
    
    def test_addMovieShow_url_is_resolved(self):
        url = reverse('addMovieShow')
        self.assertEquals(resolve(url).func, addMovieShow)

    def test_getTheatres_url_is_resolved(self):
        url = reverse('getTheatres')
        self.assertEquals(resolve(url).func, getTheatres)

    def test_userPaymentInfo_url_is_resolved(self):
        url = reverse('userPaymentInfo')
        self.assertEquals(resolve(url).func, userPaymentInfo)

    def test_getAvailableSeats_url_is_resolved(self):
        url = reverse('getAvailableSeats')
        self.assertEquals(resolve(url).func, getAvailableSeats)

    def test_confirmBooking_url_is_resolved(self):
        url = reverse('confirmBooking')
        self.assertEquals(resolve(url).func, confirmBooking)

    def test_bookingSummary_url_is_resolved(self):
        url = reverse('bookingSummary', args=('h'))
        self.assertEquals(resolve(url).func, bookingSummary)

    def test_viewticketsales_url_is_resolved(self):
        url = reverse('viewticketsales')
        self.assertEquals(resolve(url).func, viewticketsales)

    def test_viewticketsalesondate_url_is_resolved(self):
        url = reverse('viewticketsalesondate')
        self.assertEquals(resolve(url).func, viewticketsalesondate)

    def test_viewtheatres_url_is_resolved(self):
        url = reverse('viewtheatres')
        self.assertEquals(resolve(url).func, viewtheatres)

    def test_viewticketsalesadmin_url_is_resolved(self):
        url = reverse('viewticketsalesadmin')
        self.assertEquals(resolve(url).func, viewticketsalesadmin)

    def test_viewcustomers_url_is_resolved(self):
        url = reverse('viewcustomers')
        self.assertEquals(resolve(url).func, viewcustomers)
    
    def test_appsettings_url_is_resolved(self):
        url = reverse('appsettings')
        self.assertEquals(resolve(url).func, appsettings)

    def test_viewshows_url_is_resolved(self):
        url = reverse('viewshows')
        self.assertEquals(resolve(url).func, viewshows)

    def test_cancelshow_url_is_resolved(self):
        url = reverse('cancelshow')
        self.assertEquals(resolve(url).func, cancelshow)

    def test_addmovie_url_is_resolved(self):
        url = reverse('addmovie')
        self.assertEquals(resolve(url).func, addmovie)
    
    def test_archiveuser_url_is_resolved(self):
        url = reverse('archiveuser')
        self.assertEquals(resolve(url).func, archiveuser)

class TestModels(TestCase):
 
    def setUp(self):
        self.user1 = SalesAppUser.objects.create(
            username = 'Sri',
            email = 'asd@asd.com',
            full_name = 'Sri',
            role = 1,
            is_email_verified = 0,
        )

        self.user1.set_password("asdfg")
        self.user1.save()

        self.credentials = {'username': 'Sri','password': 'asdfg'}
    
    def test_login(self):
        # trying to login with self.user1 where email is not verified. Login must fail
        response = self.client.post('/salesapp/login', self.credentials, follow=True)
        self.assertFalse(response.context['user'].is_active)
 
    # def test_food_is_assigned_on_creation(self):
    #     self.assertEquals(self.food1.dish_name, 'Cake')
    #     self.assertEquals(self.food1.dish_description, 'dessert')
    #     self.assertEquals(self.food1.dish_price, 15)
 
    # def test_user_is_assigned_on_creation(self):
    #     self.assertEquals(self.user.full_name, 'Aparna')
    #     self.assertEquals(self.user.username, 'aparna53')
    #     self.assertEquals(self.user.email, 'email@email.com')
    #     self.assertEquals(self.user.address, 'gh')
    #     self.assertEquals(self.user.contact_number, 789)
    #     self.assertEquals(self.user.role, 1)
 
    # def test_table_is_assigned_on_creation(self):
    #     self.assertEquals(self.table.table_type, '2 seater')
    #     self.assertEquals(self.table.status, 'available')
