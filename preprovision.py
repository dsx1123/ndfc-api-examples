import os
from dcnm import DCNM, Fabric, Switch
from time import sleep

FABRIC = "fabric-demo"

switch_vars = {
    "address": "172.31.219.63",
    "gateway": "172.31.216.1/22",
    "hostname": "N93600-GX-S2",
    "version": "9.3(7)",
    "model": "N9K-C93600CD-GX",
    "sn": "FDO23300B6C",
    "username": "admin",
    "password": os.getenv("PASSWORD")
}

cable_plan = {
    "fabric_links": [
        {
            "src_address": "172.31.186.160",
            "dst_address": switch_vars["address"],
            "src_int": "Ethernet1/54",
            "dst_int": "Ethernet1/4",
            "template": "int_pre_provision_intra_fabric_link",
        }
    ]
}


def main():
    dcnm = DCNM("172.31.219.61", "admin", os.getenv("PASSWORD"))
    fabric = Fabric(FABRIC, dcnm)
    switch = Switch(**switch_vars)
    
    # pre-provision switch 
    result = fabric.pre_provision(switches=[switch])
    print("pre-provision switch {}:".format(switch.address))
    print(result)

    # set role of switch
    role = "border"
    result = fabric.set_role(switch, role)
    print("set role of switch {} to {}".format(switch.address, role))
    print(result)

    # add fabric link
    inv = fabric.get_inventory()
    for link in cable_plan["fabric_links"]:
        link["src_sn"] = inv[link["src_address"]]["serialNumber"] 
        link["dst_sn"] = inv[link["dst_address"]]["serialNumber"] 
        link["src_device"] = inv[link["src_address"]]["logicalName"] 
        link["dst_device"] = inv[link["dst_address"]]["logicalName"] 
        result = fabric.add_link(**link)

    # save fabric configuration, generate configuration of switch
    result = fabric.config_save()
    print(result)

    # waiting for switch come online
    while(True):
        sleep(5)
        fabric.rediscover_switch(switch)
        sleep(5)
        fabric.get_inventory()
        mode = fabric.inventory[switch.address]["mode"]
        status = fabric.inventory[switch.address]["status"]
        print("swich {} mode is {}, status is {}".format(switch.address, mode, status))
        if "Normal" == mode and "ok" == status:
            print("switch {} has done poap!".format(switch.address))
            break

    # save and deploy reset of configuration
    result = fabric.config_save()
    print(result)
    fabric.config_preview()
    result = fabric.config_deploy()
    if result:
        print("switch {} has been add to {} as {}".format(switch.address, fabric.name, role))


if __name__ == "__main__":
    main()
