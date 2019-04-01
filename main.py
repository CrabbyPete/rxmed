import os
import json
import tools

from flask              import Flask, request, render_template, jsonify, abort
from flask_admin        import Admin

from log                import log, rq_log

from models             import Plans, FTA, OpenPlans, Database
from models.admin       import *

from forms              import MedForm
from medicaid           import get_medicaid_plan
from medicare           import get_medicare_plan

from settings           import DATABASE

from user               import init_user

application = Flask(__name__, static_url_path='/static')
application.config['SECRET_KEY'] = os.urandom(12)
application.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

db = Database( DATABASE, schema='rxmed')
db.open()

# Build the admin pages
admin = Admin(application, name='RxMedAccess', template_mode='bootstrap3')
build_admin( admin, db.session )

# Initialize all users
init_user( application )


@application.errorhandler(500)
def internal_error(error):
    log.error(f"Exception caught:{str(error)}")
    return jsonify([])


@application.route('/')
def home():
    """
    Render the home page
    :return:
    """
    return render_template('home.html')

@application.route('/fit', methods=['POST','GET'])
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

        # Process either medicare or medicaid
        if form.plan_type.data == 'medicare':
            table = get_medicare_plan(medication, plan, zipcode)
        else:
            table = get_medicaid_plan(medication, plan)

        # You have to order the data in a list or it won't show right
        data = []
        for item in table['data']:
            row = [item[h] for h in table['heading']]
            data.append(row)

        context = {'data':data, 'head':table['heading'], 'drug':medication, 'pa': table['pa'], 'plan':plan }
        html = 'table.html'
    else:
        # Not a POST or errors
        context = {'form': form}
        html = 'med.html'

    content = render_template(html, **context)
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
                results = OpenPlans.session.query(OpenPlans.plan_name).filter(OpenPlans.state == state).distinct().all()
                results = [r[0] for r in results]
            elif plan == 'medicare':
                county_code = where.GEO.COUNTY_CODE
                ma_region = where.GEO.MA_REGION_CODE
                pdp_region = where.GEO.PDP_REGION_CODE
                results = Plans.find_in_county(county_code, ma_region, pdp_region, look_for)

    return jsonify(sorted(results))


@application.route('/open_plans')
def open_plans():
    """

    :return:
    """
    results = []
    if 'qry' in request.args:
        look_for = request.args['qry']
        zipcode = request.args['zipcode']

        zip_info = tools.get_location(zipcode)
        state = zip_info.STATE
        results = OpenPlans.session.query(OpenPlans.plan_name).filter(OpenPlans.state == state).distinct().all()
        plans = ((r[0] for r in results))
        return sorted(plans)


@application.route('/related_drugs')
def related_drugs():
    """ Related drug API
    http://localhost:5000/related_drugs?drug_name=Admelog
    Get related drugs by name
    :return: json
    """
    results = []

    if 'drug_name' in request.args:
        drugs, _ = tools.get_related_drugs(request.args['drug_name'], force=True)

    for drug in drugs:
        r = FTA.get(drug)
        results.append(f"{r.PROPRIETARY_NAME}-{r.NONPROPRIETARY_NAME}")

    return jsonify(results)


@application.route('/formulary_id')
def formulary_id():
    """ API to get formulary id
    localhost:5000/formulary_id?zipcode=43081&plan_name=CareSource Advantage (HMO)
    Get the formulary_id for a plan in a zipcode
    :return:
    """
    results = []
    if 'plan_name' in request.args and 'zipcode' in request.args:
        results = tools.get_formulary_id(request.args['plan_name'],
                                         request.args['zipcode' ]
                                        )
    return jsonify( results )


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
        """
        dbug = json.dumps( results['data'],indent=2, sort_keys=True )
        print(dbug)
        """
        return jsonify(results)

    abort(404)


if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000, debug=False)

