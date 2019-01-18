

def get_formulary_id( plan_name, geo_info ):
    """
    Get the formulary_id for a plan
    :param plan_name: Full or partial name of a plan
    :param geo_info: record from the geolocate DB
    :return: a formulary_id for that plan for that zipcode
    """
    plans = Plans.get_all(**dict(PLAN_NAME=plan_name))

    formulary_ids = []
    for plan in plans:
        if plan.CONTRACT_ID.startswith('S'):
            if plan.PDP_REGION_CODE == geo_info.PDP_REGION_CODE:
                formulary_ids.append(plan)

        elif plan.CONTRACT_ID.startswith('H'):
            if int(plan.COUNTY_CODE) == int(geo_info.COUNTY_CODE):
                formulary_ids.append(plan)

        elif plan.CONTRACT_ID.startswith('R'):
            if int(plan.MA_REGION_CODE) == geo_info.COUNTY_CODE:
                formulary_ids.append(plan)

    # There should only be one
    if len( formulary_ids ) == 1:
        return formulary_ids[0]
    else:
        return formulary_ids


def get_medicare(zipcode, plan_name, medication):
    """

    :param zipcode:
    :param plan:
    :param medication:
    :return:
    """
    geo_info = get_location(zipcode)
    plans = Plans.get_one(**dict(PLAN_NAME=plan_name))

    drugs = NDC.get_all(**dict(PROPRIETARY_NAME=proprietary_name,
                               DOSE_STRENGTH=str(dose_strength),
                               DOSE_UNIT=dose_unit)
                        )
    return [drug.PRODUCT_NDC for drug in drugs]


class Medicare:
    """
    Medicare funtions
    """



    def get_ndc(self, proprietary_name, dose_strength, dose_unit):
        drugs = NDC.get_all(**dict(PROPRIETARY_NAME=proprietary_name,
                                   DOSE_STRENGTH=str(dose_strength),
                                   DOSE_UNIT=dose_unit)
                            )
        return [ drug.PRODUCT_NDC for drug in drugs ]


    def step7(self, proprietary_name, nonproprietary_namename = None):
        """

        :param name:
        :return:
        """
        fta_members = FTA.find_by_name( proprietary_name )
        return fta_members


    def step5(self, drugs, plan ):
        """

        :param drugs:
        :return:
        """
        # Step 5
        benefit_costs = []
        for drug in drugs:
            int_drug = int(drug.replace("-",""))
            meds = Basic_Drugs.get_close_to(int_drug, plan.FORMULARY_ID )
            for med in meds:
                costs = Beneficiary_Costs.get_all( **dict( CONTRACT_ID    = plan.CONTRACT_ID,
                                                           PLAN_ID        = plan.PLAN_ID,
                                                           SEGMENT_ID     = plan.SEGMENT_ID,
                                                           TIER           = med['TIER_LEVEL_VALUE'],
                                                           DAYS_SUPPLY    = 1,
                                                           #COST_TYPE_PREF = 1
                                                         )
                                                )
                benefit_costs.append( costs )

        return benefit_costs

def medicare( proprietary_name ):
    geo_info = m.get_location('53558')
    plan = m.get_plan_info( 'Care Improvement Plus Gold Rx (PPO SNP)', geo_info[0])
    drugs = m.get_ndc(proprietary_name, dose_strength, dose_unit )
    result = m.step5( drugs, plan )
    results = m.step7( proprietary_name )




if __name__ == "__main__":
    #medicare('Strattera')
    medicare('Victoza')


