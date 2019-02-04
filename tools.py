import re

from functools  import lru_cache
from log        import log, log_msg
from models     import Zipcode, Plans, Basic_Drugs,Beneficiary_Costs, NDC, FTA
from api        import RxClass


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
        zipcode = Zipcode.session.query(Zipcode).filter( Zipcode.ZIPCODE == zipcode ).one()
    except Exception as e:
        log.error( log_msg(str(e)) )
        return None

    return zipcode


def get_plan( plan_name, zipcode ):
    """
    Get the formulary_id for a plan
    :param plan_name: Full or partial name of a plan
    :param zipcode: zipcode for the plan
    :return: a formulary_id for that plan for that zipcode
    """
    zipcode  = get_location( zipcode )
    plans = Plans.find_by_plan_name(plan_name, geo=zipcode.GEO.id)

    # There should only be one
    if len( plans ) == 1:
        return plans[0]

    else:
        return "More than one found"

REGEX = '\[(.*?)\]'

@lru_cache( 1024 )
def get_related_drugs(name):
    """
    Step one is search from the FTA DB and get from the xxx APIs for name
    :param proprietaryName: the proprietary name to look for
    :return: drugs that are the same class
    """
    results = set()
    excluded_front = []

    rx = RxClass()

    # There should only be one
    fta_list = FTA.find_by_name(name)
    for fta in fta_list:
        try:
            excluded = []
            if not fta.RELATED_DRUGS is None:
                if fta.EXCLUDED_DRUGS_FRONT:
                    excluded = [ f.trim() for f in fta.EXCLUDED_DRUGS_FRONT.lower().split("|")]

                return fta.RELATED_DRUGS, excluded
        except:
            pass


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

                    fta_members = fta.find_by_name(look_for)
                    if not fta_members:
                        log.error( log_msg("{} not found in FTA".format(look_for)) )
                        continue

                    for fta_member in fta_members:
                        #(f"{fta_member.id} = {fta_member.PROPRIETARY_NAME}")

                        if not fta_member.PROPRIETARY_NAME in excluded_back and \
                           not fta_member.NONPROPRIETARY_NAME in excluded_back:
                            results.update([fta_member.id])

    return results, excluded_front


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


if __name__ == "__main__":
    from settings      import DATABASE
    from models.base   import Database

    with Database(DATABASE) as db:
        # get_location('07481')
        # get_from_medicare( "Victoza", "Anthem MediBlue Essential (HMO)", '43202')
        result = get_from_medicare('Levemir','SilverScript Plus (PDP)','07040')
        #result = get_from_medicaid('Levemir','UHC Community')
        #result = get_from_medicare( "SYMBICORT","Silverscript choice (PDP)","07040")


        print(result)



