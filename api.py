import re
import json
import requests

from bs4            import BeautifulSoup

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
    
"""
rxcui/{rxcui}/filter 	Filter by property
def findRxcuiById 	/rxcui?idtype 	Search by identifier to find RxNorm concepts
def getAllConceptsByTTY 	/allconcepts 	Return the RxNorm concepts for the specified term types
def getAllHistoricalNDCs 	/rxcui/{rxcui}/allhistoricalndcs 	Return all National Drug Codes (NDC) for a concept
def getAllNDCs 	/rxcui/{rxcui}/allndcs 	TO BE DEPRECATED. Use getAllHistoricalNDCs or /rxcui/{rxcui}/allhistoricalndcs instead.
def getAllProperties 	/rxcui/{rxcui}/allProperties 	Return all properties for a concept
def getAllRelatedInfo 	/rxcui/{rxcui}/allrelated 	Return all related concept information
def getApproximateMatch 	/approximateTerm 	Approximate match search to find closest strings
def getDisplayTerms 	/displaynames 	Return the auto suggestion names
def getDrugs 	/drugs 	Return the related drugs
def getIdTypes 	/idtypes 	Return the available identifier types
def getMultiIngredBrand 	/brands 	Return the brands containing the specified ingredients
def getNDCs 	/rxcui/{rxcui}/ndcs 	Return all National Drug Codes (NDC) for a concept
def getNDCProperties 	/ndcproperties 	Return National Drug Code (NDC) properties
def getNDCStatus 	/ndcstatus 	Return the status of a National Drug Code (NDC)
def getPropCategories 	/propCategories 	Return the property categories.
def getPropNames 	/propnames 	Return the property names.
def getProprietaryInformation 	/rxcui/{rxcui}/proprietary 	Return the proprietary information for a concept
def getRelatedByRelationship 	/rxcui/{rxcui}/related?rela 	Return the related concepts of specified relationship types
def getRelatedByType 	/rxcui/{rxcui}/related?tty 	Return the related concepts of specified term types
def getRelaTypes 	/relatypes 	Return the available relationship types
def getRxConceptProperties 	/rxcui/{rxcui}/properties 	Return the concepts properties
def getRxcuiStatus 	/rxcui/{rxcui}/status 	Return the status of the concept
def getRxNormVersion 	/version 	Return the RxNorm data set version
def getRxProperty 	/rxcui/{rxcui}/property 	Return the value of a concept property
def getSourceTypes 	/sourcetypes 	Return the available vocabulary abbreviated source types
def getSpellingSuggestions 	/spellingsuggestions 	Return spelling suggestions for a name
def getTermTypes 	/termtypes 	Return the available term types
"""
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

    def findRxcuiByString(self,name):
        """ Search by name to find RxNorm concepts
        :param name: name to look for
        :return:
        """
        url = self.base_url + f'/rxcui.json?'
        kwargs = {'name':name,'search':2}
        data = self.api(url, kwargs)
        return walk(data,'rxnormId')


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

"""
def findClassesById 	/class/byId 	newFind the drug classes from a class identifier
def findClassByName 	/class/byName 	Find drug classes from a class name
def findSimilarClassesByClass 	/similar 	Find similar class membership
def findSimilarClassesByDrugList 	/similarByRxcuis 	Find similar classes from a list of RxNorm drug identifiers
def getAllClasses 	/allClasses 	Get all drug classes
def getClassByRxNormDrugId 	/class/byRxcui 	Get the classes of a specified drug identifier
def getClassByRxNormDrugName 	/class/byDrugName 	Get the classes of a specified drug name
def getClassContexts 	/classContext 	Get the class context
def getClassGraph 	/classGraph 	SOAP FUNCTION TO BE DEPRECATED. Use getClassGraphBySource instead
def getClassGraphBySource 	/classGraph 	newGet the class graph of ancestors
def getClassMembers 	/classMembers 	Get the drug members of a specified class
def getClassTree 	/classTree 	Get the descendents of a class
def getClassTypes 	/classTypes 	Get the class types
def getRelas 	/relas 	Get the relationships for a source of drug relations
def getSimilarityInformation 	/similarInfo 	Get the similarity information between members of two classes
def getSourcesOfDrugClassRelations 	/relaSources 	Get the sources of drug-class relations
def getSpellingSuggestions 	/spellingsuggestions 	Get spelling suggestions for a drug or class name
"""
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


    def findSimilarClassesByDrugList(self,rxcui):
        """ Find similar classes from a list of RxNorm drug identifiers
        :param rxcui: rxcui from RxNorm
        :return:
        """
        url = self.base_url + '/similarByRxcuis.json'
        data = self.api(url, **{'rxcui':rxcui})
        return data


    def byDrugName(self, drugName, relaSource=None, relas=None ):
        """
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


    def classMembers(self, **kwargs):
        """ Return class members of a drug
        :param:classId - the class identifier. Note that this is NOT an RxNorm identifier, but an identifier from the source vocabulary. See examples below.
        :param:relaSource - the source asserting the relationships between the drug members and the drug class. See table below for the valid sources.
        :param:rela - the relationship of the drug class to its members. See table below for valid relationship values.
        :param:trans - (optional) 0 = include indirect and direct relations (the default). 1 = direct relations only.
        :param:ttys - (optional) include only drugs with the specified RxNorm term types. Default is IN, PIN and MIN.
        :return:
        """
        url = self.base_url + '/classMembers.json'
        if 'ttys' in kwargs:
            kwargs['ttys'] = "+".join(kwargs['ttys'])

        # You have to do this because of the + in ttys outwise its uuencoded
        kwargs = "&".join("%s=%s" % (k,v) for k,v in kwargs.items())
        data = self.api( url, kwargs )
        return walk(data,'drugMember')


"""
Open FDA API
"""
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


def open_fda_rxcui( rxcui ):
    search=f'openfda.rxcui:"{str(rxcui)}"'

    url = OPENFDA_URL.format(search)
    r = requests.get(url)
    if r.ok:
        data = json.loads(r.text)
    else:
        return r.status_code,[]

    return r.status_code, data['results']


if __name__ == "__main__":
    from models.base import Database
    from models.fta import FTA
    from models.medicaid import OhioState
    from settings import DATABASE

    with Database( DATABASE) as db:
        rxnorm = RxNorm()
        rxclass = RxClass()

        with open('related.csv','+w') as fyle:
            for fta in FTA.session.query(FTA).filter(FTA.ACTIVE == True).order_by(FTA.id):
                name = fta.PROPRIETARY_NAME
                result = rxnorm.findRxcuiByString(name)
                if result and len( result ) == 1:
                    drug_class = rxclass.getClassByRxNormDrugId(result[0])
                    fta.RXCUI = result[0]
                    result = result[0]
                    fta.save()

                print( f"{fta.id},{name},{result}")

            """
            data = OhioStateAPI(name)
            for d in data:
                ohio = OhioState.get_or_create( **d )
                ohio.drug_name = name
                ohio.save()
            """

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
