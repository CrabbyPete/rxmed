import arrow
import logging

from api import FDA
from rxnorm import RxNav
from models     import FTA, Database, Basic_Drugs, OpenNDC, Drugs
from tools import one_rxcui, get_related
#from settings   import DATABASE

DATABASE = 'postgresql+psycopg2://pete:d0cterd00m@rxmed.cespfzxrbadm.us-east-2.rds.amazonaws.com:5432/rxmed'
#DATABASE ='postgresql+psycopg2://petedouma:drd00m@127.0.0.1:5432/rxmed'

rx = RxNav()

def get_related(fta):
    """ Get the related drugs for an FTA entry
    :param fta: FTA record
    :return: list: fta ids that are related drugs
    """

    class_list = rx.getClassByRxNormDrugId(fta.RXCUI, relaSource='ATC')
    if not class_list:
        return []

    rxcui_list = []
    for ci in class_list:
        class_id = ci['rxclassMinConceptItem']['classId']
        members = rx.classMembers(class_id, relaSource='ATC') #, term_type = fta.TTY)
        if not members:
            continue
        for member in members:
            look_for = FTA.find_rxcui(int(member['minConcept']['rxcui']))
            if not look_for:
                logging.info(f"{member} not in FTA")
            rxcui_list.append(int(member['minConcept']['rxcui']))

    return set(rxcui_list)


def get_scdsbd(rxcui):
    """ Add the SCD or SCD rxcui to the drugs DB

    :param rxcui:
    :param brand_name:
    :param generic_name:
    :return:
    """

    # Get the TTY
    tty = None
    attributes = rx.getAllProperties(rxcui, prop='ATTRIBUTES')
    if attributes:
        for property in attributes:
            if property['propName'] == 'TTY':
                tty = property['propValue']
                break

    if not tty in ('SCD','SBD','GPCK','BPCK'):
        related_info = rx.getAllRelatedInfo(rxcui)
        ttys = {'SCD':[], 'SBD':[], 'GPCK':[], 'BPCK':[]}
        for info in related_info:
            if 'conceptProperties' in info and info['tty'] in ('SCD', 'SBD', 'GPCK', 'BPCK'):
                if info['tty'] == 'SCD':
                    ttys['SCD'].extend([int(cp['rxcui']) for cp in info['conceptProperties']])
                elif info['tty'] == 'SBD':
                    ttys['SBD'].extend([int(cp['rxcui']) for cp in info['conceptProperties']])
    return ttys


def second_pass():
    """ Get all the related drugs on a second pass
    :date the day to run this for
    :return:
    """
    for fta in FTA.session.query(FTA).filter(FTA.ACTIVE==False).order_by(FTA.id):
        related = get_related(fta)
        if related:
            related = [int(r) for r in related if FTA.find_rxcui(r)]
            fta.RELATED_DRUGS = related
            fta.save()


def job():
    fda = FDA()
    today = arrow.now()
    tday = today.format('YYYY-MM-DD')
    day=['2018-11-01',tday]

    # Search parameters for open fda
    product_type = "HUMAN PRESCRIPTION DRUG"
    marketing_category = set(['BLA','NDA'])

    limit = 100

    skip = 0
    stop = False
    while not stop:
        data = fda.open_fda(marketing_start_date=day,
                            product_type = product_type,
                            marketing_category = marketing_category,
                            limit=limit,
                            skip=skip)
        skip += len(data)
        if len(data)< limit:
            stop = True

        for item in data:

            if item['product_type'] == 'HUMAN OTC DRUG' or 'GAS' in item['dosage_form']:
                print(f"Excluding {item}")
                continue

            rxcui_list = item['openfda'].get('rxcui',[])
            for rxcui in rxcui_list:
                property = rx.getRxConceptProperties(rxcui)
                if property:
                    if property['tty'] in ('SCD','SBD'):
                        drug = Drugs.get(int(property['rxcui']))
                        if not drug:
                            params = dict(RXCUI=int(property['rxcui']),
                                          TTY=property['tty'],
                                          NAME=property['name']
                                          )
                            drug = Drugs(**params)
                            drug.save()
                            print(f"Saving new drug {drug}")
                else:
                    print(f"no properties for {rxcui}")
                    continue

            brand_name   = item.get("brand_name", None)
            generic_name = item.get("generic_name", None)
            print(f"{brand_name}:{generic_name}")

            if brand_name:
                fta = FTA.find_by_name(brand_name)
            elif generic_name:
                fta = FTA.find_by_name(generic_name)

            if not fta:
                fta = FTA( PROPRIETARY_NAME    = brand_name.lower(),
                           NONPROPRIETARY_NAME = generic_name.lower()
                         )

                rxcui_data = one_rxcui(brand_name, force=True)
                if rxcui_data:
                    fta.RXCUI = int(rxcui_data['RXCUI'])
                    fta.TTY = rxcui_data['TTY']
                    ttys = get_scdsbd(fta.RXCUI)
                    fta.SBD = ttys['SBD']
                    fta.SCD = ttys['SCD']
                    fta.CLASS_ID = rxcui_data.get('CLASS_ID', None)
                    fta.CLASS_NAME = rxcui_data.get('CLASS_NAME', None)
                    fta.ACTIVE = False
                    fta.RELATED_DRUGS = get_related(fta)
                    fta.save()



if __name__ == "__main__":
    with Database( DATABASE ) as db:
        job()
        second_pass()
"""
schedule.every().day.at("20:00").do(job)


while True:
    schedule.run_pending()
    time.sleep(1)
"""

