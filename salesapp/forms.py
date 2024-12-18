from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password
from .models import *
import re
from .validators import *


User = get_user_model()

alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    username = forms.CharField(max_length=50, validators=[alphanumeric])

    class Meta:
        model = User
        fields = ["username", "full_name", "email","role", "password", "password_2"]

    def clean(self):
        cleaned_data = super().clean()
        # verify 
        # verify email is unique
        email = self.cleaned_data.get('email')
        qs = User.objects.filter(email=email)
        if qs.exists(): self.add_error("email", "There is another account with the given email id.")

        if int(cleaned_data.get("role")) not in [1,2]: self.add_error("role", "Please select theatre owner or customer")

        # verify matching of passwords
        password = cleaned_data.get("password")
        password_2 = cleaned_data.get("password_2")
        if password is not None and password != password_2:
            self.add_error("password_2", "Your passwords must match")
        # validate_password(password)
        return cleaned_data

class UpdateUserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['full_name', 'email']

class UserPaymentDetails(forms.ModelForm):
    expiry = forms.CharField(label='Expiry', widget=forms.TextInput(attrs={'placeholder': 'MM/YY', 'maxlength': 5}))

    class Meta:
        model = UserPaymentInformation
        fields = ['cardnumber', 'cvv', 'expiry']

    def clean(self):
        cleaned_data = super().clean()
        if len(cleaned_data["cardnumber"]) != 16:
            self.add_error("cardnumber", "Card number must be 16 digits")
        if len(cleaned_data["cvv"]) != 3:
            self.add_error("cvv", "CVV must be 3 digits")
        if len(cleaned_data["expiry"]) != 5:
            self.add_error("expiry", "Please enter in correct format - mm/yy")
        date_pattern = re.compile("^([0-9]{2})\/?([0-9]{2})$")
        if not date_pattern.match(cleaned_data['expiry']):
            self.add_error("expiry", "Please enter in correct format - mm/yy")
        return cleaned_data

class ApplicationSettingsForm(forms.ModelForm):

    class Meta:
        model = ApplicationSettings
        fields = ['ticket_price', 'min_seats', 'max_seats']

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data["ticket_price"] < 50:
            self.add_error("ticket_price", "Ticket price cannot be less than 50")
        elif cleaned_data["min_seats"] <30 or cleaned_data["min_seats"] > 100:
            self.add_error("min_seats", "Range of minimum seats is between 30 to 100")
        elif cleaned_data["max_seats"] < cleaned_data["min_seats"]:
            self.add_error("max_seats", "Maximum seats cannot be less than Minimum seats")
        elif cleaned_data["max_seats"] - cleaned_data["min_seats"] > 200:
            self.add_error("max_seats", "The difference between Maximum seats and Minimum seats must be less than 200")
        return cleaned_data

class AddMovieForm(forms.ModelForm):

    class Meta:
        model= Movies
        fields = ["movie_name"]