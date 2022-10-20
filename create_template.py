import os
from dcnm import DCNM, Template


def main():
    dcnm = DCNM("172.31.219.61", "admin", os.getenv("PASSWORD"))
    template_file = "./VRF_Universal_modified.template"
    name = os.path.basename(template_file).split('.')[0]
    vrf_template = Template(name=name,
                            platforms="All",
                            temp_type="PROFILE",
                            temp_sub_type="VXLAN",
                            tags="vrf")
    with open(template_file) as f:
        vrf_template.content = f.read()

    result = dcnm.create_template(vrf_template)
    if result:
        print("template {} is created".format(name))


if __name__ == "__main__":
    main()
