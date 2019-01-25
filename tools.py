import re

from log          import log, log_msg

from models       import db
from models.geo   import Zipcode, Geolocate
from models.ndc   import NDC, Plans, Basic_Drugs,Beneficiary_Costs
from models.fta   import FTA
from models.plans import Caresource, Paramount, Molina, Molina_Healthcare, UHC, Buckeye

from api          import RxClass, OhioState

from sqlalchemy.orm import join

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
    try:
        zipcode = Zipcode.find_one( zipcode )
    except Exception as e:
        log.error( log_msg(str(e)) )
        return None

    return zipcode


def get_formulary_id( plan_name, zipcode ):
    """
    Get the formulary_id for a plan
    :param plan_name: Full or partial name of a plan
    :param zipcode: zipcode for the plan
    :return: a formulary_id for that plan for that zipcode
    """
    plans = Plans.find_by_plan_name(plan_name)
    zipcode  = get_location( zipcode )

    formulary_ids = []
    for plan in plans:
        if plan['CONTRACT_ID'].startswith('S'):
            if int(plan['PDP_REGION_CODE']) == zipcode.GEO.PDP_REGION_CODE:
                formulary_ids.append(plan)

        elif plan['CONTRACT_ID'].startswith('H'):
            if int(plan['COUNTY_CODE']) == int(zipcode.GEO.COUNTY_CODE):
                formulary_ids.append(plan)

        elif plan['CONTRACT_ID'].startswith('R'):
            if int(plan['MA_REGION_CODE']) == zipcode.GEO.COUNTY_CODE:
                formulary_ids.append(plan)

    # There should only be one
    if len( formulary_ids ) == 1:
        return  formulary_ids[0]

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
        if fta.RELATED_DRUGS:
            if fta.EXCLUDED_DRUGS_FRONT:
                exclude = fta.EXCLUDED_DRUGS_FRONT.lower().split("|")
            else:
                exclude = []
            return fta.RELATED_DRUGS.split(';'), exclude

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
        if not data:
            data = rx.byDrugName(drugName=fta.NONPROPRIETARY_NAME,
                                 relaSource=fta.DRUG_RELASOURCE,
                                 relas=fta.DRUG_RELA
                                )
            if not data:
                log.error( "No data found for {} or {}".format( fta.PROPRIETARY_NAME, fta.NONPROPRIETARY_NAME) )
                return [], None
            
            
        if fta.CLASS_ID:
            class_ids = [ fta.CLASS_ID ]
        else:
            try:
                class_ids = [ d['rxclassMinConceptItem']['classId'] for d in data['rxclassDrugInfo'] ]
            except:
                class_ids = []

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
                log.error( log_msg(f"No members of class {class_id}") )
                continue

            for dm in drug_members['drugMember']:

                    look_for = dm['minConcept']['name']
                    if ttys == 'SBD+BPCK+GPCK':
                        try:
                            look_for =  re.findall(REGEX, look_for )[0]
                        except IndexError:
                            log.error( log_msg( f"No brackets in {look_for}") )
                            continue

                    if look_for.lower() in excluded_back:
                        continue

                    fta_members = FTA.find_by_name(look_for)
                    if not fta_members:
                        log.error( log_msg("{} not found in FTA".format(look_for)) )
                        continue

                    for fta_member in fta_members:
                        #print(f"{fta_member.ID + 2} = {fta_member.PROPRIETARY_NAME}")
                        if not fta_member.PROPRIETARY_NAME in excluded_back and \
                           not fta_member.NONPROPRIETARY_NAME in excluded_back:
                            drugs.update([fta_member.PROPRIETARY_NAME])

    return drugs, excluded_front


def get_ndc( proprietary_name, dose_strength = None, dose_unit = None ):
    """

    :param self:
    :param proprietary_name:
    :param dose_strength:
    :param dose_unit:
    :return:
    """
    qry = dict( PROPRIETARY_NAME=proprietary_name )
    if dose_strength:
        qry.update( dict(PROPRIETARY_NAME=proprietary_name) )
    if dose_unit:
        qry.update( dict(DOSE_UNIT=dose_unit) )

    drugs = NDC.get_all(**qry )
    return drugs 


