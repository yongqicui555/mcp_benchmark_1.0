"""_summary_
Code for EVE API management fleet
"""
#import
import requests
import time
import json

#utils func
def check_role_position(role,squad_id,wing_id):
    allow = False
    if role=="squad_member" or role=="fleet_commander":
        allow = True
    elif role=='wing_commander' and wing_id:
        allow = True
    elif role=='squad_commander' and wing_id and squad_id:
        allow = True
    else:
        allow = False
    return allow
    

#get fleet id
def get_sso_fleetid(access_token, character_id, character_name = None):
    sso_path = ("https://esi.evetech.net/latest/characters/{}/fleet/?datasource=tranquility".format(character_id))
    headers = {
        "Authorization": "Bearer {}".format(access_token)
    }

    res = requests.get(sso_path, headers=headers)
    res.raise_for_status()

    data = res.json()
    fleet_id = data['fleet_id']
    return fleet_id
#get fleet members
def get_sso_fleetmembers(access_token, fleet_id):
    '''
        Returns:
        get_fleets_fleet_id_members_ok[
        maxItems: 256
        title: get_fleets_fleet_id_members_ok
        200 ok array
        get_fleets_fleet_id_members_200_ok{
        character_id*	integer($int32)
        title: get_fleets_fleet_id_members_character_id
        character_id integer

        join_time*	string($date-time)
        title: get_fleets_fleet_id_members_join_time
        join_time string

        role*	string
        title: get_fleets_fleet_id_members_role
        Member’s role in fleet

        Enum:
        Array [ 4 ]
        role_name*	string
        title: get_fleets_fleet_id_members_role_name
        Localized role names
        ship_type_id*	integer($int32)
        title: get_fleets_fleet_id_members_ship_type_id
        ship_type_id integer

        solar_system_id*	integer($int32)
        title: get_fleets_fleet_id_members_solar_system_id
        Solar system the member is located in
        squad_id*	integer($int64)
        title: get_fleets_fleet_id_members_squad_id
        ID of the squad the member is in. If not applicable, will be set to -1

        station_id	integer($int64)
        title: get_fleets_fleet_id_members_station_id
        Station in which the member is docked in, if applicable

        takes_fleet_warp*	boolean
        title: get_fleets_fleet_id_members_takes_fleet_warp
        Whether the member take fleet warps
        wing_id*	integer($int64)
        title: get_fleets_fleet_id_members_wing_id
        ID of the wing the member is in. If not applicable, will be set to -1

        }]
    '''
    sso_path = ("https://esi.evetech.net/latest/fleets/{}/members/?datasource=tranquility".format(fleet_id))
    headers = {
        "Authorization": "Bearer {}".format(access_token)
    }

    res = requests.get(sso_path, headers=headers)
    res.raise_for_status()

    data = res.json()
    return data
#get fleet motd
def get_sso_fleetmotd(access_token, fleet_id, character_name=None):
    sso_path = ("https://esi.evetech.net/latest/fleets/{}/?datasource=tranquility".format(fleet_id))
    headers = {
        "Authorization": "Bearer {}".format(access_token)
    }

    res = requests.get(sso_path, headers=headers)
    res.raise_for_status()

    data = res.json()
    fleet_motd = data['motd']
    return fleet_motd

#get wings/squads
def get_sso_fleetwings(access_token, fleet_id):
    sso_path = ("https://esi.evetech.net/latest/fleets/{}/wings/?datasource=tranquility".format(fleet_id))
    headers = {
        "Authorization": "Bearer {}".format(access_token)
    }

    res = requests.get(sso_path, headers=headers)
    #print("\nMade request to {} with headers: "
    #        "{}".format(sso_path, res.request.headers))
    res.raise_for_status()

    data = res.json()
    return data

#put fleet motd
def put_sso_fleet(access_token, fleet_id, fleet_motd, free_move=True):
    sso_path = ("https://esi.evetech.net/latest/fleets/{}/?datasource=tranquility".format(fleet_id))
    headers = {
        "Authorization": "Bearer {}".format(access_token)
    }
    param = {
        "is_free_move": free_move,
        "motd": fleet_motd
    }
    payload = json.dumps(param)
    res = requests.put(sso_path,data=payload, headers=headers)
    if res.status_code==500:
        time.sleep(5)
        res = requests.put(sso_path,data=payload, headers=headers)
    res.raise_for_status()
    return
#put auto inv
def put_sso_invitation(access_token, fleet_id, character_id,role = "squad_member", squad_id=None, wing_id=None):
    sso_path = ("https://esi.evetech.net/latest/fleets/{}/members/?datasource=tranquility".format(str(int(fleet_id))))
    headers = {
        "Authorization": "Bearer {}".format(access_token)
    }
    param = {
        "character_id": character_id,
        "role": role,
        #"squad_id": 0,
        #"wing_id": 0
    }
    check_role_position(role,squad_id,wing_id)
    if squad_id and wing_id:
        param['squad_id'] = squad_id
        param['wing_id'] = wing_id
    payload = json.dumps(param)
    res = requests.post(sso_path,data=payload, headers=headers)
    res.raise_for_status()
    return
#move fleet members
def put_sso_move(access_token, fleet_id, character_id, role='squad_member', squad_id=None, wing_id=None):
    '''
    If a character is moved to the fleet_commander role, neither wing_id or squad_id should be specified.
    If a character is moved to the wing_commander role, only wing_id should be specified.
    If a character is moved to the squad_commander role, both wing_id and squad_id should be specified.
    If a character is moved to the squad_member role, both wing_id and squad_id should be specified.
    '''
    sso_path = ("https://esi.evetech.net/latest/fleets/{}/members/{}/?datasource=tranquility".format(fleet_id,character_id))
    headers = {
        "Authorization": "Bearer {}".format(access_token)
    }
    param = {
        "role": role,
        #"squad_id": 0,
        #"wing_id": 0
    }
    if squad_id:
        param['squad_id'] = squad_id
    if wing_id:
        param['wing_id'] = wing_id
    payload = json.dumps(param)
    res = requests.put(sso_path,data=payload, headers=headers)
    res.raise_for_status()
    return
#post create wing
def post_create_wing(access_token, fleet_id):
    sso_path = ("https://esi.evetech.net/latest/fleets/{}/wings/?datasource=tranquility".format(fleet_id))
    headers = {
        "Authorization": "Bearer {}".format(access_token)
    }

    res = requests.post(sso_path, headers=headers)
    res.raise_for_status()

    data = res.json()
    return data['wing_id']
#post create squad
def post_create_squad(access_token, fleet_id, wing_id):
    sso_path = ("https://esi.evetech.net/latest/fleets/{}/wings/{}/squads/?datasource=tranquility".format(fleet_id,wing_id))
    headers = {
        "Authorization": "Bearer {}".format(access_token)
    }

    res = requests.post(sso_path, headers=headers)
    res.raise_for_status()

    data = res.json()
    return data['squad_id']

#del kick member
def del_sso_kick(access_token, fleet_id, character_id):
    sso_path = ("https://esi.evetech.net/latest/fleets/{}/members/{}/?datasource=tranquility".format(fleet_id,character_id))
    headers = {
        "Authorization": "Bearer {}".format(access_token)
    }
    res = requests.delete(sso_path, headers=headers)
    res.raise_for_status()
    return