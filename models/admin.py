from flask_admin.contrib.sqla import ModelView

class FTAModelView(ModelView):
    can_delete = False  # disable model deletion
    page_size = 50      # the number of entries to display on the list view
    column_searchable_list = ['PROPRIETARY_NAME', 'NONPROPRIETARY_NAME']


class MolinaView(ModelView):
    can_delete = False
    column_searchable_list = ['Brand_name','Generic_name']

class CaresourceView(ModelView):
    can_delete = False
    column_searchable_list = ['Brand_name']

class BuckeyeView(ModelView):
    can_delete = False
    column_searchable_list = ['Drug_Name']

class ParamountView(ModelView):
    can_delete = False
    column_searchable_list = ['Brand_name','Generic_name']

class UHCView(ModelView):
    can_delete = False
    column_searchable_list = ['Brand','Generic']

