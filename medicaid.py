import json
import pandas as pd

from functools       import lru_cache

from api             import OhioStateAPI
from tools           import get_related_drugs

from models          import FTA
from models.medicaid import Caresource, Molina, Molina_Healthcare, Paramount, Buckeye, UHC, OhioState

""" Select in the HTML
        <option>Buckeye Health Plan</option>
        <option>Caresource</option>
        <option>OH State Medicaid</option>
        <option>UHC Community Health Plan</option>
        <option>Molina Healthcare</option>
        <option>Paramount Advantage</option>
"""

row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}


def front_end_excluded( drug, excluded:list)->bool:
    """
    Check if this record should be excluded
    :param exclude:
    :param excluded:
    :return:
    """
    for ex in excluded:
        if len(ex) and ex in drug.lower():
            return True
    return False


def reform_data( data, heading ):
    """
    Reformat the data to ensure there is a Formulary Restrictions, and capitalize drugs
    :param data:
    :return:
    """
    result = {}
    for k, v in data.items():
        if k.lower().startswith('fo'):
            k = 'Formulary Restrictions'
        else:
            k = " ".join([k.capitalize() for k in k.split('_')])

        if k in heading:
            result[k] = v

    # Get rid of duplicate dicts
    return result


def get_drug_list( drug_name ):
    """
    Get all the alternative drugs
    :param drug_name:
    :return: set of drugs and excluded front end
    """
    fta_list, excluded = get_related_drugs(drug_name)
    drug_list = set([FTA.get(fta).PROPRIETARY_NAME for fta in fta_list])
    drug_list.update([drug_name])

    return set(drug_list), excluded


def caresource(drug_name):
    """
    Get all the alternatives for Caresource
    :param drug_name:
    :return:
    """
    heading = ['Drug Name', 'Drug Tier', 'Formulary Restrictions']

    pa = False
    included = False

    drug_name = drug_name.lower()
    drug_list, excluded = get_drug_list(drug_name)

    data = []
    for drug in drug_list:
        records = Caresource.find_by_name(drug)
        for record in records:
            if front_end_excluded( record.Drug_Name, excluded ):
                continue

            record = row2dict(record)
            record.pop('id')

            if drug_name in record['Drug_Name'].lower():
                included = True
                if 'PA' in record['Formulary_Restrictions']:
                    pa = True

            data.append(reform_data(record, heading))

    if not included:
        pa = True

    if data:
        data = pd.DataFrame(data).drop_duplicates().to_dict('records')
    return {'data': data, 'pa':pa, 'heading':heading}


def molina( drug_name ):
    """
    Return results from Molina
    :param drug_name:
    :return:
    """
    heading = ['Brand Name', 'Generic Name', 'Formulary Restrictions']

    pa = False
    included = False

    drug_name = drug_name.lower()
    drug_list, excluded = get_drug_list(drug_name)

    data = []
    for drug in drug_list:
        records = Molina.find_by_name(drug)
        """
            if (Generic_name) has a capital word “PA”, 
            then retrieve its respective column B (Brand_name) [2018 Molina PDL 10_9_18]. 
            Match (first word match), to [Molina Healthcare PA criteria 10_1_18].DRUG_NAME). 
        """
        for record in records:
            look_at = record.Brand_name if record.Brand_name else ''
            if isinstance(record.Generic_name, str):
                look_at += " "+record.Generic_name
            if front_end_excluded(look_at, excluded):
                continue

            record = row2dict(record)
            record.pop('id')

            name = record['Generic_name']
            name = name.split(',')[0] if ',' in name else name
            if name.endswith("PA"):
                try:
                    adc = Molina_Healthcare.find_brand(record['Brand_name'])[0]
                    record['Note'] = adc['ALTERNATIVE_DRUG_CRITERIA']
                except:
                    record['Note'] = ''
            else:
                record['Note'] = ''

            if 'prior' in record['Formulary_Restrictions'] or 'PA' in record['Generic_name']:
                record['Formulary_restriction'] = 'PA'

            if drug_name in record['Brand_name'].lower() or \
               drug_name in record['Generic_name'].lower():
                    included = True
                    if 'PA' in record['Formulary_Restrictions']:
                        pa = True

            data.append(reform_data(record, heading))

    if not included:
        pa = True

    if data:
        data = pd.DataFrame(data).drop_duplicates().to_dict('records')
    return {'data':data, 'pa':pa, 'heading':heading}


def uhc_community( drug_name ):
    heading = ['Brand', 'Generic','Tier','Formulary Restrictions']

    pa = False
    included = False

    drug_name = drug_name.lower()
    drug_list, excluded = get_drug_list(drug_name)

    data = []
    for drug in drug_list:

        records  = UHC.find_by_name(drug)
        for record in records:

            look_at = record.Brand if record.Brand else ''
            if isinstance(record.Generic, str):
                look_at += ' '+record.Generic
            if front_end_excluded(look_at, excluded):
                continue

            record = row2dict(record)
            record.pop('id')

            if drug_name in record['Brand'].lower() or \
               drug_name in record['Generic'].lower():
                    included = True
                    if 'PA' in record['Formulary_Restrictions']:
                        pa = True

            data.append(reform_data(record,heading))

    if not included:
        pa = True

    if data:
        data = pd.DataFrame(data).drop_duplicates().to_dict('records')
    return {'data': data, 'pa': pa, 'heading':heading}


