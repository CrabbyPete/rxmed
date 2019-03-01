import re
import pandas as pd

from functools       import lru_cache
from log             import log, log_msg
from models          import Zipcode, Plans, FTA
from api             import RxClass, RxNorm, RxTerm


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
def get_location(zipcode):
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


def get_rxcui( drug_name, tty='IN', relasource=None, rela=None):
    """ Get the tty:IN rxcui for a drug name
    :param drug_name:
    :return:
    """
    rxnorm = RxNorm()
    rxclass = RxClass()

    rxcui = rxnorm.findRxcuiByString(drug_name,)
    if not rxcui:
        guess = rxnorm.getApproximateMatch(drug_name)
        if guess:
            try:
                rxcui = guess['candidate'][0]['rxcui']
            except:
                log.error(f"No rxcui found for {drug_name}")
                return None
        else:
            log.error(f"No rxcui found for {drug_name}")
            return None
    else:
        rxcui = rxcui[0]

    # Get the drug class for this rxcui
    drug_classes = rxclass.getClassByRxNormDrugId(rxcui, relasource, rela)

    # Get all related info and look for the tty:
    records = rxnorm.getAllRelatedInfo(rxcui)
    if not records:
        log.error(f"No AllRelatedInfo for {drug_name}:{rxcui}")
        return None

    results = []
    for record in records:
        if not (record['tty'] == tty and 'conceptProperties' in record):
            continue

        for prop in record['conceptProperties']:
            if not prop['tty'] == tty:
                continue

            params = dict(RXCUI=prop['rxcui'],
                          PROPRIETARY_NAME=drug_name,
                          TTY=tty,
                          RELASOURCE=relasource,
                          RELA=rela
                          )
            drug_classes = rxclass.getClassByRxNormDrugId(prop['rxcui'], relasource, rela)

            if drug_classes:
                for dc in drug_classes:
                    if not dc['minConcept']['tty'] == tty:
                        continue

                    params['CLASS_ID'] = dc['rxclassMinConceptItem']['classId']
                    params['CLASS_NAME'] = dc['rxclassMinConceptItem']['className']

            results.append(params)

    if len(results) == 1 and not 'CLASS_ID' in params:
        if drug_classes and len(drug_classes) == 1:
            params['CLASS_ID'] = drug_classes[0]['rxclassMinConceptItem']['classId']
            params['CLASS_NAME'] = drug_classes[0]['rxclassMinConceptItem']['className']

    if len(results) > 1:
        results = pd.DataFrame(results).drop_duplicates().to_dict('records')
    return results


def one_rxcui(name, relaSource=None, rela=None):
    """ Only return 1 rxcui either IN or MIN
    :param name:
    :param tty:
    :param relasource:
    :param rela:
    :return:
    """
    if redis;
        if name in redis:
            return redis

    rxclass = RxClass()

    tty = 'IN'
    results = get_rxcui(name, tty, relaSource, rela)
    if not results or len(results) > 1:
        tty = 'MIN'
        results = get_rxcui(name, tty, relaSource, rela)
        if not results or len(results) > 1:
            return None

    result = results[0]
    try:
        result['RXCUI'] = int(result['RXCUI'])
    except Exception as e:
        result['RXCUI'] = None


    return result


REGEX = '[\\[\\(](.*?)[\\]\\)]' #Brackets and parenthesis
#REGEX = "\\[(.*?)\\]"

def get_related_class(rxcui, class_id = None, relaSource = None, rela = None):
    rxclass = RxClass()
    rxnorm  = RxNorm()

    def get_class_id(rxcui):
        for record in rxnorm.getAllRelatedInfo(rxcui):
            if record['tty'] in ['IN', 'MIN'] and record['conceptProperties']:
                rxcui = record['conceptProperties'][0]['rxcui']
                tty = record['tty']
                break

        class_id = rxclass.getClassByRxNormDrugId(rxcui)
        return class_id

    related = []
    if not class_id:
        class_id = get_class_id(rxcui)

    members = rxclass.classMembers(class_id, relaSource, rela)
    if not members:
        class_id = get_class_id(rxcui)
        members = rxclass.classMembers(class_id)
        return []


    names = []
    for member in members:
        m_rxcui = member['minConcept']['rxcui']
        fta_list = FTA.session.query(FTA).filter(FTA.RXCUI == m_rxcui).all()
        for fta in fta_list:
            names.append(fta.PROPRIETARY_NAME)
            related.append(fta.id)

    return related


def get_related_drugs(name, force = False ):
    """
    Step one is search from the FTA DB and get from the xxx APIs for name
    :param proprietaryName: the proprietary name to look for
    :return: drugs that are the same class
    """
    rx = RxClass()

    # There should only be one
    name = name.split()[0].lower()
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

            if fta.DRUG.CLASS_ID:
                class_id = fta.DRUG.CLASS_ID
            else:
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

                class_id = walk(data,'classId')
                if not class_id:
                    log.info("No CLASS_ID for {}".format( fta.PROPRIETARY_NAME, fta.NONPROPRIETARY_NAME))
                    continue

            # Get the class members
            members = rx.classMembers(classId=class_id,
                                      relaSource=fta.DRUG_RELASOURCE,
                                      rela=fta.DRUG_RELA,
                                      ttys=fta.DRUG.TTY
                                     )

            va = True if fta.DRUG_RELASOURCE == 'VA' and fta.DRUG_RELA in ['has_VAClass_extended', 'has_VAClass'] else False
            if members:
                drug_names = []
                for dm in members:
                    look_for = dm['minConcept']['name']
                    if va:
                        try:
                            look_for = re.findall(REGEX, look_for)[0]
                        except IndexError:
                            look_for = dm['nodeAttr'][1]['attrValue']
                            for node in dm['nodeAttr']:
                                if node['attrName'] == 'SourceName':
                                    if node['attrValue']:
                                        look_for = node['attrValue'].split()[0]
                                        break
                            else:
                                log.info(log_msg(f"No brackets in {fta.PROPRIETARY_NAME}:<{look_for}>"))
                                continue

                    drug_names.append(look_for)

                for drug_name in set(drug_names):
                    drug = drug_name.lower()

                    fta_members = fta.find_by_name(drug)
                    if not fta_members:
                        log.info("{} not found in FTA".format(look_for))
                        #inactive = FTA.get_or_create(**{'PROPRIETARY_NAME':look_for,"ACTIVE":False})
                        #inactive.save()
                        continue

                    for fta_member in fta_members:
                        if not fta_member.ACTIVE:
                            continue

                        for xb in excluded_back:
                            if xb in fta_member.PROPRIETARY_NAME or xb in fta_member.NONPROPRIETARY_NAME:
                                break
                        else:
                           #print(fta.PROPRIETARY_NAME,fta.NONPROPRIETARY_NAME)
                            drug_list.update([fta_member.id])

    return drug_list, excluded_front


if __name__ == "__main__":
    from settings      import DATABASE
    from models.base   import Database

    with Database(DATABASE) as db:
        results = get_related_drugs('flovent', force=True)
        """
        for fta in FTA.get_all():
            results = get_related_drugs(fta.PROPRIETARY_NAME, force=True)
            for result in results[0]:
                fta_related = FTA.get(result)
                print(f"{fta.PROPRIETARY_NAME},{fta_related.PROPRIETARY_NAME},{fta_related.NONPROPRIETARY_NAME}")
        """



