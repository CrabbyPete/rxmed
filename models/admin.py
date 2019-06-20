from flask_admin.contrib.sqla import ModelView
from .fta import FTA
from .user import Users


class FTAModelView(ModelView):
    can_delete = False  # disable model deletion
    page_size = 50      # the number of entries to display on the list view
    column_exclude_list    = []
    form_excluded_columns  = []
    column_searchable_list = ['PROPRIETARY_NAME','NONPROPRIETARY_NAME']

    def on_model_change(self, form, model, is_created):
        model.RELATED_DRUGS = [int(d) for d in model.RELATED_DRUGS]
        model.SCD = [int(d) for d in model.SCD]
        model.SBD = [int(d) for d in model.SBD]

class UserModelView(ModelView):
    pass



def build_admin( admin, session ):
    admin.add_view(FTAModelView(FTA, session))
    admin.add_view(UserModelView(Users, session))



