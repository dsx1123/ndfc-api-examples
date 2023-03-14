""" This example only works with NDFC 12.1.2e and above
"""
import os
import argparse
import getpass
import logging
from datetime import datetime, timedelta
import time
from ndclient import Client
from urllib.parse import urlparse


__author__ = "Author: Shangxin Du(shdu@cisco.com)"
APP_NAME = "NDFC ISSU Example"
APP_DESCRIPTION = "This example will upgrade group of switch with provided image"
COMPLIANCE_TIMEOUT = 300
STAGE_TIMEOUT = 1200
UPGRADE_TIMEOUT = 1800
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class URL():
    GET_UPLOADED_IMAGES = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupload/uploaded-images-table"
    SCP_UPLOAD = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupload/scp-upload"
    LOCAL_UPLOAD = "/appcenter/cisco/ndfc/api/v1/imagemanagement/imageupload/smart-image-upload"
    GET_IMAGE_POLICES = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies"
    GET_ATTACHED_POLICY = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/attached-policies"
    CREATE_IMAGE_POLICY = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/platform-policy"
    DELETE_IMAGE_POLICY = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policy"
    GET_PACKAGES = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/nxos"
    DETACH_IMAGE_POLICY = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/detach-policy"
    ATTACH_IMAGE_POLICY = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/attach-policy"
    GET_ISSU_DEVICES = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/packagemgnt/issu"
    STAGE_IMAGE = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/stage-image"
    ISSU_UPGRADE = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupgrade/upgrade-image"


