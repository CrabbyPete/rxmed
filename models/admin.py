from flask_admin.contrib.sqla import ModelView
from .medicaid import *
from .fta import FTA

class FTAModelView(ModelView):
    can_delete = False  # disable model deletion
    page_size = 50      # the number of entries to display on the list view
    column_exclude_list    = ['NDC_IDS']
    form_excluded_columns  = ['NDC_IDS']
    column_searchable_list = ['PROPRIETARY_NAME','NONPROPRIETARY_NAME']

    def on_model_change(self, form, model, is_created):

        model.RELATED_DRUGS = [int(d) for d in model.RELATED_DRUGS]
        model.SBD_RXCUI = [int(d) for d in model.SBD_RXCUI]
        pass


def build_admin( admin, session ):
    admin.add_view(FTAModelView(FTA, session))

