from flask_admin.contrib.sqla import ModelView

class FTAModelView(ModelView):
    can_delete = False  # disable model deletion
    page_size = 50      # the number of entries to display on the list view
    column_searchable_list = ['PROPRIETARY_NAME', 'NONPROPRIETARY_NAME']