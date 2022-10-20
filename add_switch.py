import os
from ndfc import NDFC, Fabric, Switch
from time import sleep

FABRIC = "fabric_stage"
URL = "https://shdu-ndfc-1"
USERNAME = "admin"
PASSWORD = os.getenv("PASSWORD")


def main():
    ndfc = NDFC(URL, USERNAME, PASSWORD)
    ndfc.logon()
    fabric = Fabric(FABRIC, ndfc)
    switch = Switch(address="192.168.123.103",
                    username="admin",
                    password="ins3965!")
    result = fabric.register_switch(switch=switch,
                                    preserve_config=False)
    print("register switch {}:".format(switch.address))
    print(result)

    role = "border"
    result = fabric.set_role(switch, role)
    print("set role of switch {} to {}".format(switch.address, role))
    print(result)

    while(True):
        sleep(10)
        fabric.get_inventory()
        mode = fabric.inventory[switch.address]["mode"]
        print("swich {} mode is {}".format(switch.address, mode))
        if "Normal" == mode:
            print("switch {} has done migration!".format(switch.address))
            break
    result = fabric.config_save()
    print(result)
    fabric.config_preview()
    result = fabric.config_deploy()
    if result:
        print("switch {} has been added to {} as {}".format(switch.address, fabric.name, role))


if __name__ == "__main__":
    main()
