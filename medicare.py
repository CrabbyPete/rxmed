
from models.geo import Zipcode, Geolocate
from models.ndc import NDC, Plans, Basic_Drugs,Beneficiary_Costs
from models.fta import FTA

def get_location( zipcode ):
    """
    Get the geo location infor from a given zipcode
    :param zipcode: string: zipcode to look in
    :return: geo_info The geo location information in the Geolocate db
    """
    while zipcode.startswith('0'):
        zipcode = zipcode[1:]

    zip_info = Zipcode.get_one(**dict(ZIPCODE=zipcode))
    geo_info = Geolocate.get_all(**dict(COUNTY=zip_info.COUNTY.strip(), STATENAME=zip_info.STATENAME.strip()))
    return geo_info


def get_plans( plan_name, geo_info):
    """

    :param plan_name: Full or partial name of a plan
    :param geo_info: record from the geolocate DB
    :return: list: plan names
    """


class Medicare:
    """
    Medicare funtions
    """
    def get_location(self, zipcode ):
        # Step 1
        zip_info = Zipcode.get_one(**dict(ZIPCODE=zipcode))

        # Step 2
        geo_info = Geolocate.get_all(**dict(COUNTY=zip_info.COUNTY.strip(), STATENAME=zip_info.STATENAME.strip()))

        return geo_info


    def get_plan_info(self, plan_name, geo):
        """

        :param plan_name:
        :return:
        """
        # Step 3
        found = []
        plans = Plans.get_all(**dict(PLAN_NAME=plan_name))

        formulary_ids = []
        for plan in plans:
            if plan.CONTRACT_ID.startswith('S'):
                if plan.PDP_REGION_CODE == geo.PDP_REGION_CODE:
                    formulary_ids.append(plan)

            elif plan.CONTRACT_ID.startswith('H'):
                if int(plan.COUNTY_CODE) == int(geo.COUNTY_CODE):
                    formulary_ids.append(plan)

            elif plan.CONTRACT_ID.startswith('R'):
                if int(plan.MA_REGION_CODE) == geo.COUNTY_CODE:
                    formulary_ids.append(plan)

        return formulary_ids[0]

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

def medicare( proprietary_name, dose_strength, dose_unit ):
    m = Medicare()
    geo_info = m.get_location('53558')
    plan = m.get_plan_info( 'Care Improvement Plus Gold Rx (PPO SNP)', geo_info[0])
    drugs = m.get_ndc(proprietary_name, dose_strength, dose_unit )
    result = m.step5( drugs, plan )
    results = m.step7( proprietary_name )



def step5_6( drugs ):
    """
    :param drugs:
    :return:
    """
    # Step 5
    for drug in drugs:
        int_drug = int(drug.replace("-",""))
        meds = Basic_Drugs.get_close_to(int_drug)
        for med in meds:
            costs = Beneficiary_Costs.get_all( **dict( CONTRACT_ID = plan.CONTRACT_ID,
                                                       PLAN_ID     = plan.PLAN_ID,
                                                       SEGMENT_ID  = plan.SEGMENT_ID,
                                                       TIER        = med['TIER_LEVEL_VALUE']
                                                     )
                                             )
            benefit_costs = []
            for cost in costs:
                print(cost)


if __name__ == "__main__":
    #medicare('Strattera', 25,'mg/1')
    medicare('Victoza', 6, 'mg/mL')


