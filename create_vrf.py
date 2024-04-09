import os
from ndfc import NDFC, Fabric, VRF
from time import sleep

SWITCH_LIST = ["192.168.123.101", "192.168.123.102"]

FABRIC = "fabric_stage"
URL = "https://shdu-ndfc-2"
USERNAME = "admin"
PASSWORD = os.getenv("PASSWORD")
VRF_NAME = "vrf_green"


def main():
    ndfc = NDFC(URL, USERNAME, PASSWORD)
    ndfc.logon()
    fabric = Fabric(FABRIC, ndfc)
    # check if vrf exists
    vrf = fabric.get_vrf_detail(VRF_NAME)
    if len(vrf) != 0:
        print(f"{VRF_NAME} already exists!")
        exit(1)

    # Get next available VNI and vlan id from NDFC
    vrf_id = fabric.get_next_vrf_id()
    vlan_id = fabric.get_proposed_vlan(usage='vrf')

    # Create new vrf
    vrf = VRF(FABRIC, VRF_NAME, vrf_id, vlan_id=vlan_id)
    result = fabric.create_vrf(vrf)
    if result:
        print(f"vrf {VRF_NAME} is created successfully!")

    sleep(2)

    # Attach vrf to the provided switches
    result = fabric.attach_vrf(VRF_NAME, SWITCH_LIST)
    if result:
        print(f"vrf {VRF_NAME} are attached to switches {SWITCH_LIST}")

    # Deploy
    result = fabric.deploy_vrf(VRF_NAME)
    if result:
        print(f"vrf {VRF_NAME} is being deployed...")

    sleep(2)

    while (True):
        # check if vrf is undeployed
        vrf = fabric.get_vrf_detail(VRF_NAME)
        if vrf[0].status == "DEPLOYED":
            break
        print("  waiting for deploy")
        sleep(1)
    print(f"vrf {VRF_NAME} is deployed successfully!")


if __name__ == "__main__":
    main()
