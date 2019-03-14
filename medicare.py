import pandas as pd

from functools  import lru_cache

from log              import log, log_msg
from api              import RxTerm
from tools            import get_related, get_plan
from models.fta       import FTA, NDC, OpenNDC
from models.medicare  import Beneficiary_Costs, Basic_Drugs

def beneficiary_costs(rxcui_list, plan):
    """
    Get the beneficary costs for a drug in plan
    :param ndc: drug ndc id number
    :param plan: dict: plan record
    :return:“COST_AMT_PREF” ONLY if “DAYS_SUPPLY” = 1 and “COST_TYPE_PREF” = 1, for each “COVERAGE_LEVEL” 0 AND 1
    """
    bd_list = Basic_Drugs.session.query(Basic_Drugs).filter(Basic_Drugs.FORMULARY_ID == plan.FORMULARY_ID,
                                                            Basic_Drugs.RXCUI.in_(rxcui_list)).all()

    bdbc_list = []
    for bd in bd_list:
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
        bdbc_list.append((bd, bc))

    return bdbc_list


def front_end_excluded( drug, excluded:list)->bool:
    """
    Check if this record should be excluded
    :param ndc:
    :param excluded: list: names to exclude
    :return:
    """
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
    drug_parts = [dp.strip() for dp in drug_name.split('-')]

    # Get the right fta record
    excluded = set()
    rxcui_list = set()
    fta_list = FTA.find_by_name(drug_parts[0], drug_parts[1] if len(drug_parts)==2 else None)


    for fta in fta_list:

        if fta.SBD_RXCUI:
            rxcui_list.update(fta.SBD_RXCUI)

        # Get the excluded list
        if fta.EXCLUDED_DRUGS_FRONT:
            excluded.update([s.strip() for s in fta.EXCLUDED_DRUGS_FRONT.lower().split("|") if s.strip()])

        # Get all the related RXCUI's
        if fta.RELATED_DRUGS:
            related = fta.RELATED_DRUGS
        else:
            related = get_related(fta)

        # Get all the FTA's for those related rxcui's
        for rxcui in related:
            for related_fta in FTA.find_rxcui(rxcui):
                if related_fta.SBD_RXCUI:
                    rxcui_list.update(related_fta.SBD_RXCUI)

    # Match up the beneficiary file with the plan and the rxcui from the ndc
    prior_authorize = True
    bdbc_list = beneficiary_costs(rxcui_list, plan)
    rxterm = RxTerm()
    for bd,bc in bdbc_list:
        if not bd:
            """
            pa = 'Yes'
            ql = ''
            st = ''
            tier = ''
            """
            continue
        else:
            term = rxterm.getAllRxTermInfo(bd.RXCUI)
            full_name = term.get('fullName','')
            generic_name = term.get('fullGenericName','')

            if front_end_excluded(full_name, excluded):
                continue

            if bd.PRIOR_AUTHORIZATION_YN:
                pa = 'Yes'
            else:
                pa = 'No'
                if drug_parts[0] in full_name.lower() or \
                   drug_parts[0] in generic_name.lower():
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

        result = {'Brand': full_name,
                  'Generic': generic_name,
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

        result = get_medicare_plan("tresiba - insulin degludec injection","Aetna Medicare NJ Silver Plan (Regional PPO)","07040")
        result = get_medicare_plan( "Victoza", "Anthem MediBlue Essential (HMO)", '43202')
        print(result)
        result = get_medicare_plan('Levemir','SilverScript Plus (PDP)','07040')
        print(result)
        result = get_medicare_plan( "SYMBICORT","Silverscript choice (PDP)","07040")
        print(result)
        result = get_medicare_plan( "Novolog","WellCare Classic (PDP)",'43219')
        print(result)
        result = get_medicare_plan('pulmicort flexhaler', 'humana preferred rx','07040')
        print( result )
        result = get_medicare_plan("Pulmicort", 'SilverScript Plus (PDP)', '07481')
        print(result)
        result = get_medicare_plan("Biktary", 'SilverScript Plus (PDP)', '07481')
        print(result)



