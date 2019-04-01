from wtforms                import ( validators,
                                     Form,
                                     StringField,
                                     PasswordField,
                                     SubmitField,
                                     SelectField,
                                     BooleanField,
                                     RadioField   )

from wtforms.fields.html5   import TelField
from wtforms.validators     import Email, EqualTo, InputRequired

class ValidationError(Exception):
    pass

class MedForm(Form):
    """
    Medicaid form input
    """
    plan_type  = RadioField(choices=[('medicare','Medicare'),
                                     ('medicaid','Medicaid'),
                                     ('private' ,'Private')])
    zipcode    = StringField()
    plan       = StringField()
    medication = StringField()


class SignInForm(Form):
    email = StringField("Enter Email",
                           [validators.Email(message=u'That\'s not a valid email address.'),
                            validators.Length(min=6, max=45)
                           ]
                          )
    password = PasswordField("Enter password")


class SignUpForm(Form):
    email         = StringField("Email Address",[validators.Email(u'Please use a valid email address.')])
    first_name    = StringField("First Name")
    last_name     = StringField("Last Name")
    provider_type = SelectField("Provider Type", choices=[('MD','MD'),
                                                          ('PA','PA'),
                                                          ('DO','DO'),
                                                          ('NP','NP'),
                                                          ('RN','RN'),
                                                          ('Rph or PharmD','RP')])


    practice_name = StringField("Practive Name")
    practice_type = SelectField("What type of practice site is your facility?",
                                choices=[('PCC','Primary Care Clinic'),
                                         ('PPP','Physician Private Practice'),
                                         ('UC','Urgent Care'),
                                         ('SC','Speciality Clinic'),
                                         ('IP','Independent Pharmacy'),
                                         ('IMC','Internal Medicine Clinic'),
                                         ('OC','Outpatient Clinic')] )

    password     = PasswordField('New Password', [InputRequired(), EqualTo('confirm_pass', message='Passwords must match')])
    confirm_pass = PasswordField('Confirm Password')
    checkbox     = BooleanField("I have read and understood the terms and conditions of use above.")



class ForgotForm(Form):
    email  = StringField(u"Email")
    submit = SubmitField("")
