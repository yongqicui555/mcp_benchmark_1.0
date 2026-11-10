"""_summary_
Code for EVE API management char/location/UI
"""
#import
from collections import defaultdict
from pathlib import Path
import csv
import yaml
from importlib import resources

from mcp_server_evefleet.IO.API_IO import (post_name2id, post_id2name)

#manage char name<->char id
class CharID_Dict():
    def __init__(self,
                 init_file_name='setting/chardict.yaml') -> None:
        init_file = Path(init_file_name)
        self.name2id_key = "characters"
        self.id2name_key = "character"
        if init_file.exists():
            with open(init_file) as file:
                self.char_name2id = yaml.safe_load(file)
            self.char_id2name = {v:k for k,v in self.char_name2id.items()}
        else:
            # Fallback: load defaults from packaged resource if available
            try:
                with resources.files('mcp_server_evefleet').joinpath(init_file_name).open('r') as file:
                    self.char_name2id = yaml.safe_load(file) or {}
                self.char_id2name = {v:k for k,v in self.char_name2id.items()}
            except FileNotFoundError:
                self.char_name2id = {}
                self.char_id2name = {}
        self.init_file = init_file
    #check
    def check_names(self,names_list):
        return [n for n in names_list if self.char_name2id.get(n.lower(),None)==None]
    def check_ids(self,ids_list):
        return [n for n in ids_list if self.char_id2name.get(n,None)==None]
    #update names
    def update_names(self,names_list):
        need_list = self.check_names(names_list)
        if need_list:
            data = post_name2id(need_list)
            new_name2id_dic = {e['name'].lower():int(e['id']) for e in data[self.name2id_key]}
            new_id2name_dic = {v:k for k,v in new_name2id_dic.items()}
            self.char_name2id.update(new_name2id_dic)
            self.char_id2name.update(new_id2name_dic)
            self.save()
        return [self.char_name2id[name.lower()] for name in names_list]
    #update ids
    def update_ids(self,ids_list):
        need_list = self.check_ids(ids_list)
        if need_list:
            data = post_id2name(need_list)
            new_id2name_dic = {int(e['id']):e['name'].lower() for e in data if e['category']==self.id2name_key}
            new_name2id_dic = {v:k for k,v in new_id2name_dic.items()}
            self.char_name2id.update(new_name2id_dic)
            self.char_id2name.update(new_id2name_dic)
            self.save()
        return [self.char_id2name[id] for id in ids_list]
    #call
    def __call__(self, charidorname: int|str):
        #api call if not exist in dict, not good
        if isinstance(charidorname, int):
            if charidorname not in self.char_id2name:
                self.update_ids([charidorname])
            output = self.char_id2name.get(charidorname,None)
        else:
            charidorname = charidorname.lower()
            if charidorname not in self.char_name2id:
                self.update_names([charidorname])
            output = self.char_name2id.get(charidorname,None)
        return output
    
    #save to yaml
    def save(self):
        with open(self.init_file,'w') as f:
            yaml.dump(self.char_name2id,f)

#System Dict static name<->id
class Static_Dict(CharID_Dict):
    def __init__(self,
                 init_file_name,name2id_key,id2name_key) -> None:
        init_file = Path(init_file_name)
        self.name2id_key = name2id_key
        self.id2name_key = id2name_key
        if init_file.exists():
            with open(init_file) as file:
                self.char_name2id = yaml.safe_load(file)
            self.char_id2name = {v:k for k,v in self.char_name2id.items()}
        else:
            # Fallback: load defaults from packaged resource if available
            try:
                with resources.files('mcp_server_evefleet').joinpath(init_file_name).open('r') as file:
                    self.char_name2id = yaml.safe_load(file) or {}
                self.char_id2name = {v:k for k,v in self.char_name2id.items()}
            except FileNotFoundError:
                self.char_name2id = {}
                self.char_id2name = {}
        self.init_file = init_file

#Ship Dict
class ShipID_Dict():
    def __init__(self,
                 init_file_name='setting/shipid_list.csv') -> None:
        init_path = Path(init_file_name)
        if init_path.exists():
            with open(init_path) as csvfile:
                rows = csv.reader(csvfile)
                self.update_ids(rows)
        else:
            # Fallback: load from packaged resource
            with resources.files('mcp_server_evefleet').joinpath(init_file_name).open('r') as csvfile:
                rows = csv.reader(csvfile)
                self.update_ids(rows)
    #update ids
    def update_ids(self,csv_rows):
        self.ship_id2name, self.ship_name2id, self.ship_id2group, self.ship_name2group, self.group_id2name, self.name2group_id = {},{},{},{},{},{}
        self.group_id2ship = defaultdict(list)
        self.group_ids = set()
        self.type_ids = set()
        col_names = []
        for row in csv_rows:
            if not col_names:
                col_names = [n for n in row]
            else:
                type_id = int(row[0])
                group_id = int(row[1])
                type_name = row[2]
                group_name = row[3]
                self.ship_id2name[type_id] = type_name
                self.ship_name2id[type_name.lower()] = type_id
                
                self.ship_id2group[type_id] = group_id
                self.ship_name2group[type_name.lower()] = group_name.lower()
                self.group_id2ship[group_id].append(type_id)

                self.group_id2name[group_id] = group_name
                self.name2group_id[group_name.lower()] = group_id
                self.group_ids.add(group_id)
                self.type_ids.add(type_id)
        self.col_names = col_names
        self.ship_names = [n for n in self.ship_name2id.keys()]
        self.class_names = [n for n in self.group_id2ship.keys()] 
    #call
    def __call__(self, idorname: int|str):
        #auto transform
        if isinstance(idorname, int) or idorname.isdigit():
            idorname = int(idorname)
        #api call if not exist in dict, not good
        if idorname in self.ship_id2name:
            output = self.ship_id2name.get(idorname,None)
        elif isinstance(idorname, str) and idorname.lower() in self.ship_name2id:
            output = self.ship_name2id.get(idorname.lower(),None)
        elif idorname in self.group_id2name:
            output = self.group_id2name.get(idorname,None)
        elif isinstance(idorname, str) and idorname.lower() in self.name2group_id:
            output = self.name2group_id.get(idorname.lower(),None)
        else:
            raise ValueError(f"Ship id/name '{idorname}' not found in dictionary.")
        return output
    #type to group
    def typeid_to_groupid(self, type_id: int|str):
        if isinstance(type_id, int) or type_id.isdigit():
            type_id = int(type_id)
        return self.ship_id2group.get(type_id,None)
    #group to type
    def groupid_to_typeids(self, group_id: int|str):
        if isinstance(group_id, int) or group_id.isdigit():
            group_id = int(group_id)
        return self.group_id2ship.get(group_id,[])
    #type to group name
    def type_to_groupname(self, type_name: str):
        # Convert to lowercase for lookup, then capitalize first letter of result
        result = self.ship_name2group.get(type_name.lower(), None)
        return result.capitalize() if result else None
    #types to group name
    def type_to_groupnames(self, type_names: list[str]):
        # Convert to lowercase for lookup, then capitalize first letter of result
        results = [self.ship_name2group.get(name.lower(), None) for name in type_names]
        return [result.capitalize() for result in results if result]
    #group to type name
    def group_to_typenames(self, group_name: str):
        return [self.ship_id2name[n] for n in self.group_id2ship.get(self.name2group_id.get(group_name.lower(),None),[])]

#test main
if __name__ == '__main__':
    pass
        