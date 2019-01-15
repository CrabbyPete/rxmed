import json
import requests

from xmltodict import parse

BASE_URL     = "https://rxnav.nlm.nih.gov/REST"
OPENFDA_URL  = 'https://api.fda.gov/drug/event.json?search='


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
    """

    """

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



if __name__ == "__main__":
    r = RxClass()
    data = r.byDrugName(drugName='morphine', relaSource='MEDRT',relas='may_treat')
    for d in data['rxclassDrugInfo']:
        classId = d['rxclassMinConceptItem']['classId']
        drug  = r.classMembers( classId=classId,
                                relas='may_treat',
                                relaSource='MEDRT'
                                )

        print( drug )