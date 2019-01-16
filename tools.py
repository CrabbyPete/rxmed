import re

from log          import log

from models.geo   import Zipcode, Geolocate
from models.ndc   import NDC, Plans, Basic_Drugs,Beneficiary_Costs
from models.fta   import FTA
from models.plans import Caresource, Paramount, Molina, Molina_Healthcare, UHC, Buckeye

from api          import RxClass



def walk(seq, look_for):
    """
    Find a part of a json
    :param seq: the full json to look into
    :param look_for: what to look for
    :return: the first instance of the json you want
    """
    if isinstance( seq, list ):
        for value in seq:
            found = walk( value, look_for )
            if found:
                return found

    elif isinstance( seq, dict ):
        for key,value in seq.items():
            if key == look_for:
                return value

            if isinstance( value, dict ) or isinstance( value, list ):
                found = walk( value, look_for )
                if found:
                    return found
    return None


def get_location( zipcode ):
    """
    Get the geo location infor from a given zipcode
    :param zipcode: string: zipcode to look in
    :return: geo_info The geo location information in the Geolocate db
    """
    while zipcode.startswith('0'):
        zipcode = zipcode[1:]

    zip_info = Zipcode.get_one(**dict(ZIPCODE=zipcode))
    geo_info = Geolocate.get_all(**dict(COUNTY=zip_info.COUNTY.strip(), STATENAME=zip_info.STATENAME.strip()))
    return geo_info[0]


def get_formulary_id( plan_name, zipcode ):
    """
    Get the formulary_id for a plan
    :param plan_name: Full or partial name of a plan
    :param zipcode: zipcode for the plan
    :return: a formulary_id for that plan for that zipcode
    """
    plans = Plans.get_all(**dict(PLAN_NAME=plan_name))
    geo_info = get_location( zipcode )

    formulary_ids = []
    for plan in plans:
        if plan.CONTRACT_ID.startswith('S'):
            if plan.PDP_REGION_CODE == geo_info.PDP_REGION_CODE:
                formulary_ids.append(plan)

        elif plan.CONTRACT_ID.startswith('H'):
            if int(plan.COUNTY_CODE) == int(geo_info.COUNTY_CODE):
                formulary_ids.append(plan)

        elif plan.CONTRACT_ID.startswith('R'):
            if int(plan.MA_REGION_CODE) == geo_info.COUNTY_CODE:
                formulary_ids.append(plan)

    # There should only be one
    if len( formulary_ids ) == 1:
        return {"plan_name":formulary_ids[0].PLAN_NAME,
                "zipcode":zipcode,
                "formulary_id":formulary_ids[0].FORMULARY_ID
               }
    else:
        return "More than one found"


REGEX = '\[(.*?)\]'
def get_related_drugs(name):
    """
    Step one is search from the FTA DB and get from the xxx APIs for name
    :param proprietaryName: the proprietary name to look for
    :return: drugs that are the same class
    """
    drugs = set()
    excluded_front = []

    rx = RxClass()

    # There should only be one
    for fta in FTA.find_by_name(name):
        if fta.EXCLUDED_DRUGS_FRONT:
            excluded_front = [s.strip() for s in fta.EXCLUDED_DRUGS_FRONT.lower().split("|") if len(s) > 1]
        else:
            excluded_front = []

        if fta.EXCLUDED_DRUGS_BACK:
            excluded_back = [s.strip() for s in fta.EXCLUDED_DRUGS_BACK.lower().split("|")]
        else:
            excluded_back = []

        data = rx.byDrugName(drugName=fta.PROPRIETARY_NAME,
                             relaSource=fta.DRUG_RELASOURCE,
                             relas=fta.DRUG_RELA
                            )

        if fta.CLASS_ID:
            class_ids = [ fta.CLASS_ID ]
        else:
            class_ids = [ d['rxclassMinConceptItem']['classId'] for d in data['rxclassDrugInfo'] ]

        for class_id  in set(class_ids):

            if fta.DRUG_RELASOURCE == 'VA' and fta.DRUG_RELA in ['has_VAClass_extended', 'has_VAClass']:
                ttys = 'SBD+BPCK+GPCK'
            else:
                ttys = 'IN+MIN+PIN+BN'

            members = rx.classMembers(classId=class_id,
                                      relaSource=fta.DRUG_RELASOURCE,
                                      rela=fta.DRUG_RELA,
                                      ttys=ttys
                                      )

            drug_members = walk( members,'drugMemberGroup' )
            if not drug_members:
                log.error( f"No members of class {class_id}")
                continue

            for dm in drug_members['drugMember']:

                    look_for = dm['minConcept']['name']
                    if ttys == 'SBD+BPCK+GPCK':
                        try:
                            look_for =  re.findall(REGEX, look_for )[0]
                        except IndexError:
                            log.error( f"No brackets in {look_for}")
                            continue

                    if look_for.lower() in excluded_back:
                        continue

                    fta_members = FTA.find_by_name(look_for)
                    if not fta_members:
                        log.error("{} not found".format(look_for))
                        continue

                    for fta_member in fta_members:
                        #print(f"{fta_member.ID + 2} = {fta_member.PROPRIETARY_NAME}")
                        if not fta_member.PROPRIETARY_NAME in excluded_back and \
                           not fta_member.NONPROPRIETARY_NAME in excluded_back:
                            drugs.update([fta_member.PROPRIETARY_NAME])

    return drugs, excluded_front


def get_from_medicaid(drug_name, plan_name ):
    """

    :param drug_name: Name of the drug to find
    :param source: Source to look through
    :return:
    """

    collection = []
    results, exclude = get_related_drugs(drug_name)

    for drug_name in results:
        for clean_name in drug_name.split(' / '):
            clean_name = clean_name.strip()

            if plan_name.startswith("Caresource"):
                records = Caresource.find_by_name(clean_name)

            elif plan_name.startswith("Paramount"):
                records = Paramount.find_by_name(clean_name)

            elif plan_name.startswith("Molina"):
                records = Molina.find_by_name(clean_name)
                for record in records:
                    name = record['Generic_name']
                    name = name.split(',')[0] if ',' in name else name
                    if name.endswith("PA"):
                        more = Molina_Healthcare.find_brand(record['Brand_name'])

            elif plan_name.startswith("UHC"):
                records = UHC.find_by_name(clean_name)

            elif plan_name.startswith("Buckeye"):
                records = Buckeye.find_by_name(clean_name)

            else:
                log.error( f'Unknown plan name( {plan_name} )' )
                record = []

            if records:
                collection.extend(records)

    return collection, exclude