"""_summary_
    Functions for all requires features with comprehensive error handling and debugging
    
"""
import threading
import time
import math
import logging
import traceback
from collections import defaultdict
from multiprocessing.dummy import Pool as ThreadPool
from typing import Optional, Dict, List, Tuple, Any, Union
from functools import wraps
from mcp_server_evefleet.IO.API_IO import get_char_info
from mcp_server_evefleet.IO.fleet_api import (put_sso_invitation,
                          put_sso_move,
                          get_sso_fleetmotd,
                          get_sso_fleetmembers,
                          get_sso_fleetwings,
                          post_create_squad,
                          post_create_wing,
                          del_sso_kick,
                          put_sso_fleet,
                          )
from mcp_server_evefleet.static_manage import CharID_Dict,ShipID_Dict,Static_Dict

class loop_memory:
    def __init__(self, max_size=10):
        self.max_size = max_size
        self.data = []
    def append(self, item):
        if len(self.data) >= self.max_size:
            self.data.pop(0)
        self.data.append(item)
    def get_data(self):
        return self.data
    def clear(self):
        self.data = []
    def head(self):
        if not self.data:
            return None
        return self.data[0]
    def tail(self):
        if not self.data:
            return None
        return self.data[-1]
    def __getitem__(self, index):
        if isinstance(index, slice):
            return self.data[index]
        elif isinstance(index, int):
            return self.data[index % len(self.data)]
    def __index__(self, index):
        if index < 0 or index >= len(self.data):
            raise IndexError("Index out of range")
        return self.data[index]
    def __len__(self):
        return len(self.data)
    def __iter__(self):
        return iter(self.data)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fleet_support.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Custom Exception Classes
class FleetSupportError(Exception):
    """Base exception for fleet support operations"""
    pass

class WarpCalculationError(FleetSupportError):
    """Exception raised for warp calculation errors"""
    pass

class FleetManagementError(FleetSupportError):
    """Exception raised for fleet management errors"""
    pass

class DScanAnalysisError(FleetSupportError):
    """Exception raised for D-Scan analysis errors"""
    pass

class APIError(FleetSupportError):
    """Exception raised for API communication errors"""
    pass

class ValidationError(FleetSupportError):
    """Exception raised for input validation errors"""
    pass

