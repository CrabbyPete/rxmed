import sys
import logging
from flask import Flask, request, render_template, jsonify

from forms      import MedicaidForm
from models.fta import FTA
from models.ndc import Plans
from medicare   import get_location

application = Flask(__name__,static_url_path='/static')

# Initialize logging
handler = logging.StreamHandler(sys.stderr)

application.logger.setLevel(logging.INFO)
application.logger.addHandler(handler)

log = logging.getLogger("rxmed")
log.setLevel(logging.INFO)
log.addHandler(handler)


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
    Get medicare results
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


    for val, txt in enumerate(plans_list):
            results.append(txt[0])

    return jsonify(results)


@application.route('/drugs', methods=['GET'])
def drugs():
    """
    Retrieve a list of drugs on spelling
    :param spelling:
    :return:
    """
    results=[]
    if 'qry' in request.args:
        look_for = request.args['qry'].lower()
        drug_list = FTA.query( FTA.PROPRIETARY_NAME ).filter( FTA.PROPRIETARY_NAME.ilike(look_for) )
        for drug in drug_list:
            results.append( drug.PROPRIETARY_NAME)


    return jsonify(results)

if __name__ == "__main__":
    application.run(host='localhost', port=5000, debug=False)