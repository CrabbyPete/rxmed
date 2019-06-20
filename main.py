import os
import time
import tools

from flask              import Flask, request, render_template, jsonify, abort, redirect
from flask_admin        import Admin
from flask_login        import login_required, current_user

from log import rq_log

from models             import Plans, OpenPlans, Database, Requests, PlanNames, Contacts
from models.admin       import *

from forms import MedForm, ContactForm

from medicaid import get_medicaid_plan
from medicare import get_medicare_plan

from settings import DATABASE
from mail import send_email

from user import init_user

application = Flask(__name__, static_url_path='/static')
application.secret_key = "jaldsfji93dnd3"

#application.config['SECRET_KEY'] = os.urandom(12)
application.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

db = Database( DATABASE, schema='rxmed')
db.open()

# Initialize all users
init_user( application )

# Build the admin pages
admin = Admin(application, name='RxMedAccess', template_mode='bootstrap3')
build_admin( admin, db.session )

@application.errorhandler(500)
def internal_error(error):
    msg = str(error)
    return "500 error:{}".format(msg)


@application.route('/')
def home():
    """
    Render the home page
    :return:
    """
    return render_template('home.html')


@application.route('/fit', methods=['POST','GET'])
@login_required
def fit():
    """ Form submit of meds
    :return:
    """
    form = MedForm(request.form)
    if request.method == 'POST' and form.validate():

        zipcode = form.zipcode.data
        # Check the zipcode

        plan = form.plan.data
        medication = form.medication.data

        ip = str(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
        rq = Requests(**dict(user=current_user.id, ip = ip, zipcode = zipcode, plan = plan, drug = medication))
        rq.save()

        # Process either medicare or medicaid
        plan_type = form.plan_type.data
        try:
            if plan_type == 'medicare':
                table = get_medicare_plan(medication, plan, zipcode)
            else:
                table = get_medicaid_plan(medication, plan, zipcode, plan_type)

        except tools.BadPlanName as e:
            form.errors['plan_name'] = str(e)
            context = {'form': form}
            html = 'fit.html'

        except tools.BadLocation as e:
            form.errors['zipcode'] = str(e)
            context = {'form': form}
            html = 'fit.html'
        else:
            # You have to order the data in a list or it won't show right
            data = []
            for item in table['data']:
                row = [item[h] for h in table['heading']]
                data.append(row)

            context = {'data':data,
                       'head':table['heading'],
                       'drug':medication,
                       'pa': table['pa'],
                       'zipcode':zipcode,
                       'plan':plan,
                       'plan_type':form.plan_type.data,
                      }
            html = 'table.html'

    # If its a GET see if parameters were passed
    else:
        if request.method == 'GET':
            form.zipcode.data = request.args.get('zipcode', "")
            form.plan.data = request.args.get('plan', "")
            form.medication.data = request.args.get('drug', "")
            form.plan_type.data = request.args.get('plan_type', "medicare")

        # a POST with errors
        elif form.errors:
            if 'plan_type' in form.errors:
                form.errors['plan_type'] = "Please pick a Medicare, Medicaid, or Private plan"

        context = {'form': form}
        html = 'fit.html'

    content = render_template(html, **context)
    return content


@application.route('/contact', methods=['GET','POST'])
def contact():
    form = ContactForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.data['name']
        email = form.data['email']
        message = form.data['message']
        contact = Contacts( name = name,
                            email = email,
                            comment=message)
        contact.save()
        send_email(name, email, message)
        time.sleep(5)
        return redirect('/')

    context = {'form':form}
    content = render_template('contact.html', **context)
    return content

# Ajax calls
@application.route('/plans', methods=['GET'])
def plans():
    """ Plan name API find similar to spelling
    http://localhost:5000/plans?zipcode=36117&qry=Hum
    :return: json list of plan names
    """
    results = []
    if 'qry' in request.args:
        look_for = request.args['qry']
        if look_for[0] == '*':
            look_for = ''
        zipcode = request.args['zipcode']

        try:
            plan = request.args['plan']
        except KeyError:
            return None

        # If this is a medicaid or private plan
        where = tools.get_location(zipcode)
        if where:
            if plan in ('medicaid', 'private'):
                state = where.STATE
                results = PlanNames.by_state(state, look_for,  plan=='medicaid')
                results = [r.plan_name for r in results]
                if state == 'OH':
                    results.append('OH State Medicaid')
            elif plan == 'medicare':
                county_code = where.GEO.COUNTY_CODE
                ma_region = where.GEO.MA_REGION_CODE
                pdp_region = where.GEO.PDP_REGION_CODE
                results = Plans.find_in_county(county_code, ma_region, pdp_region, look_for)

    return jsonify(sorted(results))


@application.route('/drug_names', methods=['GET'])
def drug_names():
    """ Live search drug name API
    Type ahead api for drugs
    Retrieve a list of drugs on spelling
    :return: json:
    """
    results = set()
    if 'qry' in request.args and len(request.args['qry']) >= 3:
        look_for = f"{request.args['qry'].lower()}%"
        drug_list = FTA.find_by_name(look_for, False )
        results = set([f"{d.PROPRIETARY_NAME} - {d.NONPROPRIETARY_NAME}" for d in drug_list if d.ACTIVE])

    results = sorted(list(results))
    return jsonify(results)


@application.route('/medicaid_options', methods=['GET'])
def medicaid_options():
    """ Medicaid API
    Get all the options for a drug for a plan
    :return: json:
    """
    rq = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    #request.headers.get('X-Forwarded-For', request.remote_addr)

    data = []
    if 'drug_name' in request.args and 'plan_name' in request.args:

        drug_name = request.args['drug_name']
        plan_name = request.args['plan_name']

        rq_log.info(f"{rq},{drug_name},{plan_name},medicaid")
        results = get_medicaid_plan( drug_name, plan_name )
        return jsonify(results)

    abort(404)


@application.route('/medicare_options', methods=['GET'])
def medicare_options():
    """ Medicare API interface
    drug_name, dose_strength, dose_unit, plan_name
    :return: json: data
    """
    rq = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

    results = []
    if 'drug_name' in request.args and 'plan_name' in request.args and 'zipcode' in request.args:

        drug_name = request.args['drug_name']
        plan_name = request.args['plan_name']
        zipcode = request.args['zipcode']

        rq_log.info(f"{rq},{drug_name},{plan_name},'medicare")
        results = get_medicare_plan(drug_name, plan_name, zipcode )
        return jsonify(results)

    abort(404)


if __name__ == "__main__":
    application.run(host='localhost', port=5000, debug=False)

