
import tools

from flask              import Flask, request, render_template, jsonify, url_for
from flask_admin        import Admin

from log                import log, rq_log
from models.fta         import FTA
from models.medicaid    import Caresource, Molina, Paramount, Buckeye, UHC
from models             import Plans, NDC
from models.base        import Database
from models.admin       import *

from settings       import DATABASE

from user           import init_user

application = Flask(__name__, static_url_path='/static')
application.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

db = Database( DATABASE )
db.open()

admin = Admin(application, name='RxMedAccess', template_mode='bootstrap3')
admin.add_view( FTAModelView(FTA, db.session))
admin.add_view( CaresourceView(Caresource, db.session))
admin.add_view( MolinaView(Molina,db.session))
admin.add_view( ParamountView(Paramount,db.session))
admin.add_view( BuckeyeView(Buckeye,db.session))
admin.add_view( UHCView(UHC,db.session))

init_user( application )

@application.errorhandler(500)
def internal_error(error):
    log.error(f"Exception caught:{str(error)}")
    return jsonify([])


@application.route('/')
def home():
    return render_template('home.html')


@application.route('/fit')
def fit():
    """
    Get medicaid results
    :return:
    """
    context = {}
    return render_template( 'fit.html', **context )


# Ajax calls
@application.route('/plans', methods=['GET'])
def plans():
    """
    Retrieve plans similar to spelling
    http://localhost:5000/plans?zipcode=36117&qry=Hum
    :param spelling:
    :return: json list of plan names
    """
    results = []
    if not 'zipcode' in request.args or request.args['zipcode'] == "":
        results = ['Caresource',
                   'Paramount Advantage',
                   'Molina Healthcare',
                   'UHC Community Plan',
                   'OH State Medicaid',
                   'Buckeye Health Plan'
                  ]
    else:
        if 'qry' in request.args:
            look_for = request.args['qry']
            zipcode = request.args['zipcode']

            look_in = tools.get_location( zipcode )
            if look_in:
                county_code = look_in.GEO.COUNTY_CODE
                ma_region   = look_in.GEO.MA_REGION_CODE
                pdp_region  = look_in.GEO.PDP_REGION_CODE
            
                results = Plans.find_in_county(county_code, ma_region, pdp_region, look_for)
   
    return jsonify(results)


@application.route('/related_drugs')
def related_drugs():
    """
    http://localhost:5000/related_drugs?drug_name=Admelog
    Get related drugs by name
    :return: drugs
    """
    results = []

    if 'drug_name' in request.args:
        drugs, _ = tools.get_related_drugs(request.args['drug_name'])

    for drug in drugs:
        results.append(drug)

    return jsonify(results)


