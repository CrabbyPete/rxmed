import pandas as pd

from functools  import lru_cache

from log              import log, log_msg
from tools            import get_related_drugs, get_plan
from models.fta       import FTA, NDC
from models.medicare  import Beneficiary_Costs, NDC_BD


@lru_cache(8192)
def beneficiary_costs(drug, plan):
    """
    Get the beneficary costs for a drug in plan
    :param drug: drug ndc id number
    :param plan: dict: plan record
    :return:“COST_AMT_PREF” ONLY if “DAYS_SUPPLY” = 1 and “COST_TYPE_PREF” = 1, for each “COVERAGE_LEVEL” 0 AND 1
    """
    bd = NDC_BD.get_basic_drug( drug, plan.FORMULARY_ID)
    if not bd:
        log.info(f"No Basic Drug for NDC:{drug} FormularyID:{plan.FORMULARY_ID}")
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


def front_end_excluded( ndc, excluded:list)->bool:
    """
    Check if this record should be excluded
    :param ndc:
    :param excluded: list: names to exclude
    :return:
    """
    drug = ndc.PROPRIETARY_NAME + ' '+ ndc.NONPROPRIETARY_NAME
    for ex in excluded:
        if len(ex) and ex in drug.lower():
            return True
    return False


def get_medicare_plan(drug_name, plan_name, zipcode=None):
    """
    Get alternative drugs for medicare for a plane and drug
    :param drug_name: string: drug name
    :param plan_name: string: plan name
    :return: dict: results
    """
    plan = get_plan(plan_name, zipcode)

    # Get all related drugs
    results = []
    drugs, excluded = get_related_drugs(drug_name)

    # Get all the NDC numbers for each FTA
    ndc_list = set()
    for fta_id in drugs:
        fta = FTA.get(fta_id)
        if fta.NDC_IDS:
            ndc_list.update(fta.NDC_IDS)

    prior_authorize = True
    for ndc_id in ndc_list:
        ndc = NDC.get(ndc_id)
        if front_end_excluded( ndc, excluded):
            continue

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
            if bd.PRIOR_AUTHORIZATION_YN:
                pa = 'Yes'
            else:
                pa = 'No'
                if drug_name.lower() in ndc.PROPRIETARY_NAME.lower() or \
                   drug_name.lower() in ndc.NONPROPRIETARY_NAME.lower():
                    prior_authorize = False

            if bd.STEP_THERAPY_YN:
                st = 'Yes'
            else:
                st = 'No'

            if bd.QUANTITY_LIMIT_YN:
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

        result = {'Brand': f"{ndc.PROPRIETARY_NAME} {ndc.DOSE_STRENGTH} {ndc.DOSE_UNIT}",
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

    return {'data':results, 'pa': prior_authorize}


if __name__ == "__main__":
    from settings      import DATABASE
    from models.base   import Database

    with Database(DATABASE) as db:
        """
        result = get_medicare_plan( "Victoza", "Anthem MediBlue Essential (HMO)", '43202')
        print(result)
        result = get_medicare_plan('Levemir','SilverScript Plus (PDP)','07040')
        print(result)
        result = get_medicare_plan( "SYMBICORT","Silverscript choice (PDP)","07040")
        print(result)
        result = get_medicare_plan( "Novolog","WellCare Classic (PDP)",'43219')
        print(result)
        """
        result = get_medicare_plan('pulmicort flexhaler', 'humana preferred rx','07040')
        print( result )

        result = get_medicare_plan("Pulmicort", 'SilverScript Plus (PDP)', '07481')
        print(result)

        result = get_medicare_plan("Biktary", 'SilverScript Plus (PDP)', '07481')
        print(result)
        print( beneficiary_costs.cache_info() )