class Upgrade():
    def __init__(self, client: Client):
        self._client = client

    def get_uploaded_images(self) -> dict:
        r = client.send(URL.GET_UPLOADED_IMAGES, "get")
        return r.data.get("lastOperDataObject", [])

    def get_uploaded_image(self, image: str) -> dict:
        images = self.get_uploaded_images()
        for i in images:
            if not i["name"] == image:
                continue
            return i
        return None

    def get_image_policies(self) -> dict:
        r = client.send(URL.GET_IMAGE_POLICES, "get")
        return r.data.get("lastOperDataObject", [])

    def get_issu_devices(self, switches: list) -> dict:
        r = client.send(URL.GET_ISSU_DEVICES, "get")
        devices = {}
        if not r.ok:
            return devices
        for sw in r.data.get("lastOperDataObject", []):
            if not sw["deviceName"] in switches:
                continue
            devices[sw["deviceName"]] = sw
        return devices

    def normallize_nxos_package(self, image: str) -> str:
        r = self.get_uploaded_image(image)
        version = r["version"]
        prefix = image.split(".")[0]
        os_type = r["osType"]
        package = f"{version}_{prefix}_{os_type}"
        return package

    def image_exist(self, image: str) -> bool:
        images = self.get_uploaded_images()
        for i in images:
            if i["name"] == image:
                return True
        return False

    def scp_upload(self, server: str, username: str, password: str, path: str) -> bool:
        data = {
            "server": server,
            "filePath": path,
            "userName": username,
            "password": password,
            "acceptHostkey": True  # always accept the host key
        }
        r = client.send(URL.SCP_UPLOAD, "post", data)
        if not r.ok:
            return False
        return True

    def local_upload(self, path: str) -> bool:
        with open(path, "rb") as f:
            data = {
                "file": f
            }
            r = client.send_file(URL.LOCAL_UPLOAD, data)
            if not r.ok:
                return False
            return True

    def create_image_policy(self, name: str, image: str, platform: str) -> bool:
        package = self.normallize_nxos_package(image)

        data = {
            "policyName": name,
            "policyType": "PLATFORM",
            "nxosVersion": package,
            "platform": "N9K"
        }
        r = client.send(URL.CREATE_IMAGE_POLICY, "post", data)
        if r.ok:
            return True
        else:
            logging.error(r.data)
            return False

    def delete_image_policy(self, name: str) -> bool:
        data = {
            "policyNames": [name]
        }
        r = client.send(URL.DELETE_IMAGE_POLICY, "delete", data)
        if r.ok:
            return True
        else:
            logging.error(r.data)
            return False

    def detach_policy(self, devices: dict) -> bool:
        sn_list = [v["serialNumber"] for v in devices.values()]
        serial_number = ",".join(sn_list)
        r = client.send(f"{URL.DETACH_IMAGE_POLICY}?serialNumber={serial_number}", "delete")
        if r.ok:
            return True
        else:
            return False

    def attach_policy(self, devices: dict, policy: str) -> bool:
        data = {
            "mappingList": []
        }
        for d in devices.values():
            mapping = {
                "policyName": policy,
                "hostName": d["deviceName"],
                "serialNumber": d["serialNumber"],
                "ipAddr": "",
                "platform": "",
                "bootstrapMode": ""
            }
            data["mappingList"].append(mapping)

        r = client.send(URL.ATTACH_IMAGE_POLICY, "post", data)
        if r.ok:
            return True
        else:
            logging.error(f"failed to attach policy: {r.data}")
            return False

    def wait_for_compliance(self, devices: dict) -> bool:
        switches = [v["deviceName"] for v in devices.values()]
        issu_status = self.get_issu_devices(switches)
        finished = False
        start_time = datetime.now()
        timeout = timedelta(seconds=COMPLIANCE_TIMEOUT)
        while(start_time + timeout > datetime.now()):
            issu_status = self.get_issu_devices(switches)
            status = [s["status"] for s in issu_status.values()]
            if "In-Progress" in status:
                time.sleep(3)
                continue
            finished = True
            break
        return finished

    def wait_for_staging(self, devices: dict) -> bool:
        switches = [v["deviceName"] for v in devices.values()]
        issu_status = self.get_issu_devices(switches)
        finished = False
        start_time = datetime.now()
        timeout = timedelta(seconds=STAGE_TIMEOUT)
        while(start_time + timeout > datetime.now()):
            issu_status = self.get_issu_devices(switches)
            stage_status = [s["imageStaged"] for s in issu_status.values()]
            if "In-Progress" in stage_status:
                time.sleep(5)
                continue
            finished = True
            break
        return finished

    def wait_for_upgrade(self, devices: dict) -> bool:
        switches = [v["deviceName"] for v in devices.values()]
        issu_status = self.get_issu_devices(switches)
        finished = False
        start_time = datetime.now()
        timeout = timedelta(seconds=UPGRADE_TIMEOUT)
        while(start_time + timeout > datetime.now()):
            issu_status = self.get_issu_devices(switches)
            upgrade_status = [s["upgrade"] for s in issu_status.values()]
            if "In-Progress" in upgrade_status:
                time.sleep(5)
                continue
            finished = True
            break
        return finished

    def stage_image(self, devices: dict) -> bool:
        self.wait_for_compliance(devices)
        data = {
            "sereialNum": []
        }
        for v in devices.values():
            data["sereialNum"].append(v["serialNumber"])
        r = client.send(URL.STAGE_IMAGE, "post", data)
        if r.ok:
            return True
        else:
            logging.error(f"failed to stage images, error code {r.status_code}, {r.data}")
            return False

    def trigger_upgrade(self, policy_name: str, devices: dict) -> None:
        self.wait_for_staging(devices)
        data = {
            "devices": [
            ],
            "issuUpgrade": True,
            "issuUpgradeOptions1": {
                "nonDisruptive": True,
                "forceNonDisruptive": False,
                "disruptive": False
            },
            "issuUpgradeOptions2": {
                "biosForce": False
            },
            "epldUpgrade": False,
            "epldOptions": {
                "moduleNumber": "ALL",
                "golden": False
            },
            "reboot": False,
            "rebootOptions": {
                "configReload": False,
                "writeErase": False
            },
            "pacakgeInstall": False,
            "pacakgeUnInstall": False
        }
        for v in devices.values():
            device = {
                "serialNumber": v["serialNumber"],
                "policyName": policy_name
            }
            data["devices"].append(device)
        r = client.send(URL.ISSU_UPGRADE, "post", data)
        if r.ok:
            return True
        else:
            logging.error(f"failed to upgrade, error: {r.data}")
            return False


