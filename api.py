import re
import json
import requests

from bs4 import BeautifulSoup
from log import log


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
        r = requests.get(url, params=kwargs)

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


    def getApproximateMatch(self, term):
        """ Approximate match search to find closest strings
        :param term:
        :return:
        """
        url = self.base_url + '/approximateTerm.json'
        kwargs = {'term':term}
        data = self.api(url, kwargs)
        return  walk(data,'approximateGroup')


    def getAllProperties(self, rxcui):
        """ Return all properties for a concept
        :param rxcui: rxcui
        :return:
        """
        url = self.base_url +f"/rxcui/{rxcui}/allProperties.json"
        kwargs = {}
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

        # You need to keep the + signs and not uuencode them
        if 'tty' in kwargs:
            kwargs = "tty={}".format( kwargs['tty'] )

        data = self.api(url, kwargs)
        return data


class RxClass(RxBase):

    def __init__(self):
        self.base_url = BASE_URL + '/rxclass'


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


    def classMembers(self, classId, relaSource=None, rela=None, trans=0, ttys=None):
        """ Return class members of a drug
        :param:classId - the class identifier. Note that this is NOT an RxNorm identifier, but an identifier from the source vocabulary. See examples below.
        :param:relaSource - the source asserting the relationships between the drug members and the drug class. See table below for the valid sources.
        :param:rela - the relationship of the drug class to its members. See table below for valid relationship values.
        :param:trans - (optional) 0 = include indirect and direct relations (the default). 1 = direct relations only.
        :param:ttys - (optional) include only drugs with the specified RxNorm term types. Default is IN, PIN and MIN.
        :return:
        """
        url = self.base_url + '/classMembers.json'
        kwargs = {'classId':classId, 'trans':trans}
        if relaSource:
            kwargs['relaSource'] = relaSource
        if rela:
            kwargs['rela']=rela
        if ttys:
            kwargs['ttys']=ttys

        data = self.api( url, kwargs )
        return walk(data,'drugMember')


"""
Open FDA API
"""
class FDA(RxBase):
    base_url = OPENFDA_URL

    def open_fda(self, brand_name, generic_name = None, look_for = None ):
        """ Use Open FDA to find a drug
        :param brand_name:
        :param generic_name:
        :return:
        """
        search = f'brand_name:"{brand_name}"'
        if generic_name:
            search += f'+AND+generic_name:"{generic_name}"'

        url = OPENFDA_URL.format(search)
        data = self.api( url, {})

        if look_for:
            return walk(data, look_for)

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

