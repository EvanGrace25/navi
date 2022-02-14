import click
from .api_wrapper import request_data
from IPy import IP


def find_target_group(tg_name):

    data = request_data("GET", '/target-groups')
    group_id = 0
    for group in data['target_groups']:
        try:
            if group['name'] == tg_name:
                group_id = group['id']
        except KeyError:
            pass
    return group_id


def create_target_group(target_name, tg_list):

    # Check to see if the Target group exists
    group_id = find_target_group(target_name)

    # Target group API takes a string of IPs. We will start the string here.
    trgstring = ""

    # Check to see if tg_list is a string
    string_test = isinstance(tg_list, str)

    # turn the list into a string separated by a comma
    if not string_test:
        for ips in tg_list:
            trgstring = trgstring + str(ips) + ","
    else:
        trgstring = tg_list

    if not tg_list:
        click.echo("\nYour request returned zero results\nAs a result, nothing happened\n")
        exit()

    click.echo("\nThese are the IPs that will be added to the target Group: {}".format(target_name))
    click.echo(tg_list)
    click.echo()

    if group_id != 0:
        # Update current Target Group
        payload = {"name": target_name, "members": trgstring, "type": "system"}
        request_data("PUT", '/target-groups/'+str(group_id), payload=payload)
    else:
        # Create a New Target Group
        payload = {"name": target_name, "members": str(trgstring), "type": "system", "acls": [{"type": "default", "permissions": 64}]}
        request_data("POST", '/target-groups', payload=payload)


def cloud_to_target_group(cloud, days, choice, target_group_name):
    query = {"date_range": days, "filter.0.filter": "sources", "filter.0.quality": "set-has", "filter.0.value": cloud}
    data = request_data('GET', '/workbenches/assets', params=query)
    target_ips = []

    for assets in data['assets']:
        target_ip_list = assets['ipv4']
        # loop through all of the IPs
        for ip in target_ip_list:
            # Check to IP type
            check_ip = IP(ip)
            check = check_ip.iptype()
            if check == choice:
                # Add the IP if there is a match
                target_ips.append(ip)

    create_target_group(target_group_name, target_ips)


@click.command(help="Create a Target Group - DEPRECATED IN T.io")
@click.option('--name', default='', required=True, help="Target Group Name")
@click.option('--ip', default='', help="Ip(s) or subnet(s) separated by coma")
@click.option('-aws', is_flag=True, help="Turn AWS assets found by the connector into a Target Group")
@click.option('-gcp', is_flag=True, help="Turn GCP assets found by the connector into a Target Group")
@click.option('-azure', is_flag=True, help="Turn Azure assets found by the connector into a Target Group")
@click.option('--days', default='30', help="Set the number of days for the IPs found by the connector. Requires: aws, gcp, or azure")
@click.option('-priv', is_flag=True, help="Set the IP(s) to be used as Private")
@click.option('-pub', is_flag=True, help="Set the IP to be used as Public")
@click.option('-migrate', is_flag=True, help="Migrate Target Groups to Tags")
def tgroup(name, ip, aws, gcp, azure, days, priv, pub, migrate):
    choice = 'PUBLIC'

    if priv:
        choice = 'PRIVATE'

    if pub:
        choice = 'PUBLIC'

    if ip != '':
        create_target_group(name, ip)

    if aws:
        cloud_to_target_group("AWS", days, choice, name)

    if gcp:
        cloud_to_target_group("GCP", days, choice, name)

    if azure:
        cloud_to_target_group("AZURE", days, choice, name)

    if migrate:

        tgroups = request_data('GET', '/target-groups')

        for group in tgroups['target_groups']:
            member = group['members']
            name = group['name']
            group_type = group['type']
            d = "Imported by Script"
            try:
                if name != 'Default':
                    payload = {"category_name": str(group_type), "value": str(name), "description": str(d), "filters": {"asset": {"and": [{"field": "ipv4", "operator": "eq", "value": str(member)}]}}}
                    data = request_data('POST', '/tags/values', payload=payload)

                    value_uuid = data["uuid"]
                    cat_uuid = data['category_uuid']
                    print("\nI've created your new Tag - {} : {}\n".format(group_type, name))
                    print("The Category UUID is : {}\n".format(cat_uuid))
                    print("The Value UUID is : {}\n".format(value_uuid))
            except:
                pass
