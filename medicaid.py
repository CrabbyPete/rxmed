import pandas as pd

from api import OhioStateAPI, RxNorm
from log import log
from tools import get_related_drugs, get_location

from models          import FTA, OpenPlans, PlanNames
from models.medicaid import OhioState

row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}

rxnorm = RxNorm()


class BadPlanName(Exception):
    pass


def reform_data( data, heading ):
    """
    Reformat the data to ensure there is a Formulary Restrictions, and capitalize drugs
    :param data:
    :return:
    """
    result = {}
    for k, v in data.items():
        k = " ".join([k for k in k.split('_')])
        try:
            n = [h.lower() for h in heading].index(k.lower())
        except ValueError:
            pass
        else:
            result[heading[n]] = v

    # Get rid of duplicate dicts
    return result


def get_drug_list(drug_name):
    """
    Get all the alternative drugs
    :param drug_name:
    :return: set of drugs
    """
    rxcui_list = get_related_drugs(drug_name, False)
    return rxcui_list


def get_sdb_scd( rxcui ):
    """ Get the SBD/SCD for a rxcui

    :param rxcui:
    :return:
    """
    scd = []
    sbd = []

    related = rxnorm.getRelatedByType(rxcui,tty=['SBD','SCD'])
    if related:
        if 'conceptGroup' in related:
            for info in related['conceptGroup']:
                if info['tty'] == 'SCD':
                    scd = [ int(cp['rxcui']) for cp in info.get('conceptProperties','') ]

                elif info['tty'] == 'SBD':
                    sbd = [ int(cp['rxcui']) for cp in info.get('conceptProperties',[]) ]
    return sbd, scd


def all_plans(drug_name, plan_name, zipcode, plan_type):

    heading = ['Drug Name', 'Drug Tier','Step Therapy', 'Quantity Limit','Prior Authorization']

    pa = False
    included = False

    drug_name = drug_name.split()[0].lower()
    fta_list = FTA.find_by_name(drug_name)
    location = get_location(zipcode)
    state = location.STATE
    plan_ids = PlanNames.ids_by_name(state, plan_name)

    # Get all the SCD and SBD rxcui for this and related
    rxcui_list = []
    excluded = set()

    if fta_list:
        for fta in fta_list:
            if fta.SCD:
                rxcui_list.extend(fta.SCD)
            if fta.SBD:
                rxcui_list.extend(fta.SBD)

            if fta.RELATED_DRUGS:
                rxcui_list.extend(fta.RELATED_DRUGS)
                for rxcui in fta.RELATED_DRUGS:
                    sbd, scd = get_sdb_scd(rxcui)
                    rxcui_list.extend( sbd + scd )
    try:
        rxcui_list = set(rxcui_list)
        records = OpenPlans.session.query(OpenPlans).filter(OpenPlans.plan_id.in_(plan_ids),
                                                            OpenPlans.rxnorm_id.in_(rxcui_list)).all()
    except Exception as e:
        log.error(f"OpenPlans query exception {str(e)}")
        records = []

    # remaining = [r.rxnorm_id for r in records]
    data = []
    pa = False
    included = False
    for record in records:
        name = record.drug.NAME
        new_record = row2dict(record)
        new_record['Drug Name'] = name
        if drug_name in name.lower():
            included = True
            if new_record['prior_authorization'] == 'True':
                pa = True
        data.append(reform_data(new_record, heading))

    if not included:
        pa = True

    if data:
        data = pd.DataFrame(data).drop_duplicates().to_dict('records')

    return {'data': data, 'pa':pa, 'heading':heading}


