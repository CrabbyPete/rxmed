import re
import json
import requests

from bs4 import BeautifulSoup
from log import log,log_msg


BASE_URL      = "https://rxnav.nlm.nih.gov/REST"
HISTORIC_URL  = "https://rxnav.nlm.nih.gov/REST/rxcuihistoryconcept?rxcui={}"
OPENFDA_URL   = 'https://api.fda.gov/drug/ndc.json?search={}'
OHSTATE       = 'https://druglookup.ohgov.changehealthcare.com/DrugSearch/application/search?searchBy=name&name={}'

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

def OhioStateAPI( name )->list:
    name = name.split()[0]
    url = OHSTATE.format(name)
    r = requests.get(url, verify=False)

    not_found = set()
    if r.ok:
        html=r.text
    else:
        return r.status_code

    soup = BeautifulSoup(html,features="lxml")
    tbody = soup.tbody
    if not tbody:
        return []

    rows = []
    for tr in tbody.find_all('tr'):
        row = [t.text for t in tr.find_all('td')]
        try:

            data = dict( Product_Description          = row[2],
                         Route_of_Administration      = row[3],
                         Package                      = re.sub('\r|\n|\t','',row[4]),
                         Prior_Authorization_Required = re.sub('\r|\n|\t','',row[5]),
                         Covered_for_Dual_Eligible    = re.sub('\r|\n|\t','',row[6]),
                         Copay                        = re.sub('\r|\n|\t','',row[8]),
                         active                       = True
                        )
        except:
            log.error(f"Ohio State scrape error {name}")
            data = dict(Product_Description=name, active = False)
        
        rows.append(data)
    
    return rows


def get_historic_rxcui( rxcui ):
    """
    Get the history of a rxcui
    :param rxcui:
    :return:
    """
    url = HISTORIC_URL.format(rxcui)
    r = requests.get(url)
    if r.ok:
        data = json.loads(r.text)
    else:
        return r.status_code

    return data


class RxBase:
    def api(self, url, kwargs):
        try:
            r = requests.get(url, params=kwargs)
        except Exception as e:
            log.exception(log_msg(f"Exception in api:{str(e)}"))
            return None

        if r.ok:
            data = json.loads(r.text)
        else:
            return r.status_code

        return data


class RxTerm(RxBase):
    base_url = BASE_URL+'/RxTerms/'

    def getAllRxTermInfo(self, rxcui):
        """Retrieve RxTerms information for a specified RxNorm concept

        :param rxcui:
        :return:
        """
        url = self.base_url + f'rxcui/{rxcui}/allinfo.json'
        data = self.api(url, {})
        return walk(data,'rxtermsProperties')


    def getRxTermDisplayName(self,rxcui):
        """ Retrieve the RxTerms display name for a specified RxNorm concept
        :param rxcui:
        :return:
        """
        url = self.base_url+f'rxcui/{rxcui}/name.json'
        data = self.api(url,{})
        return walk(data,'displayName')


class RxNorm(RxBase):
    """
    """
    def __init__(self):
        self.base_url = BASE_URL
        return

    def getApproximateMatch(self, **kwargs):
        """ Approximate match search to find closest strings
        :param term:
        :return:
        """
        url = self.base_url + '/approximateTerm.json'
        data = self.api(url, kwargs)
        return  walk(data,'approximateGroup')


    def getAllProperties(self, rxcui, **kwargs):
        """ Return all properties for a concept
        :param rxcui: rxcui
        :return:
        """
        url = self.base_url +f"/rxcui/{rxcui}/allProperties.json"
        data = self.api(url, kwargs)
        return walk(data, "propConcept")


    def findRxcuiByString(self,name, search=0):
        """ Search by name to find RxNorm concepts
        :param name: name to look for
        :return:
        """
        url = self.base_url + f'/rxcui.json?'
        kwargs = {'name':name,'search':search}
        data = self.api(url, kwargs)
        return walk(data,'rxnormId')


    def getRxConceptProperties(self, rxcui):
        """Return the concepts properties
        :param rxcui:
        :return:
        """
        url = self.base_url + f'/rxcui/{rxcui}/properties.json'
        data = self.api(url, {})
        return walk(data,'properties')


    def getAllRelatedInfo(self, rxcui):
        """ Return all related concept information
        :param rxcui: rxcui id
        :return:
        """
        url = self.base_url + f'/rxcui/{rxcui}/allrelated.json'
        kwargs = {}
        data = self.api(url, kwargs)
        return walk(data,'conceptGroup')


    def getDrugs(self, name, perscribe=False):
        """ Return the related drugs
        :param name: drug name
        :return:
        """
        if perscribe:
            url = self.base_url + '/Prescribe/drugs.json'
        else:
            url = self.base_url + '/drugs.json'

        kwargs = {'name':name}
        data = self.api(url,kwargs)
        return walk( data,'conceptGroup')


    def getRelatedByType(self, rxcui, **kwargs):
        """ Return the related concepts of specified term types
        :param rxcui:
        :param kwargs:
        :return:
        """
        url = self.base_url + f'/rxcui/{rxcui}/related.json'
        if 'tty' in kwargs:
            kwargs = f"tty={'+'.join(kwargs['tty'])}"
        data = self.api(url, kwargs)
        return walk(data,'relatedGroup')

