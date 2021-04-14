import os
import re
import pickle
import time
from CoreLibrary.PyCurlRequest import CurlRequests


class USPSTrackingApi:
    """
    Main purpose of this class is return the USPS specific curl_headers and send requests
    """
    tracking_api_url = 'https://tools.usps.com/go/TrackConfirmAction?qtc_tLabels1='  # Tracking number is appended to this

    def __init__(self, cookies_dict=None, proxy=None):
        self.cookies_dict = cookies_dict
        self.proxy = proxy  # IP:PORT or HOST:PORT
        self.carrier = 'usps_curl'

        # Set the cookies and the token for the request here
        self.set_cookies_dict()

    def load_cookie(self):
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
        with open(f'{self.carrier}.cookie', 'wb') as cookie_store:
            pickle.dump(cookies_dict, cookie_store)
            print("INFO: Cookie saved")

    def set_cookies_dict(self):
        """
        This token can only be obtained via a browser session
        Check if cookies are stored on local machine before trying to get a new one
        :return:
        """
        cookie = self.load_cookie()
        if cookie:
            self.cookies_dict = cookie
            return

        print(f"INFO: USPS cookie not loaded from on disk. Will obtain new one from USPS site")
        curl = CurlRequests(cookies_dict={}, headers_dict={})
        rnd_link = 'https://tools.usps.com/go/TrackConfirmAction?qtc_tLabels1=92001901795912912884327069'
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

    def base_headers_dict(self):
        """
        Defines and returns curl_headers for Costco API requests.
        This is the base setting for headers. All other header request settings derive from this one.
        :return: dictionary of curl_headers
        """

        headers_dict = {
            "authority": "tools.usps.com",
            "cache-control": "max-age=0",
            "sec-ch-ua": "\"Google Chrome\";v=\"87\", \" Not;A Brand\";v=\"99\", \"Chromium\";v=\"87\"",
            "sec-ch-ua-mobile": "?0",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "sec-fetch-site": "cross-site",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "accept-language": "en-US,en;q=0.9"

        }
        return headers_dict

    def send_tracking_query(self, tracking_number):
        """
        Sends a tracking query to USPS.
        The response is in html format. The tracking status and detailed information can be scraped from the html response
        :param tracking_number:
        :return: html response containing tracking details
        """

        headers_dict = self.base_headers_dict()
        curl = CurlRequests(cookies_dict=self.cookies_dict, headers_dict=headers_dict)

        proxy = self.format_proxy()
        url = f"{self.tracking_api_url}{tracking_number}"
        response = curl.send_curl_request(request_url=url, proxy=proxy)

        return response