def beneficiary_costs( drug, plan ):
    """
    Get the beneficary costs for a drug in plan
    :param drugs:
    :return:“COST_AMT_PREF” ONLY if “DAYS_SUPPLY” = 1 and “COST_TYPE_PREF” = 1, for each “COVERAGE_LEVEL” 0 AND 1
    """
    drug = int(drug.replace("-",""))
    bd = Basic_Drugs.get_close_to(drug, plan['FORMULARY_ID'])
    try:
        if len( bd ) > 1:
            log.error( log_msg(f"{drug}-{plan['FORMULARY_ID']} returned more than 1 value"))

        bd = bd[0]
    except IndexError:
        log.error(f"No Basic Drug for {drug}-{plan['FORMULARY_ID'] }")
        return None,None

    benefit_costs = Beneficiary_Costs.get_all( **dict( CONTRACT_ID    = plan['CONTRACT_ID'],
                                                       PLAN_ID        = int(plan['PLAN_ID']),
                                                       SEGMENT_ID     = int(plan['SEGMENT_ID']),
                                                       TIER           = int(bd['TIER_LEVEL_VALUE']),
                                                       DAYS_SUPPLY    = 1,
                                                       COST_TYPE_PREF = 1
                                                     )
                                             )
    bc = [c for c in benefit_costs if c.COVERAGE_LEVEL in (1,0) ]
    return bd, bc


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

            if plan_name.lower().startswith("caresource"):
                records = Caresource.find_by_name(clean_name)

            elif plan_name.lower().startswith("paramount"):
                records = Paramount.find_by_name(clean_name)

            elif plan_name.lower().startswith("molina"):
                records = Molina.find_by_name(clean_name)
                """
                if (Generic_name) has a capital word “PA”, 
                  then retrieve its respective column B (Brand_name) [2018 Molina PDL 10_9_18]. 
                  Match (first word match), to [Molina Healthcare PA criteria 10_1_18].DRUG_NAME). 
                """
                for record in records:
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

            elif plan_name.lower().startswith('oh'):
                records = OhioState(clean_name)

            elif plan_name.lower().startswith("uhc "):
                records = UHC.find_by_name(clean_name)

            elif plan_name.lower().startswith("buckeye"):
                records = Buckeye.find_by_name(clean_name)

            else:
                log.error( log_msg(f'Unknown plan name( {plan_name} )' ))
                records = []

            if records:
                collection.extend(records)

    return collection, exclude


def get_from_medicare(drug_name, plan_name, zipcode=None ):
    """

    :param drug_name:
    :param plan_name:
    :return:
    """
    
    drug_list, exclude = get_related_drugs(drug_name)
    plan = get_formulary_id(plan_name, zipcode)
    
    results = []

    for drug in drug_list:
        ndc_list = NDC.find_by_name( drug )
        for ndc in ndc_list:
            bd, bc = beneficiary_costs(ndc.PRODUCT_NDC, plan)
        
            if not bd:
                pa = 'Yes'
                ql = ''
                st = ''
                copay_p = ''
                copay_d = ''
                tier = ''
            else:
                if bd['PRIOR_AUTHORIZATION_YN'] == 'False':
                    pa = 'No'
                else:
                    pa = 'Yes'

                if bd['STEP_THERAPY_YN'] == 'False':
                    st = 'No'
                else:
                    st = 'Yes'

                if bd['QUANTITY_LIMIT_YN'] == 'True':
                    ql = f"Yes {bd['QUANTITY_LIMIT_AMOUNT']}:{bd['QUANTITY_LIMIT_DAYS']}"
                else:
                    ql = f"No"
                try:
                    tier    = bc[0].TIER
                except IndexError:
                    tier = bd['TIER_LEVEL_VALUE']
                
                copay_d = ''
                copay_p = ''
                if bc:
                    for c in bc:
                        if c.COVERAGE_LEVEL == 0:
                            copay_p = "{:.2f}".format(c.COST_AMT_PREF)
                        if c.COVERAGE_LEVEL == 1:
                            copay_d =  "{:.2f}".format(c.COST_AMT_PREF)
            
            result = { 'Brand'  : ndc.PROPRIETARY_NAME,
                       'Generic': ndc.NONPROPRIETARY_NAME,
                       'Tier'   : tier,
                       'ST'     : st,
                       'QL'     : ql,
                       'PA'     : pa,
                       'CopayP' :copay_p,
                       'CopayD' :copay_d
                     }
        
        results.append( result )
    
    return results

if __name__ == "__main__":
    #get_location('07481')
    get_from_medicare( "Victoza", "Anthem MediBlue Essential (HMO)", '43202')
    #get_from_medicare('Levemir','Silverscript plus (PDP)','07040')
    # get_from_medicare( "SYMBICORT","Silverscript choice (PDP)","07040")
    # get_from_medicaid("Admelog", "Caresource" )
    # get_from_medicaid("Breo","Ohio State")
    # get_from_medicaid("Trulicity","OH State Medicaid")
    # main("Pamidronate Disodium", "Caresource") # CLASS_ID != NULL
    # main("Tresiba", "Paramount")
    # main("Advair", "Paramount")
    # main("epinephrine", "Paramount")
    # main("Potassium Citrate", "Caresource")
    # main("Zanaflex", "Caresource")
    # main("Trelegy", "Caresource")
    # main("Breo","Caresource")
    # main('Symbicort','Molina')
    # get_from_medicaid('ARTHROTEC','Molina')


