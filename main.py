
import tools

from flask      import Flask, request, render_template, jsonify

from forms      import MedicaidForm
from models.fta import FTA
from models.ndc import Plans
from medicare   import get_location



application = Flask(__name__,static_url_path='/static')



@application.route('/')
def home():
    return render_template( 'home.html')


@application.route('/medicaid')
def medicaid():
    """
    Get medicaid results
    :return:
    """
    form = MedicaidForm(request.form)
    if request.method == 'POST' and form.validate():
        pass

    context = {}
    return render_template( 'fit.html', **context )


@application.route('/medicare')
def medicare():
    """
    get
    :return:
    """


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
    if 'qry' in request.args:
        look_for = "{}%".format( request.args['qry'].lower() )

    if 'zipcode' in request.args:
        look_in = get_location(request.args['zipcode'] )[0]
        county_code = f"%{str(look_in.COUNTY_CODE)}%"

    plans_list = Plans.session.query(Plans.PLAN_NAME)\
                                  .filter(Plans.PLAN_NAME.ilike(look_for), Plans.COUNTY_CODE.ilike(county_code))\
                                  .distinct(Plans.PLAN_NAME)\
                                  .all()


    # If you use a selector in the json, return a json with numbered values, otherwise just a list
    for val, txt in enumerate(plans_list):
            results.append(txt[0])

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
        drugs, excluded = tools.get_related_drugs(request.args['drug_name'])

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



@application.route('/drug_names', methods=['GET'])
def drug_names():
    """
    Retrieve a list of drugs on spelling
    :return:
    """
    results=[]
    if 'qry' in request.args:
        look_for = f"{request.args['qry'].lower()}%"
        drug_list = FTA.session.query(FTA.PROPRIETARY_NAME).filter( FTA.PROPRIETARY_NAME.ilike(look_for) )

        for drug in drug_list:
            results.append( drug.PROPRIETARY_NAME)


    return jsonify(results)


@application.route('/alternatives', methods=['GET'])
def alternatives():
    """

    :return:
    """
    results = []
    if 'drug_name' in request.args and 'plan_name' in request.args:
         alternatives,exclude = tools.get_from_medicaid(request.args['drug_name'],
                                                        request.args['plan_name']
                                                       )

    for alternative in alternatives:
        fr = alternative['Formulary_Restrictions'].lower()

        # Make sure no excluded words formulary restrictions
        for ex in exclude:
            if ex in fr:
                break
        else:
            results.append(alternative)


    return jsonify( results )




@application.route('/medicare_options', methods=['GET'])
def medicare_options():
    """
    drug_name, dose_strength, dose_unit, plan_name
    :return:
    """
    if 'drug_name' in request.args and 'plan_name' in request.args:
        pass

    return jsonify( results )



if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000, debug=False)
