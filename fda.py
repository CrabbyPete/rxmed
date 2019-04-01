import time
import arrow
import schedule

from api        import FDA, RxNorm
from models     import OpenNDC, FTA, Database, Basic_Drugs
from tools      import related_drugs, one_rxcui, get_related
from settings   import DATABASE




def match_fta_ndc(fta):
    """ Find all the NDC that match this FTA record
    :param fta: a record in the fta
    :return: list of ndc_id
    """
    rxnorm = RxNorm()

    if not fta.RXCUI:
        return None

    ndc_list = []
    related = rxnorm.getRelatedByType(fta.RXCUI,tty=['SBD'])
    try:
        for rel in related['conceptGroup'][0]['conceptProperties']:
            if Basic_Drugs.get_by_rxcui(rel['rxcui']):
                ndc_list.append(int(rel['rxcui']))
    except Exception as e:
        print(fta, str(e))

    if not ndc_list:
        print(f"{fta.PROPRIETARY_NAME}:{fta.NONPROPRIETARY_NAME} not in basic drugs")
    return ndc_list


def second_pass(date):
    """ Get all the related drugs on a second pass
    :date the day to run this for
    :return:
    """
    for fta in FTA.session.query(FTA).filter(FTA.MODIFIED == date).order_by(FTA.id):
        related = related_drugs(fta.PROPRIETARY_NAME)
        if related:
            related = [int(r) for r in related if FTA.find_rxcui(r)]
            fta.RELATED_DRUGS = related

        fta.SBD_RXCUI = match_fta_ndc(fta)
        fta.save()


def job():
    fda = FDA()
    today = arrow.now()
    tday = today.format('YYYY-MM-DD')
    day=['2018-11-18',tday]

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
            brand_name   = item.get("brand_name", None)
            generic_name = item.get("generic_name", None)
            print(f"{brand_name}:{generic_name}")

            ndc = OpenNDC.get_or_create(product_ndc  = item["product_ndc"],
                                        brand_name   = brand_name,
                                        generic_name = generic_name
                                        )

            if not ndc.id:
                rxcui_list = item['openfda'].get("rxcui", None)
                if rxcui_list:
                    ndc.rxcui = [int(rxcui) for rxcui in rxcui_list]

                ndc.brand_name_base = item.get('brand_name_base', None)
                ndc.product_type = item.get('product_type', None)
                ndc.route = item.get('route', None)
                ndc.pharm_class = item.get('pharm_class', None)
                ndc.packaging = item.get('packaging', None)
                ndc.active_ingredients = item.get('active_ingredients', None)
                ndc.save()

            fta = FTA.find_by_name(brand_name)
            if not fta:
                fta = FTA( PROPRIETARY_NAME    = brand_name.lower(),
                           NONPROPRIETARY_NAME = generic_name.lower()
                         )

                rxcui_data = one_rxcui(brand_name, force=True)
                if rxcui_data:
                    fta.RXCUI = int(rxcui_data['RXCUI'])
                    fta.TTY = rxcui_data['TTY']
                    fta.CLASS_ID = rxcui_data.get('CLASS_ID', None)
                    fta.CLASS_NAME = rxcui_data.get('CLASS_NAME', None)

                ndc_list = match_fta_ndc(fta)
                fta.SBD_RXCUI = ndc_list

                fta.ACTIVE = False
                fta.save()




if __name__ == "__main__":
    with Database( DATABASE ) as db:
        #job()
        day = arrow.get('2019-03-14')
        second_pass(day.date())
"""
schedule.every().day.at("20:00").do(job)


while True:
    schedule.run_pending()
    time.sleep(1)
"""

