from flask_admin.contrib.sqla import ModelView
from .medicaid import *
from .fta import FTA

class FTAModelView(ModelView):
    can_delete = False  # disable model deletion
    page_size = 50      # the number of entries to display on the list view
    column_exclude_list    = ['NDC_IDS']
    form_excluded_columns  = ['NDC_IDS']
    column_searchable_list = ['PROPRIETARY_NAME','NONPROPRIETARY_NAME']


class MolinaView(ModelView):
    can_delete = False
    column_searchable_list = ['Brand_name','Generic_name']


class CaresourceView(ModelView):
    can_delete = False
    column_searchable_list = ['Drug_Name']


class BuckeyeView(ModelView):
    can_delete = False
    column_searchable_list = ['Drug_Name']

class ParamountView(ModelView):
    can_delete = False
    column_searchable_list = ['Brand_name','Generic_name']


class UHCView(ModelView):
    can_delete = False
    column_searchable_list = ['Brand','Generic']


def build_admin( admin, session ):
    admin.add_view(FTAModelView(FTA, session))
    admin.add_view(CaresourceView(Caresource, session))
    admin.add_view(MolinaView(Molina, session))
    admin.add_view(ParamountView(Paramount, session))
    admin.add_view(BuckeyeView(Buckeye, session))
    admin.add_view(UHCView(UHC, session))