class RxClass(RxBase):

    def __init__(self):
        self.base_url = BASE_URL + '/rxclass'

    def findClassById(self,class_id):
        url = self.base_url + '/class/byId.json'
        kwargs = {'classId': class_id}
        data = self.api(url, kwargs)
        return walk(data,'rxclassMinConcept')


    def findSimilarClassesByDrugList(self,rxcui):
        """ Find similar classes from a list of RxNorm drug identifiers
        :param rxcui: rxcui from RxNorm
        :return:
        """
        url = self.base_url + '/similarByRxcuis.json'
        data = self.api(url, **{'rxcui':rxcui})
        return data


    def byDrugName(self, drugName, relaSource=None, relas=None ):
        """ Get drug by name
        :param drugName:
        :param relaSource:
        :param relas:
        :return:
        """
        url = self.base_url + '/class/byDrugName.json'
        kwargs = {'drugName':drugName}
        if relaSource:
            kwargs['relaSource'] = relaSource
        if relas:
            kwargs['relas'] = relas

        data = self.api( url, kwargs )
        return walk(data,'rxclassDrugInfoList')


    def getClassByRxNormDrugId(self, rxcui, relaSource=None, relas=None):
        """Get the classes of a specified drug identifier
        :param rxcui - the RxNorm identifier (RxCUI) of the drug. This can be an identifier for any RxNorm drug term.
        :param relaSource - (optional) a source of drug-class relationships. See /relaSources for the list of sources of drug-class relations. If this field is omitted, all sources of drug-class relationships will be used.
        :param relas - (optional) a list of relationships of the drug to the class. This field is ignored if relaSource is not specified.
        :return:
        """
        url = self.base_url +'/class/byRxcui.json'
        kwargs = {'rxcui':rxcui}
        if relaSource:
            kwargs['relaSource'] = relaSource
        if relas:
            kwargs['relas'] = relas
        data = self.api(url, kwargs)
        return walk(data,'rxclassDrugInfo')


    def classMembers(self, classId, **kwargs):
        """ Return class members of a drug
        :param:classId - the class identifier. Note that this is NOT an RxNorm identifier, but an identifier from the source vocabulary. See examples below.
        :param:relaSource - the source asserting the relationships between the drug members and the drug class. See table below for the valid sources.
        :param:rela - the relationship of the drug class to its members. See table below for valid relationship values.
        :param:trans - (optional) 0 = include indirect and direct relations (the default). 1 = direct relations only.
        :param:ttys - (optional) include only drugs with the specified RxNorm term types. Default is IN, PIN and MIN.
        :return:
        """
        url = self.base_url + '/classMembers.json'
        kwargs['classId'] = classId
        if 'ttys' in kwargs:
            kwargs['ttys']= f"{'+'.join(kwargs['ttys'])}"

        kwargs = "&".join("%s=%s" % (k, v) for k, v in kwargs.items())

        data = self.api( url, kwargs )
        return walk(data,'drugMember')


"""
Open FDA API
"""

FIELDS = ('product_id',
          'product_ndc',
          'spl_id',
          'product_type',
          'finished',
          'brand_name',
          'brand_name_base',
          'brand_name_suffix',
          'generic_name',
          'dosage_form',
          'route',
          'marketing_start_date',
          'marketing_end_date',
          'marketing_category',
          'application_number',
          'active_ingredients',
          'pharm_class',
          'dea_schedule',
          'listing_expiration_date',
          'packaging',
          'openfda')


class FDA():
    base_url = OPENFDA_URL

    def api(self, url, kwargs):
        try:
            r = requests.get(url, params=kwargs)
        except Exception as e:
            log.exception(f"Exception in api:{str(e)}")
            return None

        if r.ok:
            data = json.loads(r.text)
        else:
            log.error(f"Bad request for {url}:{r.status_code}")
            return r.status_code

        return data

    def open_fda(self, **kwargs:dict):
        """ Use Open FDA to find a drug
        :param brand_name:
        :param generic_name:
        :return:
        """
        search = None
        context = {}
        if 'limit' in kwargs.keys():
            context['limit'] = kwargs.pop('limit')

        if 'skip' in kwargs.keys():
            context['skip'] = kwargs.pop('skip')


        for k,v in kwargs.items():
            if not k in FIELDS:
                continue

            # Dates are in lists
            if isinstance(v, list):
                v = f"[{v[0]}+TO+{v[1]}]"

            elif isinstance(v,set):
                v =f"({'+'.join(v)})"

            if not search:
                search = f'{k}:"{v}"'
            else:
                search +=f'+AND+{k}:"{v}"'

        url = OPENFDA_URL.format(search).replace('"','')

        data = self.api(url, context)

        if 'look_for' in kwargs.keys():
            return walk(data, kwargs['look_for'])

        try:
            return data['results']
        except:
            return None


    def open_fda_rxcui(self,rxcui):
        """ Use rxcui with open fda
        :param rxcui:
        :return:
        """
        search=f'openfda.rxcui:"{str(rxcui)}"'

        url = OPENFDA_URL.format(search)
        data = self.api(url,{})
        try:
            return data['results']
        except:
            return None

