import re

from functools       import lru_cache
from log             import log, log_msg
from models          import Zipcode, Plans, FTA
from api             import RxClass


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


@lru_cache(4096)
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

@lru_cache(4096)
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

REGEX = '[\[\(](.*?)[\]\)]'

def get_related_drugs(name, force = False ):
    """
    Step one is search from the FTA DB and get from the xxx APIs for name
    :param proprietaryName: the proprietary name to look for
    :return: drugs that are the same class
    """
    rx = RxClass()

    # There should only be one
    fta_list = FTA.find_by_name(name)

    excluded_front = set()
    drug_list = set()

    for fta in fta_list:

        # Skip the whole back end if it was already done
        if not fta.RELATED_DRUGS is None and force == False:
            drug_list.update([f for f in fta.RELATED_DRUGS] )
            if fta.EXCLUDED_DRUGS_FRONT:
                excluded_front.update([s.strip() for s in fta.EXCLUDED_DRUGS_FRONT.lower().split("|") if s.strip()])

        # Find the drug and related drugs using the API
        else:
            if fta.EXCLUDED_DRUGS_FRONT:
                excluded_front.update([s.strip() for s in fta.EXCLUDED_DRUGS_FRONT.lower().split("|") if s.strip()])


            if fta.EXCLUDED_DRUGS_BACK:
                excluded_back = [s.strip() for s in fta.EXCLUDED_DRUGS_BACK.lower().split("|") if s.strip()]
            else:
                excluded_back = []

            # Look by the proprietary name
            data = rx.byDrugName(drugName=fta.PROPRIETARY_NAME,
                                 relaSource=fta.DRUG_RELASOURCE,
                                 relas=fta.DRUG_RELA
                                )
            # If nothing found look by non-proprietary name
            if not data:
                data = rx.byDrugName(drugName=fta.NONPROPRIETARY_NAME,
                                     relaSource=fta.DRUG_RELASOURCE,
                                     relas=fta.DRUG_RELA
                                    )
            # Still nothing skip it
            if not data:
                log.error( "No data found for {} or {}".format( fta.PROPRIETARY_NAME, fta.NONPROPRIETARY_NAME) )
                continue

            if fta.CLASS_ID:
                class_id = fta.CLASS_ID 
            else:
                class_id = walk(data,'classId')
                fta.CLASS_ID = class_id
                fta.save()
    
            if fta.DRUG_RELASOURCE == 'VA' and fta.DRUG_RELA in ['has_VAClass_extended', 'has_VAClass']:
                ttys = 'SCD+SBD+BPCK+GPCK'
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

            drug_names = []
            for dm in drug_members['drugMember']:
                look_for = dm['minConcept']['name']
                if ttys == 'SCD+SBD+BPCK+GPCK':
                    try:
                        look_for =  re.findall(REGEX, look_for )[0]
                    except IndexError:
                        look_for = look_for.split()[0]

                        #log.error( log_msg( f"No brackets in {origin} using {look_for}") )
                drug_names.append( look_for )

            for drug_name in set(drug_names):
                drug = drug_name.lower()

                fta_members = fta.find_by_name(drug)
                if not fta_members:
                    log.error( log_msg("{} not found in FTA".format(look_for)) )
                    inactive = FTA(**{'PROPRIETARY_NAME':look_for,"ACTIVE":False})
                    inactive.save()
                    continue

                for fta_member in fta_members:
                    if not fta_member.ACTIVE:
                        continue

                    #print(f"{fta_member.id} = {fta_member.PROPRIETARY_NAME}")
                    for xb in excluded_back:
                        if xb in fta_member.PROPRIETARY_NAME or xb in fta_member.NONPROPRIETARY_NAME:
                            break
                    else:
                        drug_list.update([fta_member.id])

    return drug_list, excluded_front


if __name__ == "__main__":
    from settings      import DATABASE
    from models.base   import Database

    with Database(DATABASE) as db:
        for fta in FTA.get_all():
            results = get_related_drugs(fta.PROPRIETARY_NAME, force=True)
            for result in results[0]:
                fta_related = FTA.get(result)
                print(f"{fta.PROPRIETARY_NAME},{fta_related.PROPRIETARY_NAME},{fta_related.NONPROPRIETARY_NAME}")




