import os
from ndfc import NDFC, Fabric
from time import sleep

FABRIC = "fabric_stage"
VRF = "vrf_green"

URL = "https://shdu-ndfc-2"
USERNAME = "admin"
PASSWORD = os.getenv("PASSWORD")


def main():
    ndfc = NDFC(URL, USERNAME, PASSWORD)
    ndfc.logon()
    fabric = Fabric(FABRIC, ndfc)
    # check if vrf exists
    vrf = fabric.get_vrf_detail(VRF)
    if len(vrf) == 0:
        exit(0)

    # detach network from all the switches
    result = fabric.detach_vrf(VRF)
    if result:
        print("vrf {} is detached successfully!".format(VRF))

    # deploy the change
    result = fabric.deploy_vrf(VRF)
    if result:
        print("network {} is being undeployed....".format(VRF))

    while(True):
        # check if network is undeployed
        network = fabric.get_vrf_detail(VRF)
        if network[0].status == 'NA':
            break
        print("  waiting for undeploy")
        sleep(1)
    print("vrf {} is undeployed successfully!".format(VRF))

    # delete the vrf itself
    result = fabric.delete_vrf(VRF)
    if result:
        print("vrf {} is deleted!".format(VRF))


if __name__ == "__main__":
    main()
