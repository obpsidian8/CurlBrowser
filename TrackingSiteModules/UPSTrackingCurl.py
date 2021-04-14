import re
import os
import time
from CoreLibrary.PyCurlRequest import CurlRequests
import pickle


class UPSTrackingApi:
    """
    Main purpose of this class is return the UPS specific curl_headers
    """
    tracking_api_url = 'https://www.ups.com/track/api/Track/GetStatus?loc=en_US'

    def __init__(self, cookies_dict=None, proxy=None):
        self.cookies_dict = cookies_dict
        self.proxy = proxy  # IP:PORT or HOST:PORT
        self.carrier = 'ups_curl'

        self.x_xsrf_token = None

        # Set the cookies and the token for the request here
        self.set_cookies_dict()
        self.set_x_xsrf_token()

    def load_cookie(self):
        """
        Loads cookies from a cookie pickle file saved to the disk
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
        Function to save a dictionary of cookies as a pickle to the disk, which can be used for future requests
        :param cookies_dict:
        :return:
        """
        with open(f'{self.carrier}.cookie', 'wb') as cookie_store:
            pickle.dump(cookies_dict, cookie_store)
            print("INFO: Cookie saved")

    def set_cookies_dict(self):
        """
        This token can only be obtained via a browser session, or a prior curl session. See below.
        Check if cookies are stored on local machine before trying to get a new one
        :return:
        """
        cookie = self.load_cookie()
        if cookie:
            self.cookies_dict = cookie
            return

        print(f"INFO: UPS cookie not loaded from on disk. Will obtain new one from UPS site")
        curl = CurlRequests(cookies_dict={}, headers_dict={})
        rnd_link = 'https://www.ups.com/track?loc=null&tracknum=1Z97015F0341620620&requester=WT/trackdetails'
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

        return

    def format_proxy(self):
        """
        :return:
        """
        if self.proxy:
            curl_proxy = f"http://{self.proxy}"  # IP:PORT or HOST:PORT
            print(f"INFO: Proxy set for request: {curl_proxy}")
            return curl_proxy
        return None

    def set_x_xsrf_token(self):
        """
        XSRF token is needed for sending the requests.
        This token can be extracted from the cookies dict
        :return:
        """
        if self.cookies_dict:
            x_xsrf_token_regex = re.compile("X-XSRF-TOKEN-ST':\s+'(.+?)'")
            try:
                self.x_xsrf_token = x_xsrf_token_regex.search(str(self.cookies_dict)).group(1).strip()
                print(f'INFO: Found X-XSRF-TOKEN : {self.x_xsrf_token}')
            except Exception as e:
                print(f"ERROR: Error extracting X-XSRF-TOKEN from cookies dict. DETAILS {e}")
        else:
            print(f"ERROR: No cookies dict to get X-XSRF-TOKEN- from.")

    def base_headers_dict(self, tracking_number):
        """
        Defines and returns curl_headers for Costco API requests.
        This is the base setting for headers. All other header request settings derive from this one.
        :return: dictionary of curl_headers
        """

        headers_dict = {
            "Connection": "keep-alive",
            "sec-ch-ua": "\"Google Chrome\";v=\"87\", \" Not;A Brand\";v=\"99\", \"Chromium\";v=\"87\"",
            "Accept": "application/json, text/plain, */*",
            "sec-ch-ua-mobile": "?0",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
            "Content-Type": "application/json",
            "Origin": "https://www.ups.com",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": f"https://www.ups.com/track?loc=null&tracknum={tracking_number}&requester=WT/trackdetails",
            "X-XSRF-TOKEN": self.x_xsrf_token

        }
        return headers_dict

    def tracking_request_body_data(self, tracking_number):
        """
        Formats data used in UPS tracking requests
        :return:
        """
        data = '{"Locale":"en_US","TrackingNumber":["%s"],"Requester":"wt","consumerHub":""}' % tracking_number
        return data

    def send_tracking_query(self, tracking_number):
        """
        Sends a tracking query to UPS
        :param tracking_number:
        :return: tracking response (JSON format)
        """

        headers_dict = self.base_headers_dict(tracking_number)
        data = self.tracking_request_body_data(tracking_number)
        curl = CurlRequests(cookies_dict=self.cookies_dict, headers_dict=headers_dict)
        proxy = self.format_proxy()

        response = curl.send_curl_request(request_url=self.tracking_api_url, data=data, proxy=proxy)

        return response
