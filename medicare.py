import pandas as pd

from functools  import lru_cache

from tools      import get_related_drugs, get_plan
from log        import log, log_msg
from models.ndc import Basic_Drugs, Beneficiary_Costs
from models.fta import FTA, NDC

@lru_cache(8192)
def beneficiary_costs(drug, plan):
    """
    Get the beneficary costs for a drug in plan
    :param drugs:
    :return:“COST_AMT_PREF” ONLY if “DAYS_SUPPLY” = 1 and “COST_TYPE_PREF” = 1, for each “COVERAGE_LEVEL” 0 AND 1
    """
    # bd = Basic_Drugs.get_close_to(drug, plan.FORMULARY_ID)
    bd = Basic_Drugs.get_by_ndc(drug, plan.FORMULARY_ID)
    try:
        if len(bd) > 1:
            log.info(log_msg(f"{drug}-{plan.FORMULARY_ID} returned more than 1 value"))

        bd = bd[0]
    except IndexError:
        ndc = NDC.get( drug )
        bd = Basic_Drugs.get_close_to(ndc.PRODUCT_NDC)
        if bd and len(bd) == 1:
            bd = bd[0]
        else:
            log.info(f"No Basic Drug for {ndc.PROPRIETARY_NAME} NDC:{ndc.PRODUCT_NDC} FormularyID:{plan.FORMULARY_ID}")
            return None, None

    if not bd.NDC:
        return None, None

    try:
        benefit_costs = Beneficiary_Costs.get_all(**dict(CONTRACT_ID=plan.CONTRACT_ID,
                                                         PLAN_ID=int(plan.PLAN_ID),
                                                         SEGMENT_ID=int(plan.SEGMENT_ID),
                                                         TIER=int(bd.TIER_LEVEL_VALUE),
                                                         DAYS_SUPPLY=1,
                                                         COST_TYPE_PREF=1
                                                         )
                                                  )
    except TypeError as e:
        log.info(log_msg( f"Type error{str(e)} looking for beneficiarycosts" ))

    bc = [c for c in benefit_costs if c.COVERAGE_LEVEL in (1, 0)]
    return bd, bc


def get_medicare_plan(drug_name, plan_name, zipcode=None):
    """
    Get alternative drugs for medicare for a plane and drug
    :param drug_name: string: drug name
    :param plan_name: string: plan name
    :return: dict: results
    """
    plan = get_plan(plan_name, zipcode)

    results = []
    drugs, exclude = get_related_drugs(drug_name)

    drug_list = set()
    for drg in drugs:
        fta = FTA.get(drg)
        if fta.NDC_IDS:
            drug_list.update(fta.NDC_IDS)
        else:
            ndcs = [ndc.id for ndc in NDC.find_by_name(fta.PROPRIETARY_NAME, fta.NONPROPRIETARY_NAME) ]
            fta.NDC_IDS = ndcs
            fta.save()
            drug_list.update(ndcs)

    for ndc_id in drug_list:
        #ndc = NDC.get(ndc_id)
        bd, bc = beneficiary_costs(ndc_id, plan)

        if not bd:
            """
            pa = 'Yes'
            ql = ''
            st = ''
            tier = ''
            """
            continue
        else:
            if bd.PRIOR_AUTHORIZATION_YN == 'False':
                pa = 'No'
            else:
                pa = 'Yes'

            if bd.STEP_THERAPY_YN == 'False':
                st = 'No'
            else:
                st = 'Yes'

            if bd.QUANTITY_LIMIT_YN == 'True':
                ql = f"Yes {bd.QUANTITY_LIMIT_AMOUNT}:{bd.QUANTITY_LIMIT_DAYS}"
            else:
                ql = f"No"
            try:
                tier = bc[0].TIER
            except IndexError:
                tier = bd.TIER_LEVEL_VALUE

        copay_d = ''
        cover = ''
        if bc:
            for c in bc:
                if c.COVERAGE_LEVEL == 1:
                    copay_d = "${:.2f}".format(c.COST_AMT_PREF)
                    cover   = "${:.2f}".format(c.COST_AMT_NONPREF)

        ndc = NDC.get(ndc_id)
        result = {'Brand': ndc.PROPRIETARY_NAME,
                  'Generic': ndc.NONPROPRIETARY_NAME,
                  'Tier': tier,
                  'ST': st,
                  'QL': ql,
                  'PA': pa,
                  'CopayD': copay_d,
                  'CTNP': cover
                  }
        results.append(result)

    if results:
        results = pd.DataFrame(results).drop_duplicates().to_dict('records')

    return results

if __name__ == "__main__":
    from settings      import DATABASE
    from models.base   import Database

    with Database(DATABASE) as db:
        result = get_medicare_plan( "Victoza", "Anthem MediBlue Essential (HMO)", '43202')
        print(result)
        result = get_medicare_plan('Levemir','SilverScript Plus (PDP)','07040')
        print(result)
        result = get_medicare_plan( "SYMBICORT","Silverscript choice (PDP)","07040")
        print(result)
        result = get_medicare_plan( "Novolog","WellCare Classic (PDP)",'43219')
        print(result)
        print( beneficiary_costs.cache_info() )


