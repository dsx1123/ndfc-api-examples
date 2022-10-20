import os
from ndfc import NDFC, Fabric, VRF
from time import sleep

SWITCH_LIST = ["192.168.123.101", "192.168.123.102"]

FABRIC = "fabric_stage"
URL = "https://shdu-ndfc-1"
USERNAME = "admin"
PASSWORD = os.getenv("PASSWORD")
VRF_NAME = "vrf_green"


def main():
    ndfc = NDFC(URL, USERNAME, PASSWORD)
    ndfc.logon()
    fabric = Fabric(FABRIC, ndfc)
    # check if vrf exists
    vrf = fabric.get_vrf_detail(VRF_NAME)
    if len(vrf) == 0:
        # Get next available VNI and vlan id from DCNM
        vrf_id = fabric.get_next_vrf_id()
        vlan_id = fabric.get_proposed_vlan(usage='vrf')

        # Create new vrf
        vrf = VRF(FABRIC, VRF_NAME, vrf_id, vlan_id=vlan_id)
        result = fabric.create_vrf(vrf)
        if result:
            print("vrf {} is created successfully!".format(VRF_NAME))

    sleep(2)

    # Attach vrf to provided switches
    result = fabric.attach_vrf(VRF_NAME, SWITCH_LIST)
    if result:
        print("vrf {} are attached to switches {}".format(VRF_NAME, SWITCH_LIST))

    # Deploy the network configuration
    result = fabric.deploy_vrf(VRF_NAME)
    if result:
        print("vrf {} is being deployed...".format(VRF_NAME))
    sleep(2)
    while(True):
        # check if network is undeployed
        vrf = fabric.get_vrf_detail(VRF_NAME)
        if vrf[0].status == 'DEPLOYED':
            break
        print("  waiting for deploy")
        sleep(1)
    print("vrf {} is deployed successfully!".format(VRF_NAME))


if __name__ == "__main__":
    main()
