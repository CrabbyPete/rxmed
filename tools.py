import pandas as pd

from log import log, log_msg
from models          import Zipcode, Plans, FTA, Drugs
from api import RxClass, RxNorm


# Share this exception
class BadPlanName(Exception):
    """
    A bad plan name was entered
    """

class BadLocation(Exception):
    """
    A bad zipcode was entered
    """


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
        raise BadLocation( f"Unknown zipcode {zipcode} location")

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
        raise BadPlanName(f"Plan {plan_name} in {zipcode} not found")

def get_rxcui( drug_name, tty='IN', relasource=None, rela=None):
    """ Get the tty:IN rxcui for a drug name
    :param drug_name:
    :return:
    """
    rxnorm = RxNorm()
    rxclass = RxClass()

    rxcui = rxnorm.findRxcuiByString(drug_name)
    if not rxcui:

        # Try and guess the best answer
        guesses = rxnorm.getApproximateMatch(term=drug_name, maxEntries=12, option=0)
        for guess in guesses.get('candidate',[]):
            data = rxnorm.getAllProperties(guess['rxcui'], prop='NAMES')
            if data:
                try:
                    name = [d['propValue'] for d in data if 'RxNorm Name' in d['propName']]
                    rxcui = rxnorm.findRxcuiByString(name[0])[0]
                except:
                    pass
            else:
                try:
                    rxcui = int(guess['rxcui'])
                except:
                    log.error(f"No rxcui found for {drug_name}")

            related = rxnorm.getRelatedByType(rxcui, tty=['IN','MIN'])
            if related:
                break
        else:
            log.error(f"No rxcui found for {drug_name}")
            return None
    else:
        rxcui = int(rxcui[0])
        related = rxnorm.getRelatedByType(rxcui, tty=['IN','MIN'])

    try:
        related = [ group['conceptProperties'] for group in related['conceptGroup']\
                    if group.get('conceptProperties',None) and group['tty'] == tty]
    except TypeError:
        log( log_msg(f"TypeError for {drug_name}"))
        related = None

    results = []
    if related:
        if len( related ) > 1:
            log(log_msg(f"More than one related for {drug_name}"))

        # There should only ever be 1 related
        for property in related[0]:
            params = dict(RXCUI=property['rxcui'],
                          PROPRIETARY_NAME=drug_name,
                          TTY=tty,
                          RELASOURCE=relasource,
                          RELA=rela
                        )

            drug_classes = rxclass.getClassByRxNormDrugId(property['rxcui'], relasource, rela)
            if drug_classes:
                for dc in drug_classes:
                    if not dc['minConcept']['tty'] == tty:
                        continue

                    params['CLASS_ID'] = dc['rxclassMinConceptItem']['classId']
                    params['CLASS_NAME'] = dc['rxclassMinConceptItem']['className']

            results.append(params)

    if len(results) > 1:
        results = pd.DataFrame(results).drop_duplicates().to_dict('records')
    return results


def one_rxcui(name, relaSource=None, rela=None, force=False):
    """ Only return 1 rxcui either IN or MIN
    :param name:
    :param tty:
    :param relasource:
    :param rela:
    :return:
    """
    rxclass = RxClass()

    if not force:
        drug = Drugs.get_one( **dict(NAME = name, RELASOURCE =relaSource, RELA = rela) )
        if drug:
            return dict( RXCUI=drug.RXCUI, TTY=drug.TTY, CLASS_ID=drug.CLASS_ID, CLASS_NAME=drug.NAME )

    tty = 'IN'
    results = get_rxcui(name, tty, relaSource, rela)

    # If you did not find an IN try to get a MIN
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

    save = result.copy()

    save['NAME'] = save.pop('PROPRIETARY_NAME')
    #drug = Drugs.get_or_create(**save)
    #drug.save()

    return result


def get_related(fta):
    """ Get the related drugs for an FTA entry
    :param fta: FTA record
    :return: list: fta ids that are related drugs
    """
    rxnorm = RxNorm()
    rxclass = RxClass()

    rxcui_list = set()

    if fta.EXCLUDED_DRUGS_BACK:
        excluded_back = [s.strip() for s in fta.EXCLUDED_DRUGS_BACK.lower().split("|") if s.strip()]
    else:
        excluded_back = []

    rxcuis = None
    if fta.CLASS_ID:
        members = rxclass.classMembers(fta.CLASS_ID,relaSource='ATC',ttys=[fta.TTY])
        try:
            rxcuis = [m['minConcept']['rxcui'] for m in members if m['minConcept']['tty'] in ['MIN', 'IN']]
        except TypeError:
            pass
        else:
            print(f"member:{members}")

    if not rxcuis:
        rxcuis = []
        class_list = rxclass.getClassByRxNormDrugId(fta.RXCUI)
        if class_list:
            class_min_ids = [c['minConcept']['rxcui'] for c in class_list if c['minConcept']['tty'] == 'MIN']
            class_in_ids = [c['minConcept']['rxcui'] for c in class_list if c['minConcept']['tty'] == 'IN']
            if class_min_ids:
                rxcuis = set(class_min_ids)
            else:
                rxcuis = set(class_in_ids)


    # Find all the members back in the FTA table
    for rxcui in set(rxcuis):

        fta_members = fta.find_rxcui(int(rxcui))
        if not fta_members:
            log.info(f"{rxcui} not found in FTA")
            continue

        # If its not active skip it
        for fta_member in fta_members:
            '''
            if not fta_member.ACTIVE:
                continue
            '''
            # If its in the excluded back skip it
            for xb in excluded_back:
                if xb in fta_member.PROPRIETARY_NAME or xb in fta_member.NONPROPRIETARY_NAME:
                    break
            else:
                rxcui_list.update([fta_member.RXCUI])

    return rxcui_list


def get_related_drugs(name, force = False ):
    """
    Step one is search from the FTA DB and get from the xxx APIs for name
    :param proprietaryName: the proprietary name to look for
    :return: rxcui_list of drugs that are the same class
    """
    rx = RxClass()

    # There should only be one
    name = name.split()[0].lower()
    fta_list = FTA.find_by_name(name)

    drug_list = set()

    # Look at each fta entry
    for fta in fta_list:

        if fta.RXCUI:
            drug_list.update([fta.RXCUI])

        # Skip the whole back end if it was already done
        if fta.RELATED_DRUGS is None or force == True:
            drug_list.update(get_related(fta))
        else:
            drug_list.update([f for f in fta.RELATED_DRUGS] )

    return drug_list


if __name__ == "__main__":
    from settings      import DATABASE
    from models.base   import Database

    with Database(DATABASE) as db:
        results = one_rxcui('lidothol','VA','has_VAclass_Extended', force=True)
        """
        for fta in FTA.get_all():
            results = get_related_drugs(fta.PROPRIETARY_NAME, force=True)
            for result in results[0]:
                fta_related = FTA.get(result)
                print(f"{fta.PROPRIETARY_NAME},{fta_related.PROPRIETARY_NAME},{fta_related.NONPROPRIETARY_NAME}")
        """



