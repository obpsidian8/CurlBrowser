import re
import json
import sys
from CoreLibrary.PyCurlRequest import CurlRequests
from PIL import Image
import requests
from io import BytesIO


class DropakInfo:
    """
    Download items from dropapk hosting site without browser and javascript ads
    """

    def __init__(self, cookies_dict, proxy=None):
        self.cookies_dict = cookies_dict
        self.proxy = proxy

    def format_proxy(self):
        """
        :return:
        """
        if self.proxy:
            curl_proxy = f"http://{self.proxy}"  # IP:PORT or HOST:PORT
            print(f"INFO: Proxy set for request: {curl_proxy}")
            return curl_proxy
        return None

    def get_stage_one_response_file_info(self, download_link):
        """
        Gets details item page as html response
        :return:
        """
        headers_dict = self.get_stage_one_headers()
        self.set_cookies_dict(download_link)

        requester = CurlRequests(self.cookies_dict, headers_dict=headers_dict)
        curl_proxy = self.format_proxy()

        if curl_proxy:
            response = requester.send_curl_request(download_link, proxy=curl_proxy)
        else:
            response = requester.send_curl_request(download_link)
        return response

    def extract_file_info_from_stage_one_response(self, download_link):
        """
        Get stage one response (HTML containing download information)
        From file information, get id and file name
        """
        file_info = self.get_stage_one_response_file_info(download_link)
        file_info = file_info.get('response')

        # file_name_regex = re.compile(r'name=\"fname\"\s+value=\"(.+?)\"')
        # id_regex = re.compile(r'name=\"id\"\s+value=\"(.+?)\"')
        # op_regex = re.compile(r'name=\"op\"\s+value=\"(.+?)\"')

        download_info = {}

        names = ["fname", "id", "op"]
        for name in names:
            regex = re.compile(fr'name=\"{name}\"\s+value=\"(.+?)\"')

            try:
                value = regex.search(file_info).group(1)
                print(f"INFO: {name} value found: {value}")
            except:
                print(f"ERROR: Could not get {name} value")
                value = ""

            download_info[name] = value

        print(json.dumps(download_info, indent=2))
        return download_info

    def extract_captcha_info_from_stage_two_response(self, download_link):
        """
        Get Captcha info from stage two response
        """
        stage_two_response = self.get_stage_two_response_captcha_link(download_link)
        stage_two_response = stage_two_response.get("response")

        captcha_info = {}

        captcha_link_regex = re.compile(r'(https://dropapk.to/captchas/.+?jpg)')
        try:
            captcha_link = captcha_link_regex.search(stage_two_response).group(1)
            print(f"INFO: Captcha link found: {captcha_link}")
        except:
            print(f"ERROR: Could not get captcha link")
            captcha_link = ""

        captcha_info["CaptchaLink"] = captcha_link

        names = ["rand", "id", "op"]
        for name in names:
            regex = re.compile(fr'name=\"{name}\"\s+value=\"(.+?)\"')

            try:
                value = regex.search(stage_two_response).group(1)
                print(f"INFO: {name} value found: {value}")
            except:
                print(f"ERROR: Could not get {name} value")
                value = ""

            captcha_info[name] = value

        print(json.dumps(captcha_info, indent=2))
        return captcha_info

    def get_stage_two_response_captcha_link(self, download_link):
        download_info = self.extract_file_info_from_stage_one_response(download_link)
        file_id = download_info.get("id")

        headers_dict = self.get_stage_two_headers(file_id)
        requester = CurlRequests(self.cookies_dict, headers_dict=headers_dict)
        curl_proxy = self.format_proxy()
        form_data = self.get_form_data_for_stage_two(download_info)

        response = requester.send_curl_request(download_link, proxy=curl_proxy, form_data=form_data)

        return response

    def get_stage_three_response(self, download_link):
        """
        Gets the final response containing the link
        """
        captcha_info = self.extract_captcha_info_from_stage_two_response(download_link)
        headers_dict = self.get_stage_three_headers(captcha_info)
        form_data = self.get_form_data_for_stage_three(captcha_info)
        curl_proxy = self.format_proxy()

        requester = CurlRequests(self.cookies_dict, headers_dict=headers_dict)
        response = requester.send_curl_request(download_link, proxy=curl_proxy, form_data=form_data)

        return response

    def get_final_download_link(self, download_link):
        """
        Gets the final download link from the initial link
        """
        response = self.get_stage_three_response(download_link)
        link_regex = re.compile(r'(https://s\d+.dropapk.+?)\"')

        try:
            final_link = link_regex.search(response.get("response")).group(1)
            print(f"\nFINAL LINK: {final_link}")
        except:
            print(f"ERROR: :( Could not get final link")
            final_link = ":("

        return final_link

    def download_file(self, download_link):
        """
        Gets the final download link and downloads the file at the link
        """
        final_link = self.get_final_download_link(download_link)
        curl = CurlRequests(cookies_dict=self.cookies_dict, headers_dict={})
        curl.send_curl_request(request_url=final_link, download_file=True)
        return

    def show_image(self, image_link):
        """
        Helper method. Opens the image link and displays it for the user
        """
        response = requests.get(image_link)
        Image.open(BytesIO(response.content)).show()
        return

    def get_form_data_for_stage_three(self, captcha_info):
        """
        Formats data used in the final stage of the request
        """
        rand = captcha_info.get("rand")
        id = captcha_info.get("id")
        op = captcha_info.get("op")
        captcha_link = captcha_info.get("CaptchaLink")

        if captcha_link:
            self.show_image(image_link=captcha_link)
            code = input(f"Enter the code from this image: (Image will be displayed) {captcha_link}\n:\t")
            print(f"CODE ENTERED: {code}")
            form_data = 'op={}&id={}&rand={}&referer=https%3A%2F%2Fdropapk.to%2F{}&method_free=Free+Download+%3E%3E&method_premium=&adblock_detected=0&code={}'.format(op, id, rand, id, code)
            return form_data
        else:
            print(f"\nERROR: Download link might have expired!")
            sys.exit(1)

    def get_form_data_for_stage_two(self, download_info):
        """
        Formats data used in requests
        :return:
        """
        op = download_info.get("op")
        file_id = download_info.get("id")
        fname = download_info.get("fname")

        form_data = "'op={}&usr_login=&id={}&fname={}&referer=&method_free=Free+Download+%3E%3E'".format(op, file_id, fname)
        return form_data

    def set_cookies_dict(self, download_link):
        """
        Does an initial generic curl request to get cookies
        :return:
        """
        print(f"INFO: Fedex cookie not loaded from on disk. Will obtain new one from the site")
        curl = CurlRequests(cookies_dict={}, headers_dict={})
        rnd_link = download_link
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

    def get_stage_three_headers(self, captcha_info):
        """
        Froms the headers for the final stage of the download process
        """
        file_id = captcha_info.get('id')
        stage_three_headers = self.get_stage_two_headers(file_id=file_id)
        return stage_three_headers

    def get_stage_two_headers(self, file_id):
        """
        Returns the headers for stage two of the download process
        """
        stage_two_headers = self.get_stage_one_headers()
        stage_two_headers['cache-control'] = 'max-age=0'
        stage_two_headers['origin'] = 'https://dropapk.to'
        stage_two_headers['content-type'] = 'application/x-www-form-urlencoded'
        stage_two_headers['sec-fetch-site'] = 'same-origin'
        stage_two_headers['referer'] = f'https://dropapk.to/{file_id}'

        return stage_two_headers

    def get_stage_one_headers(self):
        """
        Defines and returns curl_headers for Dropak API requests.
        This is the base setting for headers. All other header request settings derive from this one.
        :return: dictionary of curl_headers
        """

        headers_dict = {
            "authority": "dropapk.to",
            "sec-ch-ua": "\"Google Chrome\";v=\"88\", \" Not;A Brand\";v=\"99\", \"Chromium\";v=\"88\"",
            "sec-ch-ua-mobile": "?0",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "content-type": "application/json; charset=UTF-8",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "accept-language": "en-US,en;q=0.9"

        }
        return headers_dict