def paramount( drug_name ):
    """
    Return all results for Paramount
    :param drug_name:
    :return: dict:
    """
    heading = ['Brand Name', 'Generic Name', 'Formulary Restrictions']

    pa = False
    included = False

    drug_name = drug_name.lower()

    drug_list, excluded = get_drug_list(drug_name)

    data = []
    for drug in drug_list:
        records = Paramount.find_by_name(drug)
        for record in records:

            look_at = record.Brand_name if record.Brand_name else ''
            if isinstance(record.Generic_name, str):
                look_at += " "+record.Generic_name
            if front_end_excluded(look_at, excluded ):
                continue

            record = row2dict(record)
            record.pop('id')

            if drug_name in record['Brand_name'].lower() or \
               drug_name in record['Generic_name'].lower():
                included = True
                if 'PA' in record['Formulary_restriction']:
                    pa = True

            data.append(reform_data(record, heading))

    if not included:
        pa = True

    if data:
        data = pd.DataFrame(data).drop_duplicates().to_dict('records')

    return { 'data':data, 'pa':pa, 'heading':heading }


def ohio_state( drug_name ):
    """
    Return results from Ohio State
    :param drug_name:
    :return: dict
    """
    heading = ['Product Description',
               'Formulary Restrictions',
               'Copay',
               'Package',
               'Route Of Administration',
               'Covered For Dual Eligible',
              ]

    pa = False
    included = False

    drug_name = drug_name.lower()
    drug_list, excluded = get_drug_list(drug_name)

    data = []
    for drug in drug_list:
        records = OhioState.find_product(drug)

        if not records:
            records = OhioStateAPI(drug)
            save = True
        else:
            save = False

        for record in records:
            if save:
                record['drug_name'] = drug
                ohio = OhioState.get_or_create(**record)
                ohio.save()

            # Ignore records not active
            if not record['active']:
                continue

            # Exclude the front end
            if front_end_excluded(record['Product_Description'], excluded):
                continue

            # Change name of Prior Authorization and Yes to PA
            if record['Prior_Authorization_Required'] == 'Yes':
                record['Prior_Authorization_Required'] = 'PA'

            record['Formulary_Restrictions']=record['Prior_Authorization_Required']
            del record['Prior_Authorization_Required']

            if drug_name in record['Product_Description'].lower():
                included = True
                if 'PA' in record['Formulary_Restrictions']:
                    pa = True

            data.append(reform_data(record, heading))

    if not included:
        pa = True

    if data:
        data = pd.DataFrame(data).drop_duplicates().to_dict('records')

    return { 'data':data, 'pa':pa, 'heading':heading }


def buckeye( drug_name ):
    heading = ['Drug Name', 'Preferred Agent', 'Formulary Restrictions']

    pa = False
    included = False

    drug_name = drug_name.lower()
    drug_list, excluded = get_drug_list(drug_name)

    data = []
    for drug in drug_list:
        records = Buckeye.find_by_name(drug)
        for record in records:

            if front_end_excluded(record.Drug_Name, excluded):
                continue

            record = row2dict(record)
            record.pop('id')

            if record['Preferred_Agent'] == "***":
                record['Preferred_Agent'] = "No"
            else:
                record['Preferred_Agent'] = "Yes"

            if drug_name in record['Drug_Name'].lower():
                included = True
                if 'PA' in record['Fomulary_Restrictions']:
                    pa = True

            data.append(reform_data(record, heading))

    if not included:
        pa = True

    if data:
        data = pd.DataFrame(data).drop_duplicates().to_dict('records')
    return {'data':data, 'pa':pa, 'heading':heading}


def get_medicaid_plan( drug_name, plan_name ):
    """
    Get the plan by its name
    :param plan_name: plan name from the select option
    :param drug_name: drug name the user selected
    :return: dict:
    """
    if plan_name == 'Buckeye Health Plan':
        return buckeye( drug_name )

    elif plan_name == 'Caresource':
        return caresource( drug_name )

    elif plan_name == 'OH State Medicaid':
        return ohio_state( drug_name )

    elif plan_name == 'UHC Community Health Plan':
        return uhc_community( drug_name )

    elif plan_name == 'Molina Healthcare':
        return molina( drug_name )

    elif plan_name == 'Paramount Advantage':
        return paramount( drug_name )

    else:
        return None

if __name__ == "__main__":
    from settings      import DATABASE
    from models.base   import Database

    with Database(DATABASE) as db:

        # Medicaid
        result = get_medicaid_plan('Qvar', 'OH State Medicaid')
        print(result)
        """
        result = get_medicaid_plan("Trulicity", "OH State Medicaid")
        print(result)
        result = get_medicaid_plan("Admelog", "OH State Medicaid")
        print(result)
        result = get_medicaid_plan('Lantus', 'OH State Medicaid')
        print(result)
        result = get_medicaid_plan("Symbicort", "UHC Community Health Plan")
        print(result)
        result = get_medicaid_plan("Admelog", "Caresource" )
        print( result )
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
        """
