import shlex
import subprocess
import json
import gzip


class CurlRequests:
    """
    Alternative to using python requests where curl works but equivalent python request code does not get a result
    """

    def __init__(self, cookies_dict: dict, headers_dict):
        """
        :param cookies_dict:
        :param headers_dict: Use Classes from "CurlSiteTemplates" to get default curl_headers for certain sites. If you know the curl_headers, you can just supply them as a dictionary
        If you dont have a dict of either parameter, you can pass and empty dict into the constructor and set the curl "curl_headers" and "curl_cookie_header" manually
        """
        self.cookies_dict = cookies_dict
        self.headers_dict = headers_dict
        self.cookies_as_single_str = ""
        self.curl_headers = ""
        self.curl_cookie_header = None

        self.set_headers_dict_if_empty()

    def set_headers_dict_if_empty(self):
        """
        Although headers dict is a required parameter in the __init__ method, it will allow and empty dict to be passed into it to initialize the instance.
        Just made this for special use cases where you absolutely don't know what headers to use. For using this class, implementer should know what headers to use.
        However, if you don't, pass in an empty dict and it will be changed to a 'random' set of headers defined below
        :return:
        """
        if not self.headers_dict:
            print(f"INFO: Caught empty headers dict passed into instance. Special case")
            self.headers_dict = self.regular_browser_headers_dict()
        else:
            print(f"INFO: Headers dict was passed into instance already.")

        return

    def regular_browser_headers_dict(self):
        """
        For if we want to send a request to a site just to get the response.
        In this case, we dont know specifically what headers the server requires.
        We are not trying to get a specific type of response (Like adding items to cart during purchasing)
        :return:
        """
        headers_dict = {
            "authority": "www.google.com",
            "sec-ch-ua": "\"Google Chrome\";v=\"87\", \" Not;A Brand\";v=\"99\", \"Chromium\";v=\"87\"",
            "sec-ch-ua-mobile": "?0",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "x-client-data": "CK61yQEIj7bJAQijtskBCMS2yQEIqZ3KAQisx8oBCPbHygEItMvKAQijzcoBCNzVygEIwZzLAQjVnMsBGO24ygEYucLKAQ==",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-dest": "document",
            "accept-language": "en-US,en;q=0.9"

        }
        return headers_dict

    def build_headers(self):
        """
        Formats the header dictionary into the format used by curl requests
        :return:String representing formatted curl_headers for curl command
        """
        for key, value in self.headers_dict.items():
            if not self.curl_headers:
                self.curl_headers = f"-H '{key}: {value}' "
            else:
                self.curl_headers = f"{self.curl_headers}  -H '{key}: {value}' "

        return self.curl_headers

    def build_cookie_header(self):
        """
        Formats the cookie dictionary into the format used by the curl request
        :return: String representing formatted cookies_as_single_str for curl command
        """
        for key, value in self.cookies_dict.items():
            if not self.cookies_as_single_str:
                self.cookies_as_single_str = f"{key}={value}"
            else:
                self.cookies_as_single_str = f"{self.cookies_as_single_str}; {key}={value}"

        self.curl_cookie_header = f" -H 'cookie: {self.cookies_as_single_str}' "
        return self.curl_cookie_header

    def build_body_data(self, data):
        """
        Formats the body data into the format used by curl requests.
        Used internally by the build_full_curl_cmd method
        :param data:
        :return: String representing formatted body/data portion of curl command
        """
        return f" --data-binary '{data}' "

    def build_form_data(self, form_data, url_encode_data):
        """
        Formats form data into the proper format for curl.
        This involes appending the proper tag
        :param form_data:
        :return:
        """
        if url_encode_data:
            return f"--data-urlencode {form_data}"
        return f" -d {form_data}"

    def build_full_curl_cmd(self, request_url, data, add_compression, proxy, specified_method, form_data, page_redirects, include, url_encode_data, download_file):
        """
        Builds the full curl request. Used by the send_curl_request method. (Not externally)
        :param proxy:
        :param include:
        :param page_redirects:
        :param specified_method:
        :param add_compression:
        :param request_url:
        :param data:
        :param form_data: curl form data
        :return: String representin curl command
        """
        "proxy: Should be specified as follows in example: http://38.109.22.251:21270"

        if download_file:
            download_file_option = " -O "
        else:
            download_file_option = ""

        # Add location header for pages that redirect
        if page_redirects is True:
            location_option = " --location "
        else:
            location_option = ""

        # Add option to include connection information
        if include:
            include_option = " -i "
        else:
            include_option = ""

        # Add proxy information to curl request
        if proxy:
            proxy_option = f" --proxy {proxy} "
        else:
            proxy_option = ""

        # Build curl headers
        if not self.curl_headers:
            self.build_headers()

        # Build cookie header
        if not self.curl_cookie_header:
            self.build_cookie_header()

        curl_command_prefix = f"curl{download_file_option}{location_option}{include_option}{proxy_option}"

        # Add specified method if one is specified
        if specified_method:
            print(f"INFO: Applying specified method to prefix: {specified_method}")
            specified_method_flag = f"-X '{specified_method}'"
        else:
            specified_method_flag = ""

        # If data needs to be sent, with request, add it to the request
        if data:
            body = self.build_body_data(data)
            full_cmd = f"{curl_command_prefix} {request_url} {specified_method_flag} {self.curl_headers} {self.curl_cookie_header} {body}"
        elif form_data:
            form_data = self.build_form_data(form_data, url_encode_data)
            full_cmd = f"{curl_command_prefix} {request_url} {specified_method_flag} {self.curl_headers} {self.curl_cookie_header} {form_data}"
        else:
            full_cmd = f"{curl_command_prefix} {request_url} {specified_method_flag} {self.curl_headers} {self.curl_cookie_header}"

        # Add compression if need. Never really used
        if add_compression:
            full_cmd = full_cmd + " --compressed"

        print(f"INFO: Full command formed:\n\t{full_cmd}\n\nINFO: Ready to send")
        return full_cmd

    def send_curl_request(self, request_url, data=None, add_compression=False, proxy=None, specified_method=None, form_data=None, page_redirects=False, include=False, verbose=True, url_encode_data=False, download_file=False):

        """
        Will build and send a curl request to the specified request url using the curl_headers and dict supplied
        in the init method and optional data supplied in this method
        :param verbose:
        :param form_data:
        :param page_redirects:
        :param include:
        :param request_url:
        :param data:
        :param add_compression:Always set to False. Output can be received without compression even when running curl from terminal requires compression to receive output (eg html document)
        :param proxy: Should be specified as follows in example: http://38.109.22.251:21270
        :param specified_method: If no method specified, will send a default curl request
        :return:
        """
        full_cmd = self.build_full_curl_cmd(request_url, data, add_compression, proxy, specified_method, form_data, page_redirects, include, url_encode_data, download_file)
        args = shlex.split(full_cmd)
        print(f"INFO: Sending command")
        response = {}
        try:
            if download_file:
                response = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                response = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8)

            stderr = response.stderr
            stdout = response.stdout

            if stdout and stderr:
                # If both stdout and stderr exist, there is a valid response/ output data we need to see.
                # Stderr in this case will just be diagnostics. So will only grab stdout
                response = stdout
            elif stderr:
                response = stderr
            elif stdout:
                response = stdout
            else:
                response = b''

            # Try decompressing data
            try:
                print(f"INFO: Trying to decompress the data")
                response = gzip.decompress(response)
                print(f"INFO: Successfully decompressed data")
            except Exception as e:
                print(f"ERROR: Data decompression failed. DETAILS {e}")

            try:
                print(f"INFO: Trying regular decoding.")
                response = response.decode()
                print(f"INFO: Successfully decoded data")
            except Exception as e:
                print(f"ERROR: Regular decoding failed ! DETAILS {e}")

            # Convert JSON string to actual JSON (If response is JSON string)
            try:
                print(f"INFO: Converting any JSON string response to actual JSON")
                response = json.loads(response)
                print(f"INFO: JSON loads applied successfully to response. Returning JSON loaded response.")
            except Exception as e:
                print(f"ERROR: Could not apply JSON loads to decoded response. Server is not returning JSON formatted response. DETAILS: {e}")
                # Conversion will fail if not JSON formatted string.
                # Make our own JSON (dictionary) and put the entire response as the value of the "response" key
                response = {"response": response}

        except TimeoutError as e:
            print(f"ERROR: Occurred while send request: DETAILS {e}")
            response['Timeout'] = True

        except Exception as e:
            print(f"ERROR: Occurred while send request: DETAILS {e}")

        if verbose:
            print(f"INFO:\t\nServer Response: {response}")
        return response