def ohio_state( drug_name ):
    """
    Return results from Ohio State
    :param drug_name:
    :return: dict
    """
    heading = ['Product Description',
               'Copay',
               'Package',
               'Route Of Administration',
               'Covered For Dual Eligible',
               'Formulary Restrictions',
              ]

    pa = False
    included = False

    drug_name = drug_name.split()[0].lower()
    rxcui_list = get_drug_list(drug_name)

    data = []
    for rxcui in rxcui_list:
        records = OhioState.find_by_rxcui(rxcui)

        if not records:
            records = OhioStateAPI(drug_name)
            save = True
        else:
            save = False

        for record in records:

            if save:
                record['drug_name'] = drug_name
                ohio = OhioState.get_or_create(**record)
                ohio.save()
            else:
                record = row2dict(record)

            # Ignore records not active
            if not record['active']:
                continue

            # Change name of Prior Authorization and Yes to PA
            if record['Prior_Authorization_Required'] == 'Yes':
                record['Prior_Authorization_Required'] = 'PA'

            record['Formulary_Restrictions']=record['Prior_Authorization_Required']
            if drug_name in record['Product_Description'].lower():
                included = True
                if 'PA' in record['Formulary_Restrictions']:
                    record['Formulary_Restrictions'] = 'Yes'
                    pa = True

            data.append(reform_data(record, heading))

    if not included:
        pa = True

    if data:
        data = pd.DataFrame(data).drop_duplicates().to_dict('records')

    return { 'data':data, 'pa':pa, 'heading':heading }


def get_medicaid_plan( drug_name, plan_name, zipcode, plan_type ):
    """Get the plan by its name
    :param plan_name: plan name from the select option
    :param drug_name: drug name the user selected
    :return: dict:
    """
    if plan_name == 'OH State Medicaid':
        return ohio_state( drug_name )
    else:
        return all_plans(drug_name, plan_name, zipcode, plan_type)


if __name__ == "__main__":
    from settings      import DATABASE
    from models.base   import Database

    with Database(DATABASE) as db:

        # Medicaid
        #result = get_medicaid_plan("flovent", "Caresource")

        #result = get_medicaid_plan('Symbicort', 'CARESOURCE', 'OH')
        #print(result)
        result = get_medicaid_plan("Admelog", "Caresource (OH Medicaid)", 'OH')
        #result = get_medicaid_plan('fluticasone','Caresource')


        print( result )
        result = get_medicaid_plan('Qvar', 'OH State Medicaid')
        print(result)
        result = get_medicaid_plan("Trulicity", "OH State Medicaid")
        print(result)
        result = get_medicaid_plan("Admelog", "OH State Medicaid")
        print(result)
        result = get_medicaid_plan('Lantus', 'OH State Medicaid')
        print(result)
        result = get_medicaid_plan("Symbicort", "UHC Community Health Plan")
        print(result)
        result = get_medicaid_plan("Admelog", "Buckeye Health Plan" )
        print( result )
        result = get_medicaid_plan("Admelog", "OH State Medicaid")
        print( result )
        result = get_medicaid_plan("Admelog", "UHC Community Health Plan")
        print( result )
        result = get_medicaid_plan("Admelog", "Molina Healthcare")
        print( result )
        result = get_medicaid_plan("Admelog", "Paramount Advantage")
        print(result)
        result = get_medicaid_plan('pulmicort', "Caresource")
        print(result)
        result = get_medicaid_plan("Breo","OH State Medicaid")
        print(result)
        result = get_medicaid_plan("Trulicity","OH State Medicaid")
        print(result)
        result = get_medicaid_plan("Pamidronate Disodium", "Caresource") # CLASS_ID != NULL
        print(result)
        result = get_medicaid_plan("Tresiba", "Paramount Advantage")
        print(result)
        result = get_medicaid_plan("Advair", "Paramount Advantage")
        print(result)
        result = get_medicaid_plan("epinephrine", "Paramount Advantage")
        print(result)
        result = get_medicaid_plan("Potassium Citrate", "Caresource")
        print(result)
        result = get_medicaid_plan("Zanaflex", "Caresource")
        print(result)
        result = get_medicaid_plan("Trelegy", "Caresource")
        print(result)
        result = get_medicaid_plan("Breo","Caresource")
        print(result)
        result = get_medicaid_plan('Symbicort','Molina Healthcare')
        print(result)
        result = get_medicaid_plan('ARTHROTEC','Molina Healthcare')
        print(result)
        result = get_medicaid_plan('Tresiba','Caresource')
        print(result)