# Decorator for error handling and logging
def handle_errors(func):
    """Decorator to add error handling and logging to functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logger.debug(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    return wrapper

# Input validation functions
def validate_numeric(value: Any, name: str, min_val: Optional[float] = None, max_val: Optional[float] = None) -> float:
    """Validate numeric input"""
    try:
        num_val = float(value)
        if min_val is not None and num_val < min_val:
            raise ValidationError(f"{name} must be >= {min_val}, got {num_val}")
        if max_val is not None and num_val > max_val:
            raise ValidationError(f"{name} must be <= {max_val}, got {num_val}")
        return num_val
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be a valid number, got {value}")

def validate_id(value: Any, name: str, min_val: Optional[int] = None) -> str:
    """Validate ID input"""
    try:
        id_val = int(value)
        if min_val is not None and id_val < min_val:
            raise ValidationError(f"{name} must be >= {min_val}, got {id_val}")
        return str(id_val)
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be a valid ID, got {value}")

def validate_string(value: Any, name: str, min_length: int = 0, max_length: Optional[int] = None) -> str:
    """Validate string input"""
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be a string, got {type(value)}")
    if len(value) < min_length:
        raise ValidationError(f"{name} must be at least {min_length} characters long")
    if max_length and len(value) > max_length:
        raise ValidationError(f"{name} must be at most {max_length} characters long")
    return value

def validate_list(value: Any, name: str, min_length: int = 0, max_length: Optional[int] = None) -> list:
    """Validate list input"""
    if not isinstance(value, list):
        raise ValidationError(f"{name} must be a list, got {type(value)}")
    if len(value) < min_length:
        raise ValidationError(f"{name} must have at least {min_length} items")
    if max_length and len(value) > max_length:
        raise ValidationError(f"{name} must have at most {max_length} items")
    return value

@handle_errors
def multi_auto_inv(access_token: str, fleet_id: Union[int, str], charlist_dic: Union[Dict, List[Dict]], sleep_time: float = 0.1) -> None:
    """Send multiple fleet invitations with error handling.
    
    Args:
        access_token: SSO access token
        fleet_id: Fleet ID
        charlist_dic: Character dictionary or list of character dictionaries
        sleep_time: Sleep time between invitations in seconds
        
    Raises:
        FleetManagementError: If invitation process fails
        ValidationError: If input validation fails
        APIError: If API calls fail
    """
    try:
        # Validate inputs
        access_token = validate_string(access_token, "access_token", min_length=10)
        fleet_id = validate_id(fleet_id, "fleet_id", min_val=1)
        sleep_time = validate_numeric(sleep_time, "sleep_time", min_val=0, max_val=10)
        
        # Ensure charlist_dic is a list
        if not isinstance(charlist_dic, list):
            charlist_dic = [charlist_dic]
        
        charlist_dic = validate_list(charlist_dic, "charlist_dic", min_length=1, max_length=100)
        
        logger.info(f'Starting multiple invitations for {charlist_dic}')
        
        successful_invites = 0
        failed_invites = 0
        
        for i, char_dic in enumerate(charlist_dic):
            try:
                if not isinstance(char_dic, dict):
                    raise ValidationError(f"Character entry {i} must be a dictionary")
                
                if 'char_id' not in char_dic:
                    raise ValidationError(f"Character entry {i} missing 'char_id'")
                
                char_id = validate_id(char_dic['char_id'], f"char_id[{i}]", min_val=1)
                char_role = char_dic.get('char_role', 'squad_member')
                squad_id = char_dic.get('squad_id', None)
                wing_id = char_dic.get('wing_id', None)
                
                logger.debug(f"Inviting character {char_id} with role {char_role}")
                
                put_sso_invitation(access_token, fleet_id, char_id, char_role, squad_id, wing_id)
                successful_invites += 1
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                failed_invites += 1
                logger.error(f"Failed to invite character {i}: {str(e)}")
                # Continue with other invitations
                continue
        
        logger.info(f'Invitation process completed: {successful_invites} successful, {failed_invites} failed')
        
        if failed_invites > 0 and successful_invites == 0:
            raise FleetManagementError("All invitations failed")
        
    except Exception as e:
        if isinstance(e, (ValidationError, FleetManagementError)):
            raise
        raise FleetManagementError(f"Failed to process multiple invitations: {str(e)}") from e

###class for checking fleet members:
class fleet_manager():
    def __init__(self, access_token: str,
                 fleet_id: Union[int, str],
                 main_char_id: Union[int, str],
                 group_ship_ids: List[int] = None,
                 bomb_alt_ids: List[Union[int, str]] = None,
                 auto_update: bool = True,
                 ship_dict: Optional[ShipID_Dict] = None,
                 system_dict: Optional[Static_Dict] = None
                 ) -> None:
        try:
            # Validate inputs
            self.access_token = validate_string(access_token, "access_token", min_length=10)
            self.fleet_id = validate_id(fleet_id, "fleet_id", min_val=1)
            self.main_char_id = validate_id(main_char_id, "main_char_id", min_val=1)
            
            # Initialize with defaults
            self.group_ship_ids = group_ship_ids if group_ship_ids is not None else [12038, 12032, 11377, 12034]
            self.alts = bomb_alt_ids if bomb_alt_ids is not None else []
            
            # Initialize data structures
            self.fleet_history = loop_memory(max_size=10)
            self.fleet_loss_history = loop_memory(max_size=5)
            self.fleet_struct = []
            self.fleet_struct_old = []
            self.fleet_members_list = []
            self.fleet_members_composition = {}
            self.main_char_dic = {}
            
            # Initialize dictionaries
            self.ship_dict = ship_dict if ship_dict else ShipID_Dict()
            self.char_dict = CharID_Dict()
            self.system_dict = system_dict if system_dict else Static_Dict('setting/system_dict.yaml','systems','solar_system')
            
            self.fleet_motd = ''
            self.auto_update = auto_update
            self.thread_pool = ThreadPool(5)
            
            logger.info(f"Initializing fleet manager for fleet {self.fleet_id}, main character {self.main_char_id}")
            
            # Initialize fleet data
            try:
                self.user_info = get_char_info(self.main_char_id)
                self.renew_motd()
                self.renew_members()
                
                # Update character names
                if self.fleet_members_list:
                    fleet_mem_ids = [member['character_id'] for member in self.fleet_members_list]
                    self.char_dict.update_ids(fleet_mem_ids)
                
                if auto_update:
                    self.start_background_update()
                    
                logger.info("Fleet manager initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize fleet data: {str(e)}")
                # Don't raise here, allow partial initialization
                
        except Exception as e:
            logger.error(f"Failed to initialize fleet manager: {str(e)}")
            raise FleetManagementError(f"Fleet manager initialization failed: {str(e)}") from e

    def start_background_update(self):
        threading.Thread(target=self._update_loop, daemon=True).start()
    def _update_loop(self):
        while True:
            time.sleep(60)
            self.renew_members()
    def determine_ship_type_filter(self, ship_type_filter=None):
        """
        Determine what ship types to filter based on priority:
        1. Explicitly mentioned in function args (ship_type_filter)
        2. Most common ship class in fleet (need >= 50%)
        
        Args:
            ship_type_filter (List[int], optional): Explicitly specified ship type IDs to filter
            
        Returns:
            List[int]: Ship type IDs to use for filtering
        """
        # Priority 1: Use explicitly provided ship type filter
        if ship_type_filter is not None:
            return ship_type_filter
        
        # Priority 2: Find most common ship class (>= 50%)
        if not self.fleet_members_list:
            # Fallback to default if no fleet members
            return self.group_ship_ids
        
        # Count ship classes in fleet
        ship_class_counts = {}
        total_members = len(self.fleet_members_list)
        ship_type_to_class_map = {}  # Cache for ship_type_id -> class mapping
        
        for member in self.fleet_members_list:
            ship_type_id = member.get('ship_type_id')
            if ship_type_id is not None:
                # Get ship class for this ship type
                try:
                    # Convert ship_type_id to ship_class using ship_class_dict
                    ship_class_id = self.ship_dict.typeid_to_groupid(ship_type_id)
                    if ship_class_id:
                        ship_type_to_class_map[ship_type_id] = ship_class_id
                        ship_class_counts[ship_class_id] = ship_class_counts.get(ship_class_id, 0) + 1
                except (ValueError, KeyError) as e:
                    # Skip ships that can't be mapped to classes
                    continue
        # Find ship classes that make up >= 50% of the fleet
        threshold = total_members * 0.5
        dominant_ship_classes = []
        
        for ship_class_id, count in ship_class_counts.items():
            if count >= threshold:
                dominant_ship_classes.append(ship_class_id)
        
        # Convert dominant ship classes back to ship type IDs
        if dominant_ship_classes:
            dominant_ship_types = []
            for ship_type_id, ship_class_id in ship_type_to_class_map.items():
                if ship_class_id in dominant_ship_classes:
                    dominant_ship_types.append(ship_type_id)
            
            return dominant_ship_types
        else:
            return self.group_ship_ids

    #divide/move member !!need rewrite
    def fleet_formation(self, members_in_squad=8, location_match=True, number_of_squads=None, ship_type_filter=None):
        """
        Organize fleet members into squads and wings
        
        Args:
            members_in_squad (int): Maximum members per squad (used when number_of_squads is None)
            location_match (bool): Only include members in same system as main character
            number_of_squads (int, optional): Specific number of squads to create. If provided, 
                                            overrides members_in_squad calculation
            ship_type_filter (List[int], optional): Specific ship type IDs to filter. If not provided,
                                                  will use most common ship type (>=50%) or default
        """
        members_in_squad = int(members_in_squad)
        self.renew_members() #get lastest info
        members_count = len(self.fleet_members_list)
        wings_count = len(self.fleet_struct)
        move_dictlist = []
        
        # Determine which ship types to filter
        target_ship_ids = self.determine_ship_type_filter(ship_type_filter)
        
        #count useful member
        final_sq_counts = defaultdict(list)
        useful_members = []
        other_members = []
        for member in self.fleet_members_list:
            location_same = not location_match or member['solar_system_id']==self.main_char_dic['solar_system_id']
            if member['ship_type_id'] in target_ship_ids and location_same:
                useful_members.append(member)
                final_sq_counts[member['squad_id']].append(member)
            else:
                other_members.append(member)
        
        # Calculate required squads based on either number_of_squads or members_in_squad
        if number_of_squads is not None:
            req_squads = int(number_of_squads)
        else:
            req_squads = int(len(useful_members) / members_in_squad + 0.999)
        ### put all useful members in first wing / different squad , other in other wings
        #create wing/squad if need
        if wings_count <2:
            for i in range(wings_count-1,2):
                new_wing_id = post_create_wing(self.access_token,self.fleet_id)
                new_sq_id = post_create_squad(self.access_token,self.fleet_id,new_wing_id)
                new_sq_dic = {'id': new_sq_id, 'name': '', 'members':[]}
                new_wing_dic = {'id': new_wing_id, 'name': '', 'squads':[new_sq_dic]}
                self.fleet_struct.append(new_wing_dic)
        first_wing_dic = self.fleet_struct[0]
        first_wing_id = first_wing_dic['id']
        sq_list = first_wing_dic['squads']
        sq_count = len(sq_list)
        if sq_count < req_squads:
            for i in range(sq_count-1,req_squads):
                new_sq_id = post_create_squad(self.access_token,self.fleet_id,first_wing_dic['id'])
                new_sq_dic = {'id': new_sq_id, 'name': '', 'members':[]}
                first_wing_dic['squads'].append(new_sq_dic)
        #other wing
        other_wing = self.fleet_struct[-1]
        other_sq_list = other_wing['squads']
        other_sq_len = len(other_sq_list)
        if other_sq_len==0:
            new_sq_id = post_create_squad(self.access_token,self.fleet_id,other_wing['id'])
            new_sq_dic = {'id': new_sq_id, 'name': '', 'members':[]}
            other_wing['squads'].append(new_sq_dic)
        
        #gen move dict for useful member
        final_sq_ids = []
        count = 0
        for sq_dic in first_wing_dic['squads']:
            final_sq_ids.append(sq_dic['id'])
            count += 1
            if count>=req_squads:
                break
        
        # Initialize final_sq_counts for all target squads
        for sq_id in final_sq_ids:
            if sq_id not in final_sq_counts:
                final_sq_counts[sq_id] = []
        
        # Distribute members evenly across the specified number of squads
        if number_of_squads is not None:
            # Even distribution across specified number of squads
            members_per_squad = len(useful_members) // req_squads
            extra_members = len(useful_members) % req_squads
            
            # Clear existing distribution and redistribute evenly
            final_sq_counts = {sq_id: [] for sq_id in final_sq_ids}
            
            member_index = 0
            for i, sq_id in enumerate(final_sq_ids):
                # Add base members per squad
                for _ in range(members_per_squad):
                    if member_index < len(useful_members):
                        final_sq_counts[sq_id].append(useful_members[member_index])
                        member_index += 1
                
                # Add one extra member to first few squads if there are extras
                if i < extra_members and member_index < len(useful_members):
                    final_sq_counts[sq_id].append(useful_members[member_index])
                    member_index += 1
                    
            # Generate move commands for all members that need to be moved
            for sq_id, members in final_sq_counts.items():
                for member in members:
                    if member['squad_id'] != sq_id:  # Only move if not already in correct squad
                        new_dic = {'character_id': member['character_id'], 'squad_id': sq_id, 'wing_id': first_wing_id}
                        move_dictlist.append(new_dic)
        else:
            # Original logic for members_in_squad based distribution
            for sq_id in [k for k in final_sq_counts.keys()]:
                members_need_move = []
                from_squad = final_sq_counts[sq_id]
                if sq_id not in final_sq_ids:
                    members_need_move = from_squad
                elif len(from_squad) > members_in_squad:
                    members_need_move = from_squad[members_in_squad:]
                    final_sq_counts[sq_id] = from_squad[:members_in_squad]
                else:
                    members_need_move = []
                #choose a squad to move
                while members_need_move:
                    e_member = members_need_move.pop()
                    for des_sq_id in final_sq_ids:
                        if len(final_sq_counts[des_sq_id]) < members_in_squad:
                            final_sq_counts[des_sq_id].append(e_member)
                            new_dic = {'character_id': e_member['character_id'], 'squad_id': des_sq_id, 'wing_id': first_wing_id}
                            move_dictlist.append(new_dic)
                            break
        #gen move for other member
        for mem in other_members:
            if mem['wing_id']==first_wing_dic['id']:
                new_dic = {'character_id': mem['character_id'], 'squad_id': other_wing['squads'][0]['id'], 'wing_id': other_wing['id']}
                move_dictlist.append(new_dic)
        #move member
        move_chars = []
        for e_dic in move_dictlist:
            #put_sso_move(self.access_token,self.fleet_id,**e_dic)
            move_chars.append((self.access_token,self.fleet_id,e_dic['character_id'],e_dic.get('role','squad_member'),e_dic.get('squad_id',None),e_dic.get('wing_id',None)))
        self.thread_pool.starmap(put_sso_move,move_chars)
        
    #invite member
    def fleet_invite(self,char_ids):
        if not isinstance(char_ids,list):
            char_ids = [char_ids]
        char_dic_list = []
        fleet_ids, access_tokens = [], []
        for char_id in char_ids:
            new_dic = {'char_id':char_id}
            char_dic_list.append(new_dic)
            fleet_ids.append(self.fleet_id)
            access_tokens.append(self.access_token)
        #multi_auto_inv(self.access_token,self.fleet_id,char_dic_list)
        self.thread_pool.starmap(multi_auto_inv,zip(access_tokens,fleet_ids,char_dic_list))
    #kick member
    def fleet_kick(self,char_ids,sleep_time=0.1):
        if not isinstance(char_ids,list):
            char_ids = [char_ids]
        for char_id in char_ids:
            del_sso_kick(self.access_token,self.fleet_id,char_id)
            time.sleep(sleep_time)
    #output fleet static
    def output_fleet_static(self):
        out_dict = {
            "composition_class": self.fleet_members_composition_class,
            "composition": self.fleet_members_composition,
            "motd": self.fleet_motd,
            "fleet_id": self.fleet_id,
        }
        return out_dict
    def renew_motd(self):
        self.fleet_motd = get_sso_fleetmotd(self.access_token,self.fleet_id)
        return self.fleet_motd
    #renew fleet members and record in history
    @handle_errors
    def renew_members(self) -> None:
        """Renew fleet members list with error handling.
        
        Raises:
            FleetManagementError: If member renewal fails
            APIError: If API call fails
        """
        try:
            logger.debug(f"Renewing fleet members for fleet {self.fleet_id}")
            
            # Get fleet members from API
            fleet_members_list = get_sso_fleetmembers(self.access_token, self.fleet_id)
            
            if not isinstance(fleet_members_list, list):
                raise FleetManagementError("Invalid fleet members data received from API")
            
            # Find main character
            main_char_found = False
            for member in fleet_members_list:
                if not isinstance(member, dict):
                    logger.warning(f"Invalid member data: {member}")
                    continue
                    
                if int(member.get('character_id', 0)) == int(self.main_char_id):
                    self.main_char_dic = member
                    main_char_found = True
                    break
            
            if not main_char_found:
                logger.warning(f"Main character {self.main_char_id} not found in fleet members")
                self.main_char_dic = {}
            
            # Update fleet data
            self.fleet_members_list = fleet_members_list
            self.fleet_members_composition = self.get_fleet_composition(fleet_members_list)
            self.fleet_members_composition_class = self.get_fleet_composition_class(fleet_members_list)
            
            # Create history entry
            history_each = {
                "timestamp": time.time(),
                "main_char_dic": self.main_char_dic,
                "members": fleet_members_list,
                "composition": self.fleet_members_composition,
                "motd": self.fleet_motd,
                "fleet_id": self.fleet_id,
            }
            
            self.fleet_history.append(history_each)
            
            # Build fleet structure
            try:
                self.build_fleet_tree(fleet_members_list)
            except Exception as e:
                logger.error(f"Failed to build fleet tree: {str(e)}")
                # Continue without fleet tree
            
            # Estimate losses if we have history
            if len(self.fleet_history) > 1:
                try:
                    fleet_loss = self._estimate_fleet_loss()
                    if fleet_loss:
                        self.fleet_loss_history.append({
                            "timestamp": time.time(),
                            "loss": fleet_loss
                        })
                except Exception as e:
                    logger.error(f"Failed to estimate fleet loss: {str(e)}")
                    # Continue without loss estimation
            
            logger.info(f"Fleet members renewed successfully: {len(fleet_members_list)} members")
            
        except Exception as e:
            if isinstance(e, FleetManagementError):
                raise
            raise FleetManagementError(f"Failed to renew fleet members: {str(e)}") from e

    #build fleet tree structue base on fleet->wing->squad
    def build_fleet_tree(self,fleet_members_list):
        '''
        finial fleet struct[{
            id*	integer($int64) title: get_fleets_fleet_id_wings_id id integer
            name*	string title: get_fleets_fleet_id_wings_name name string
            squads*	[
            {
                id*	integer($int64) title: get_fleets_fleet_id_wings_squad_id id integer
                name*	string title: get_fleets_fleet_id_wings_squad_name name string
                members* [
                    {
                        character_id*
                        join_time*
                        role*
                        ship_type_id*
                        solar_system_id*
                        squad_id*
                        wing_id*
                        takes_fleet_warp*
                    }
                    
                ]
            }]
        }]
        '''
        fleet_struct = get_sso_fleetwings(self.access_token,self.fleet_id)
        for wing_dic in fleet_struct:
            wing_id = wing_dic['id']
            for squad_dic in wing_dic['squads']:
                squad_id = squad_dic['id']
                squad_dic['members'] = []
                for member_dic in fleet_members_list:
                    if member_dic['wing_id']==wing_id and member_dic['squad_id']==squad_id:
                        squad_dic['members'].append(member_dic)
        #self update
        self.fleet_struct_old = self.fleet_struct
        self.fleet_struct = fleet_struct
    #update motd
    def update_motd(self, text, append=True):
        self.renew_motd()
        if append:
            put_sso_fleet(self.access_token, self.fleet_id, self.fleet_motd + text)
        else:
            put_sso_fleet(self.access_token, self.fleet_id, text)
    #get fleet composition
    def get_fleet_composition(self, fleet_members_list, location_match=False, main_char_dic=None):
        """
        Get fleet composition from fleet members list.
        Returns:
            Dict of ship type ID and name with their counts.
        """
        ship_count = {}
        for member in fleet_members_list:
            if location_match and main_char_dic['ship_type_id'] != member['ship_type_id']:
                continue
            ship_type_id = member['ship_type_id']
            ship_name = self.ship_dict(ship_type_id)
            ship_count[ship_name] = ship_count.get(ship_name, 0) + 1
        return ship_count
    #get fleet composition class
    def get_fleet_composition_class(self, fleet_members_list):
        class_count = {}
        for member in fleet_members_list:
            ship_type_id = member['ship_type_id']
            ship_name = self.ship_dict(ship_type_id)
            class_name = self.ship_dict.type_to_groupname(ship_name)
            class_count[class_name] = class_count.get(class_name, 0) + 1
        return class_count
    #estimate fleet loss
    def _estimate_fleet_loss(self, location_match=False):
        if len(self.fleet_history) < 2:
            return None
        now_time = self.fleet_history[-1]['timestamp']
        prev_time = self.fleet_history[-2]['timestamp']
        minute_diff = max((now_time - prev_time) / 60.0, 1)
        now_fleet_dict = self.fleet_history[-1]
        prev_fleet_dict = self.fleet_history[-2]
        if location_match:
            member_now = self.get_fleet_composition(now_fleet_dict['members'], location_match=True, main_char_dic=now_fleet_dict['main_char_dic'])
            member_prev = self.get_fleet_composition(prev_fleet_dict['members'], location_match=True, main_char_dic=now_fleet_dict['main_char_dic'])
        else:
            member_now = now_fleet_dict['composition']
            member_prev = prev_fleet_dict['composition']
        
        own_loss = {k: round((member_prev.get(k, 0) - member_now.get(k, 0)) / minute_diff, 2)
                    for k in member_prev if member_prev.get(k, 0) > member_now.get(k, 0)}
        return own_loss
    #get user info
    def get_user_info(self):
        return self.user_info
    
if __name__ == "__main__":
    pass
