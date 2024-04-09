import os
from ndfc import NDFC, Fabric
from time import sleep

FABRIC = "fabric_stage"
NETWORK = "network_rest"

URL = "https://shdu-ndfc-2"
USERNAME = "admin"
PASSWORD = os.getenv("PASSWORD")


def main():
    ndfc = NDFC(URL, USERNAME, PASSWORD)
    ndfc.logon()
    fabric = Fabric(FABRIC, ndfc)
    # check if vrf exists
    network = fabric.get_network_detail(NETWORK)
    if len(network) == 0:
        exit(0)

    # detach network from all the switches
    result = fabric.detach_network(NETWORK)
    if result:
        print(f"network {NETWORK} is detached successfully!")

    # deploy the change
    result = fabric.deploy_network(NETWORK)
    if result:
        print(f"network {NETWORK} is being undeployed....")

    while (True):
        # check if network is undeployed
        network = fabric.get_network_detail(NETWORK)
        if network[0].status == 'NA':
            break
        print("  waiting for undeploy")
        sleep(1)
    print("network {NETWORK} is undeployed successfully!")

    # delete the network itself
    result = fabric.delete_network(NETWORK)
    if result:
        print("network {NETWORK} is deleted!")


if __name__ == "__main__":
    main()
