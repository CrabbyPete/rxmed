import re
import sys
import logging

from api import RxClass, RxNorm


from models.fta import FTA
from models.plans import Caresource, Paramount, Molina, Molina_Healthcare, UHC, Buckeye

Rxclass = RxClass()
Rxnorm = RxNorm()



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

REGEX = '\[(.*?)\]'

def get_related_drugs(name):
    """
    Step one is search from the FTA DB and get from the xxx APIs for name
    :param proprietaryName: the proprietary name to look for
    :return: drugs that are the same class
    """
    drugs = set()

    for fta in FTA.find_by_name(name):

        excluded_back  = [s.strip() for s in fta.EXCLUDED_DRUGS_BACK.lower().split("|")] if fta.EXCLUDED_DRUGS_BACK else []
        excluded_front = [s.strip() for s in fta.EXCLUDED_DRUGS_FRONT.lower().split("|")] if fta.EXCLUDED_DRUGS_FRONT else []

        data = Rxclass.byDrugName(drugName=fta.PROPRIETARY_NAME,
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

            members = Rxclass.classMembers(classId=class_id,
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


def get_medicaid(name, source):
    """

    :param name: Name of the drug to find
    :param source: Source to look through
    :return:
    """

    collection = []
    results, exclude = get_related_drugs(name)

    for drug_name in results:
        for clean_name in drug_name.split(' / '):
            clean_name = clean_name.strip()

            if source == "Caresource":
                records = Caresource.find_by_name(clean_name)

            elif source == "Paramount":
                records = Paramount.find_by_name(clean_name)

            elif source == "Molina":
                records = Molina.find_by_name(clean_name)
                for record in records:
                    name = record['Generic_name']
                    name = name.split(',')[0] if ',' in name else name
                    if name.endswith("PA"):
                        more = Molina_Healthcare.find_brand(record['Brand_name'])

            elif source == "UHC":
                records = UHC.find_by_name(clean_name)

            elif source == "Buckeye":
                records = Buckeye.find_by_name(clean_name)

            else:
                log.error( f'Unknown source {source}' )
                record = []

            if records:
                collection.extend(records)

    return collection, exclude




if __name__ == "__main__":
    get_medicaid("Admelog", "Caresource" )
    # main("Pamidronate Disodium", "Caresource") # CLASS_ID != NULL
    # main("Tresiba", "Paramount")
    # main("Advair", "Paramount")
    # main("epinephrine", "Paramount")
    # main("Potassium Citrate", "Caresource")
    # main("Zanaflex", "Caresource")
    # main("Trelegy", "Caresource")
    # main("Breo","Caresource")
    # main('Symbicort','Molina')
    # main('ARTHROTEC','Molina')
    #app.run(host='0.0.0.0')
