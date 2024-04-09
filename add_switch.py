import os
from ndfc import NDFC, Fabric, Switch
from time import sleep

FABRIC = "fabric_stage"
URL = "https://shdu-ndfc-2"
USERNAME = "admin"
PASSWORD = os.getenv("PASSWORD")


def main():
    ndfc = NDFC(URL, USERNAME, PASSWORD)
    ndfc.logon()
    fabric = Fabric(FABRIC, ndfc)
    switch = Switch(address="192.168.123.103",
                    username="admin",
                    password=PASSWORD)
    result = fabric.register_switch(switch=switch,
                                    preserve_config=False)
    print("register switch {switch.address}:")
    print(result)

    role = "border"
    result = fabric.set_role(switch, role)
    print(f"set role of switch {switch.address} to {role}")
    print(result)

    while (True):
        sleep(10)
        fabric.get_inventory()
        mode = fabric.inventory[switch.address]["mode"]
        print(f"swich {switch.address} mode is {mode}")
        if "Normal" == mode:
            print(f"switch {switch.address} has done migration!")
            break
    result = fabric.config_save()
    print(result)
    fabric.config_preview()
    result = fabric.config_deploy()
    if result:
        print(f"switch {switch.address} has been added to the fabric {fabric.name} as {role}")


if __name__ == "__main__":
    main()
