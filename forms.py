import re


from wtforms import ( Form,
                      StringField,
                      SelectField
                     )


class ValidationError(Exception):
    pass


"""
     <label class="input-group-prepend"><span class="input-group-text">Zipcode</span></label>
      <input type="text" class="form-control" placeholder="ex. 12345">

      <label class="input-group-prepend"> <span class="input-group-text">Plan Name</span> </label>
      <input class="form-control basicAutoComplete" type="text" autocomplete="off">

      <label class="input-group-prepend"> <span class="input-group-text">Medication</span></label>
      <input class="form-control basicAutoComplete" type="text" autocomplete="off">
"""

class MedicaidForm(Form):
    """
    Medicaid form input
    """
    zipcode    = StringField()
    plan       = SelectField()
    medication = SelectField()


