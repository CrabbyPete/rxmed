from wtforms                import validators, Form, StringField, PasswordField, SubmitField, SelectField, BooleanField
from wtforms.fields.html5   import TelField

class ValidationError(Exception):
    pass

class MedicaidForm(Form):
    """
    Medicaid form input
    """
    zipcode    = StringField()
    plan       = StringField()
    medication = StringField()


class SignInForm(Form):
    username = StringField("Enter Email",
                           [validators.Email(message=u'That\'s not a valid email address.'),
                            validators.Length(min=6, max=45)
                           ]
                          )
    password = PasswordField("Enter password")


class SignUpForm(Form):
    email = StringField("Email Address", [validators.Email(message=u'That\'s not a valid email address.'),
                                          validators.Length(min=6, max=45)
                                         ]
                           )
    first_name    = StringField("First Name")
    last_name     = StringField("Last Name")
    provider_type = SelectField("Provider Type", choices=['MD','PA','DO','NP','RN','Rph or PharmD','MA'])
    practice_name = StringField("Practive Name")
    practice_type = SelectField("What type of practice site is your facility?",
                                choices=['Primary Care Clinic',
                                         'Physician Private Practice',
                                         'Urgent Care',
                                         'Speciality Clinic'
                                         'Independent Pharmacy',
                                         'Internal Medicine Clinic',
                                         'Outpatient Clinic'] )

    phone        = TelField("Phone Number")
    password     = PasswordField("Password")
    checkbox     = BooleanField("I have read and understood the terms and conditions of use above.")



class ForgotForm(Form):
    email  = StringField(u"Email")
    submit = SubmitField("")
