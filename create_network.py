import os
from ndfc import NDFC, Fabric, Network
from time import sleep

SWITCH_LIST = ["192.168.123.101", "192.168.123.102"]
INTERFACE_LIST = ['Ethernet1/37', 'Ethernet1/38', 'Ethernet1/39', 'Ethernet1/40']

FABRIC = "fabric_stage"
URL = "https://shdu-ndfc-1"
USERNAME = "admin"
PASSWORD = os.getenv("PASSWORD")

NETWORK = "network_rest"
GATEWAY = "10.3.123.1/24"
VRF = "vrf_green"


def main():
    ndfc = NDFC(URL, USERNAME, PASSWORD)
    ndfc.logon()
    fabric = Fabric(FABRIC, ndfc)
    # check if vrf exists
    network = fabric.get_network_detail(NETWORK)
    # Get next available VNI and vlan id from DCNM
    if len(network) == 0:
        network_id = fabric.get_next_segid()
        vlan_id = fabric.get_proposed_vlan()

        # Create new network
        network = Network(FABRIC, NETWORK, network_id, VRF,
                          vlan_id=vlan_id, gateway=GATEWAY)
        result = fabric.create_network(network)
        if result:
            print("network {} is created successfully!".format(NETWORK))

    sleep(2)

    # Attach network to provided switches and interfaces
    result = fabric.attach_network(NETWORK, SWITCH_LIST, INTERFACE_LIST, "")
    if result:
        print("network {} are attached to switches {} on interfaces {}".format(NETWORK, SWITCH_LIST, INTERFACE_LIST))

    sleep(2)

    # Deploy the network configuration
    result = fabric.deploy_network(NETWORK)
    if result:
        print("network {} is being deployed...".format(NETWORK))

    while(True):
        # check if network is undeployed
        network = fabric.get_network_detail(NETWORK)
        if network[0].status == 'DEPLOYED':
            break
        print("  waiting for deploy")
        sleep(3)
    print("network {} is deployed successfully!".format(NETWORK))


if __name__ == "__main__":
    main()
