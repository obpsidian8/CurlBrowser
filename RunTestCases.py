import json
from TrackingSiteModules.FedexTrackingCurl import FedexTrackingApi
from TrackingSiteModules.UPSTrackingCurl import UPSTrackingApi
from DropapkModules.DropapkCurl import DropakInfo


def run_test_fedex():
    """
    Get the raw json data from fedex for a tracking number given.
    """
    tracking_number = "975082865344"
    track = FedexTrackingApi(cookies_dict={}, proxy=None)
    result = track.send_tracking_query(tracking_number=tracking_number)
    print(f"\n\n{json.dumps(result, indent=2)}")

def get_ups_tracking():
    """
    Demos the use of the ups tracking requests module
    Gets the raw json data for the ups tracking numbers in the list
    :return:
    """
    tracking_list = ["1ZR302V40346943384", "1Z300WX00341127902" ]
    results_list = []

    for track_num in tracking_list:
        get_tracking = UPSTrackingApi()
        response = get_tracking.send_tracking_query(tracking_number=track_num)
        results_list.append(response)

    print(f"\nRESULTS: {json.dumps(results_list, indent=2)}\n")


def download_file_dropapk():
    downloader = DropakInfo(cookies_dict={}, proxy=None)
    link = "https://dropapk.to/2yo0kibvx54t/TestVideo.1920x1080.webm_vp9.webm"
    downloader.download_file(link)
    return


def get_file_download_link_dropapk():
    """
    Given a link from the site dropapk.com, you can get the true download link from the suite
    """
    downloader = DropakInfo(cookies_dict={}, proxy=None)
    link = "https://dropapk.to/2yo0kibvx54t/TestVideo.1920x1080.webm_vp9.webm"
    result = downloader.get_final_download_link(link)
    print(f"\n\n{json.dumps(result, indent=2)}")
    return


if __name__ == "__main__":
    get_ups_tracking()