@application.route('/formulary_id')
def formulary_id():
    """

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


@application.route('/ndc_drugs', methods=['GET'])
def ndc_drugs():
    """
    Type ahead for ncd drugs
    :return a list of drugs from ncd 
    """
    results = set()
    if 'qry' in request.args:
        look_for = request.args['qry']
        drug_list = NDC.find_by_name( look_for )
        for d in drug_list:
            s = d['PROPRIETARY_NAME'] 
            if d['DOSE_STRENGTH'] and d['DOSE_UNIT']:
                s += f" {d['DOSE_STRENGTH']} {d['DOSE_UNIT']}"
            results.update([s])
    
    return jsonify(list(results))


@application.route('/drug_names', methods=['GET'])
def drug_names():
    """
    Retrieve a list of drugs on spelling
    :return:
    """
    results = set()
    if 'qry' in request.args and len(request.args['qry']) >= 3:
        look_for = f"{request.args['qry'].lower()}%"
        drug_list = FTA.find_by_name(look_for, False )
        results = [d.PROPRIETARY_NAME.capitalize() for d in drug_list ]

        drug_list = FTA.find_nonproprietary( look_for )
        results.extend( [ d.NONPROPRIETARY_NAME.capitalize() for d in drug_list ])

    results = sorted( list(results) )
    return jsonify(results)


@application.route('/medicaid_options', methods=['GET'])
def medicaid_options():
    """
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

        alternatives, exclude = tools.get_from_medicaid(request.args['drug_name'], request.args['plan_name'])

        pa = False
        included = False

        drug_name = drug_name.lower()
        headings = {'caresource':['Drug Name', 'Drug Tier', 'Formulary Restrictions'],
                    'paramount' :['Brand Name', 'Generic Name', 'Formulary Restrictions'],
                    'molina'    :['Brand Name', 'Generic Name', 'Formulary Restrictions'],
                    'uhc'       :['Brand', 'Generic', 'Formulary Restrictions'],
                    'buckeye'   :['Drug Name', 'Preferred Agent', 'Formulary Restrictions'],
                    'oh'        :['Product Description',
                                  'Formulary Restrictions',
                                  'Copay',
                                  'Package',
                                  'Route Of Administration',
                                  'Covered For Dual Eligible',
                                 ]
                   }

        heading = headings[plan_name.lower().split(' ')[0]]
        for alternative in alternatives:

            # Caresource
            if plan_name.startswith("Caresource"): #Caresourse: Drug_Name,Drug_Tier,Formulary_Restrictions
                look_in = alternative['Drug_Name']

                if drug_name in alternative['Drug_Name'].lower():
                    included = True
                    if 'PA' in alternative['Formulary_Restrictions']:
                        pa = True

            # Paramount
            elif plan_name.startswith("Paramount"):# Paramount: Formulary_restriction, Generic_name, Brand_name
                look_in = alternative['Brand_name']+" "+alternative['Generic_name']

                if drug_name in alternative['Brand_name'].lower() or \
                   drug_name in alternative['Generic_name'].lower():
                    included = True
                    if 'PA' in alternative['Formulary_restriction']:
                        pa = True

            # Molina
            elif plan_name.startswith("Molina"): # Molina:# Generic_name,Brand_name,Formulary_restriction
                look_in = alternative['Brand_name']+" "+alternative['Generic_name']

                # For Molina check for the word prior authorization or PA in Generic
                if 'prior' in alternative['Formulary_restriction'] or 'PA' in alternative['Generic_name']:
                    alternative['Formulary_restriction'] = 'PA'

                if drug_name in alternative['Brand_name'].lower() or \
                   drug_name in alternative['Generic_name'].lower():
                    included = True
                    if 'PA' in alternative['Formulary_restriction']:
                        pa = True

            #UHC
            elif plan_name.startswith("UHC"):# UHC: Generic,Brand,Tier,Formulary_Restriction
                look_in = alternative['Brand']+" "+alternative['Generic']

                if drug_name in alternative['Brand'].lower() or \
                   drug_name in alternative['Generic'].lower():
                    included = True
                    if 'PA' in alternative['Formulary_Restrictions']:
                        pa = True

            elif plan_name.startswith("Buckeye"):# Buckeye: Drug_Name,Preferred_Agent,Fomulary_restriction
                if alternative['Preferred_Agent'] == "***":
                    alternative['Preferred_Agent'] = "No"
                else:
                    alternative['Preferred_Agent'] = "Yes"
                    
                look_in = alternative['Drug_Name']

                if drug_name in alternative['Drug_Name'].lower():
                    included = True
                    if 'PA' in alternative['Fomulary_restriction']:
                        pa = True

            # Ohio State
            elif plan_name.startswith("OH State"):
                look_in = alternative['Product_Description']
                pa = alternative.pop('Prior_Authorization_Required')
                alternative['fo'] = 'PA' if 'Y' in pa else "None"

                if drug_name in alternative['Product_Description'].lower():
                    included = True
                    if 'PA' in alternative['fo']:
                        pa = True


            # Check the front end exclusions
            fr = look_in.lower()
            for ex in exclude:
                if ex in fr:
                    break
            else:
                # Reformat the headers
                if 'id' in alternative:
                    alternative.pop('id')
                    
                result = {}
                for k,v in alternative.items():
                    if k.lower().startswith('fo'):
                        k = 'Formulary Restrictions'
                    else:
                        k = " ".join( [ k.capitalize() for k in k.split('_') ] )
                    result[k] = v
                    
                data.append( result )

    if not included:
        pa = True

    reply = jsonify({'heading':heading, 'data':data, 'pa':pa} )
    return reply


@application.route('/medicare_options', methods=['GET'])
def medicare_options():
    """
    drug_name, dose_strength, dose_unit, plan_name
    :return:
    """
    rq = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

    results = []
    if 'drug_name' in request.args and 'plan_name' in request.args and 'zipcode' in request.args:

        drug_name = request.args['drug_name']
        plan_name = request.args['plan_name']
        zipcode = request.args['zipcode']

        rq_log.info(f"{rq},{drug_name},{plan_name},'medicare")

        results = tools.get_from_medicare(drug_name, plan_name, zipcode )

    return jsonify( results )


if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000, debug=False)

