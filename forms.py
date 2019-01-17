import re


from wtforms import ( Form,
                      StringField,
                      SelectField
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


