from wtforms                import ( validators,
                                     Form,
                                     StringField,
                                     PasswordField,
                                     SubmitField,
                                    )

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
    username   = StringField("Email Address", [validators.Email(message=u'That\'s not a valid email address.'),
                                               validators.Length(min=6, max=45)
                                              ]
                           )
    password = PasswordField("Password")
    submit = SubmitField("Sign Up")


class ForgotForm(Form):
    email  = StringField(u"Email")
    submit = SubmitField("")
