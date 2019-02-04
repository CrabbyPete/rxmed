import re
import json
import requests

from bs4            import BeautifulSoup
from collections    import OrderedDict

from log import log

BASE_URL     = "https://rxnav.nlm.nih.gov/REST"
HISTORIC_URL = "https://rxnav.nlm.nih.gov/REST/rxcuihistoryconcept?rxcui={}"
OPENFDA_URL  = 'https://api.fda.gov/drug/ndc.json?search={}'
OHSTATE      = 'https://druglookup.ohgov.changehealthcare.com/DrugSearch/application/search?searchBy=name&name={}'


def OhioState( name ):
    url = OHSTATE.format(name)
    r = requests.get(url)

    if r.ok:
        html=r.text
    else:
        return r.status_code

    soup = BeautifulSoup(html,features="lxml")
    tbody = soup.tbody
    rows = []
    for tr in tbody.find_all('tr'):
        row = [t.text for t in tr.find_all('td')]
        try:

            data = OrderedDict( [('Product_Description'         ,row[2]),
                                 ('Route_of_Administration'     ,row[3] ),
                                 ('Package'                     ,re.sub('\r|\n|\t','',row[4])),
                                 ('Prior_Authorization_Required',re.sub('\r|\n|\t','',row[5])),
                                 ('Covered_for_Dual_Eligible'   ,re.sub('\r|\n|\t','',row[6])),
                                 ('Copay'                       ,re.sub('\r|\n|\t','',row[8]))]
                              )
        except:
            log.error(f"Ohio State scrape error {name}")
            continue
        
        rows.append(data)
    
    return rows


def get_historic_rxcui( rxcui ):
    url = HISTORIC_URL.format(rxcui)
    r = requests.get(url)
    if r.ok:
        data = json.loads(r.text)
    else:
        return r.status_code

    return data
    

class RxNorm():
    """

    """
    def __init__(self):
        self.base_url = BASE_URL
        return

    def api(self, url, kwargs ):
        r = requests.get( url, params = kwargs )

        if r.ok:
            data = json.loads(r.text)
        else:
            return r.status_code

        return data


    def getRelatedByType(self, rxcui, **kwargs):
        """
        Get drugs rela
        :param rxcui:
        :param kwargs:
        :return:
        """
        url = self.base_url + f'/rxcui/{rxcui}/related.json'

        # You need to keep the + signs and not uuencode them
        if 'tty' in kwargs:
            kwargs = "tty={}".format( kwargs['tty'] )

        data = self.api(url, kwargs)
        return data


class RxClass():
    def __init__(self):
        self.base_url = BASE_URL + '/rxclass'
        pass


    def api(self, url, kwargs ):
        r = requests.get( url, params = kwargs )
        data = None
        if r.ok:
            data = json.loads(r.text)

        return data


    def byDrugName(self, **kwargs ):
        """
        https://rxnav.nlm.nih.gov/RxClassAPIs.html#uLink=RxClass_REST_getClassByRxNormDrugName
        :param kwargs:
        :return:
        """
        url = self.base_url + '/class/byDrugName.json'

        # Because they use a + sign in argument you have to make a string
        if 'ttys' in kwargs:
            kwargs = "&".join("%s=%s" % (k,v) for k,v in kwargs.items())

        data = self.api( url, kwargs )
        if 'rxclassDrugInfoList' in data:
            return data['rxclassDrugInfoList']
        else:
            return None


    def classMembers(self, **kwargs):
        """
        Return class members of a drug
        :param kwargs:
        :return:
        """
        url = self.base_url + '/classMembers.json'

        # You have to do this because of the + in ttys outwise its uuencoded
        kwargs = "&".join("%s=%s" % (k,v) for k,v in kwargs.items())
        data = self.api( url, kwargs )
        return data


def open_fda( brand_name, generic_name = None ):
    search = f'brand_name:"{brand_name}"'
    if generic_name:
        search += f'+AND+generic_name:"{generic_name}"'
    url = OPENFDA_URL.format(search)
    r = requests.get(url)

    if r.ok:
        data = json.loads(r.text)
    else:
        return r.status_code

    return data['results']




if __name__ == "__main__":
    r = OhioState('ADMEL')
    """
    r = RxClass()
    data = r.byDrugName(drugName='morphine', relaSource='MEDRT',relas='may_treat')
    for d in data['rxclassDrugInfo']:
        classId = d['rxclassMinConceptItem']['classId']
        drug  = r.classMembers( classId=classId,
                                relas='may_treat',
                                relaSource='MEDRT'
                                )

        print( drug )
    """