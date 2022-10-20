import os
from dcnm import DCNM, VRF,Fabric
from time import sleep

SWITCH_LIST = ["172.31.217.101", "172.31.217.103"]

FABRIC = "fabric-demo"
VRF_NAME = "rt-test"
VRF_TEMPLATE = "VRF_Universal_modified"


def main():
    dcnm = DCNM("172.31.219.61", "admin", os.getenv("PASSWORD"))
    # Get next available VNI and vlan id from DCNM
    fabric = Fabric(FABRIC, dcnm)
    vrf_id = dcnm.get_next_vrf_id(FABRIC)
    vlan_id = dcnm.get_proposed_vlan(FABRIC, usage='vrf')

    # Create new vrf
    vrf = VRF(fabric=fabric,
              name=VRF_NAME,
              vrf_id=vrf_id,
              vlan_id=vlan_id,
              template=VRF_TEMPLATE,
              rt="100:100",
              rd="65000:100")
    result = fabric.create_vrf(vrf)
    if result:
        print("vrf {} is created successfully!".format(VRF_NAME))

    sleep(2)

    # Attach vrf to provided switches
    result = fabric.attach_vrf(vrf, SWITCH_LIST)
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
        sleep(10)
    print("vrf {} is deployed successfully!".format(VRF_NAME))


if __name__ == "__main__":
    main()
