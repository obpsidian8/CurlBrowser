import os
import re
import pickle
import time
from CoreLibrary.PyCurlRequest import CurlRequests


class FedexTrackingApi:
    """
    Main purpose of this class is return the UPS specific curl_headers
    """
    tracking_api_url = 'https://www.fedex.com/trackingCal/track'

    def __init__(self, cookies_dict=None, proxy=None):
        self.cookies_dict = cookies_dict
        self.proxy = proxy # IP:PORT or HOST:PORT
        self.carrier = 'fedex_curl'

        # Set the cookies and the token for the request here
        self.set_cookies_dict()

    def load_cookie(self):
        """
        Loads cookies from disk if available, for sending requests
        :return:
        """
        cookie = None
        if os.path.exists(f'{self.carrier}.cookie'):
            x = os.stat(f'{self.carrier}.cookie')
            age = (time.time() - x.st_mtime)
            if age < 86400:
                print(f"INFO: Cookie on disk is less than a day old")
                with open(f'{self.carrier}.cookie', 'rb') as cookie_store:
                    cookie = pickle.load(cookie_store)
                    if cookie:
                        print("INFO: Cookie loaded from disk")
                        self.cookies_dict = cookie
            else:
                print(f"INFO: Cookie is more than a day old. Will get new one")

        return cookie

    def saveCookie(self, cookies_dict):
        """
        Saves cookie  file to disk. To be used for sending tracking requests
        :param cookies_dict:
        :return:
        """
        with open(f'{self.carrier}.cookie', 'wb') as cookie_store:
            pickle.dump(cookies_dict, cookie_store)
            print("INFO: Cookie saved")

    def set_cookies_dict(self):
        """
        This token can only be obtained via a browser session.
        Check if cookies are stored on local machine before trying to get a new one
        :return:
        """
        cookie = self.load_cookie()
        if cookie:
            self.cookies_dict = cookie
            return

        print(f"INFO: Fedex cookie not loaded from on disk. Will obtain new one from Fedex site")
        curl = CurlRequests(cookies_dict={}, headers_dict={})
        rnd_link = 'https://www.fedex.com/fedextrack/?tracknumbers=950548487353'
        response = curl.send_curl_request(request_url=rnd_link, page_redirects=True, include=True)
        cookie_regex = re.compile(r'Set-Cookie:\s(.+?=.+?);', flags=re.IGNORECASE)
        cookies_list = cookie_regex.findall(str(response.get('response')))

        cookie_dict_regex = re.compile(r'(.+?)=(.+)')
        self.cookies_dict = {}
        for cookie in cookies_list:
            try:
                name = cookie_dict_regex.search(cookie).group(1).strip()
                print(f"INFO: Found cookie: {name}")
            except:
                print(f"ERROR Extracting cookie name")
                name = None

            try:
                value = cookie_dict_regex.search(cookie).group(2).strip()
                print(f"INFO: Found value of cookie {name}: {value}")
            except:
                print(f"ERROR Extracting cookie value")
                value = None

            if name and value:
                self.cookies_dict[name] = value

        print(f"\nINFO: Cookies found\n\t{self.cookies_dict}")
        self.saveCookie(self.cookies_dict)

    def format_proxy(self):
        """
        :return:
        """
        if self.proxy:
            curl_proxy = f"http://{self.proxy}"  # IP:PORT or HOST:PORT
            print(f"INFO: Proxy set for request: {curl_proxy}")
            return curl_proxy
        return None



    def base_headers_dict(self, tracking_number):
        """
        Defines and returns curl_headers for Costco API requests.
        This is the base setting for headers. All other header request settings derive from this one.
        :return: dictionary of curl_headers
        """

        headers_dict = {
            "Connection": "keep-alive",
            "sec-ch-ua": "\"Google Chrome\";v=\"87\", \" Not;A Brand\";v=\"99\", \"Chromium\";v=\"87\"",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua-mobile": "?0",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://www.fedex.com",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": f"//www.fedex.com/apps/fedextrack/?tracknumbers={tracking_number}"

        }
        return headers_dict

    def tracking_request_form_data(self, tracking_number):
        """
        Formats data used in Fedex tracking requests
        :return:
        """
        form_data = " 'data={\"TrackPackagesRequest\":{\"appType\":\"WTRK\",\"appDeviceType\":\"DESKTOP\",\"supportHTML\":true,\"supportCurrentLocation\":true,\"uniqueKey\":\"\",\"processingParameters\":{},\"trackingInfoList\":[{\"trackNumberInfo\":{\"trackingNumber\":\"%s\",\"trackingQualifier\":\"\",\"trackingCarrier\":\"\"}}]}}' -d 'action=trackpackages' -d 'locale=en_US' -d \"version=1\" -d \"format=json\"" % tracking_number
        return form_data

    def send_tracking_query(self, tracking_number):
        """
        Sends a tracking query to Fedex. Gets a tracking response as a JSON response
        :param tracking_number:
        :return: tracking response (JSON format)
        """

        headers_dict = self.base_headers_dict(tracking_number)
        form = self.tracking_request_form_data(tracking_number)
        curl = CurlRequests(cookies_dict=self.cookies_dict, headers_dict=headers_dict)

        proxy = self.format_proxy()

        response = curl.send_curl_request(request_url=self.tracking_api_url, form_data=form, proxy=proxy)

        return response
