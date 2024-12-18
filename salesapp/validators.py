import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy  as _


class NumberValidator(object):
    def validate(self, password, user=None):
        if not re.findall('\d', password):
            raise ValidationError(
                _("The password must contain at least 1 digit"),
                code='password_no_number',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least 1 digit"
        )


class UppercaseValidator(object):
    def validate(self, password, user=None):
        if not re.findall('[A-Z]', password):
            raise ValidationError(
                _("The password must contain at least 1 uppercase letter"),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least 1 uppercase letter"
        )


class LowercaseValidator(object):
    def validate(self, password, user=None):
        if not re.findall('[a-z]', password):
            raise ValidationError(
                _("The password must contain at least 1 lowercase letter"),
                code='password_no_lower',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least 1 lowercase letter"
        )


class SymbolValidator(object):
    def validate(self, password, user=None):
        if not re.findall('[()[\]{}|\\`~!@#$%^&*_\-+=;:\'",<>./?]', password):
            raise ValidationError(
                _("The password must contain at least 1 special character"),
                code='password_no_symbol',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least 1 special character"
        )

def validate_field_nospace(value, field_name="Name"):
   match = re.match(r"^[a-zA-Z0-9_]+$", value)
   if not match:
       raise ValidationError(f'Invalid {field_name}, use characters Only alphanumeric and _ are allowed')

def validate_field(value, field_name="Name"):
   match = re.match(r"^[a-zA-Z0-9_ ]+$", value)
   if not match:
       raise ValidationError(f'Invalid {field_name}, use characters [(a-z), (A-Z), (0-9), _, space]')

def validate_number_field(value, field_name="Numeric field", msg=""):
   if msg == "": msg = f'Invalid {field_name}, only numbers are allowed'
   match = re.match(r"^[0-9]+$", value)
   if not match:
       raise ValidationError(msg)

def validate_email(value):
   match = re.match(r"^[a-zA-Z0-9_@.-]+$", value)
   if not match:
       raise ValidationError('Email field accepts only (a-z), (A-Z), (0-9), _, @, ., -]')

def validate_date(value):
    date_pattern = re.compile("^([0-9]{2})\/?([0-9]{2})\/?([0-9]{4})$")
    if not date_pattern.match(value):
        raise ValidationError('Invalid date format. Accepted format mm/dd/yyyy')