# utils functions
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=APP_DESCRIPTION, epilog=__author__)
    parser.add_argument("--address", "-a",
                        dest="address",
                        required=True,
                        help="NDFC Url, ex, https://ndfc.example.com")
    parser.add_argument("--username", "-u",
                        dest="username",
                        required=True,
                        help="NDFC username")
    parser.add_argument("--password", "-p",
                        dest="password",
                        required=True,
                        help="NDFC password")
    parser.add_argument("--login_domain", "-d",
                        dest="login_domain",
                        default="local",
                        help="NDFC login domain")
    parser.add_argument("--switch", "-s",
                        dest="switches",
                        required=True,
                        nargs="*",
                        help="Switch hostnames are upgraded")
    parser.add_argument("--image", "-i",
                        dest="image",
                        required=True,
                        help="""local or remote location of image,
                        for example, /images/nxos64.10.2.1.F.bin, scp://admin@sftp-server/opt/file/nxos64.10.2.1.F.bin,
                        """)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    # input parameters
    url = ""
    username = ""
    password = ""
    login_domain = "local"
    switches = []
    duu = {}  # hashtable of devies under upgrade
    policy_name = ""
    version = ""

    remote_server = ""
    remote_username = ""
    remote_password = ""
    file_path = ""

    args = parse_args()

    if args.image.startswith("scp://"):
        image_parsed = urlparse(args.image)
        file_path = image_parsed.path
        # remote location need follow the format scp://[username]@[server]/[path]
        # password is provided via stdin
        remote_server = image_parsed.netloc.split("@")[1]
        remote_login = image_parsed.netloc.split("@")[0]
        remote_username = remote_login.split(":")[0]
        if len(remote_login.split(":")) < 2:
            remote_password = getpass.getpass(prompt="SCP server password:")
        else:
            remote_password = remote_login.split(":")[1]
    else:
        file_path = args.image
    image = os.path.basename(file_path)

    url = args.address
    username = args.username
    password = args.password
    login_domain = args.login_domain
    switches = args.switches

    client = Client(url, username, password)
    logged_in = client.login()
    if not logged_in:
        print("invalid login!")
        os.exit(-1)
    upg_inst = Upgrade(client)
    duu = upg_inst.get_issu_devices(switches)

    # upload image if not existed
    image_exist = upg_inst.image_exist(image)
    if not image_exist:
        if remote_server:
            logging.info(f"Uploading image {image} from remote_server {remote_server}")
            resp = upg_inst.scp_upload(remote_server, remote_username, remote_password, file_path)
        else:
            logging.info(f"Uploading image {image} from local {file_path}")
            resp = upg_inst.local_upload(file_path)
    else:
        logging.info(f"{image} exists, skip uploading")

    version = upg_inst.get_uploaded_image(image)["version"]
    policy_name = f"nxos_upgrade_{version}"

    # Create image policy
    result = upg_inst.create_image_policy(policy_name, image, "N9k/N3K")
    if not result:
        logging.error("Failed to create image policy")

    # detach policy if attached
    logging.info(f"detach current policy associated with switches {switches}")
    upg_inst.detach_policy(duu)
    logging.info(f"attach policy {policy_name} to switches {switches}")
    upg_inst.attach_policy(duu, policy_name)

    # stage image
    logging.info(f"staging image {image} to switches {switches}")
    upg_inst.stage_image(duu)

    logging.info(f"upgrade switches {switches} to {version}")
    upg_inst.trigger_upgrade(policy_name, duu)

    # Final step, delete image policy
    ok = upg_inst.wait_for_upgrade(duu)
    if not ok:
        logging.error("failed to upgrade or upgrade timeout")
    logging.info(f"detach policy {policy_name} from switches {switches}")
    upg_inst.detach_policy(duu)
    logging.info(f"delete policy {policy_name}")
    upg_inst.delete_image_policy(policy_name)
