import re
import sys
import yaml
import logging
import argparse
import importlib.util
import csv
import os
import inflect

from omero import gateway
    
def _import(patch:str):
    """
    Imports a python file containing omero wrapper patches
    """
    spec = importlib.util.spec_from_file_location(patch, patch)
    module = importlib.util.module_from_spec(spec)

    # This step is required to actually load the module
    spec.loader.exec_module(module)

class OmeroTagger():
    OPERATIONS={
        "gt": lambda a, b: a > b,
        "lt": lambda a, b: a < b,
        "eq": lambda a, b: a == b,
        "ge": lambda a, b: a >= b,
        "le": lambda a, b: a <= b,
        "ne": lambda a, b: a != b,
        "match": lambda a, b: re.match(b,a) is not None,
    }

    def __init__(self, conn: gateway.BlitzGateway, tag_rules: dict, patch=None) -> None:
        # run patch if provided
        if patch is not None:
            _import(patch)

        # connect to omero if necessary
        self.conn = conn
        if self.conn.isConnected() is False:
            self.conn.connect()

        # start pluralizer
        self._ie = inflect.engine()
        self.plural_noun = self._ie.plural_noun
        self.singular_noun = self._ie.singular_noun

        # compile rules
        rules = self.compile_rules(tag_rules)
        self.name_rules, self.attr_rules, self.attr_names, self.path_tree = rules

        # blank tagmap
        self.tag_map = {}
        
    def close(self) -> None:
        self.conn.close()

    def _get_method(self, obj, attr_name):
        obj_class = obj.__class__  # get the class of the object
        lower_case_attr_name = attr_name.lower()

        # First attempt: Look for methods in the class definition
        for name in dir(obj_class):
            if name.lower() == 'get' + lower_case_attr_name or name.lower() == 'list' + lower_case_attr_name:
                return getattr(obj, name)

        # Second attempt: Directly try to get the attribute
        try:
            return getattr(obj, 'get' + lower_case_attr_name.capitalize())
        except AttributeError:
            try:
                return getattr(obj, 'list' + lower_case_attr_name.capitalize())
            except AttributeError:
                print(f"invalid: {attr_name}")
                return lambda: print(f'could not get property: {attr_name}')


    def _validate_attr_path(self, path: list[str]):
        """
        Checks attribute path by doing mock tests on wrappers
        """
        for i, obj in enumerate(path[:-1]):
            wrapper = gateway.KNOWN_WRAPPERS.get(obj)
            if wrapper is None:
                logging.warning(f"Could not validate or invalidate path: {[path]}: Wrapper for object: {obj} does not exist! Continuing, but errors may occur!")
                break
            attr = path[i+1]
            if self._get_method(wrapper(), attr) is None and self._get_method(wrapper(), self.plural_noun(attr)) is None:
                raise ValueError(f'Could not find method to get: {attr} from: {wrapper.__name__}')

    def compile_rules(self, tag_rules):
        name_rules, attr_rules, attr_names, path_tree = [], {}, [], {}

        for tag_rule in tag_rules:
            if 'capture' in tag_rule: # name based tagging
                if 'name' in tag_rule: # enforce exclusivity 
                    logging.error('The "capture" and "name" attributes are incompatible. This is a typo or you are looking for "format"')
                    raise ValueError()
                capture_regex = tag_rule['capture']

                try: # check regex 
                    compiled_regex=re.compile(capture_regex)
                    if compiled_regex.groups < 1: # force capture regex
                        raise re.error(f"No capture groups!")
                except re.error as e:
                    logging.error(f"Error parsing yaml! Invalid capture regex: {capture_regex}")
                    raise e
                
                if 'format' in tag_rule: # check format
                    test = [""] * compiled_regex.groups
                    assert type(tag_rule['format']) is str
                    try:
                        tag_rule['format'].format(test)
                    except IndexError as e:
                        logging.error(f"regex capture group gets a different number of variables than format expects. capture gets: {compiled_regex.groups} format string: {tag_rule['format']}")
                        raise e
                else: 
                    tag_rule.update({'format': "{}"})
                    
                if 'object' in tag_rule: # check object
                    assert type(tag_rule['object']) is str
                else: # assume image
                    tag_rule.update({'object': "image"})

                if 'include_extension' in tag_rule: # check inc_ext flag or set default
                    assert type(tag_rule['include_extension']) is bool
                else:
                    tag_rule.update({'include_extension':False}) 

                if 'blacklist' in tag_rule: # check blacklist
                    assert type(tag_rule['blacklist']) is list
                else:
                    tag_rule.update({'blacklist':[]})

                # valid name rule!
                name_rules.append(tag_rule)
                if tag_rule['object'] not in path_tree: 
                    path_tree.update({tag_rule['object']:{}})
                else:
                    continue
                
            # attribute based tagging 
            elif 'name' in tag_rule: 
                assert type(tag_rule['name']) is str

                if 'absolute' in tag_rule: # default absolute rules (unset false tags)
                    assert type(tag_rule['absolute']) is bool
                else:
                    tag_rule.update({'absolute':True})

                if 'rules' not in tag_rule: # check attribute tagging rules
                    logging.error(f"No rules provided! Tag: {tag_rule['name']}")
                    raise ValueError()
                rules = tag_rule['rules']
                assert type(rules) is list
                for rule in rules:
                    if 'attribute_path' not in rule or 'operation' not in rule or 'value' not in rule:
                        logging.error(f"Incomplete rule! path: {rule.get('attribute_path')}, operation: {rule.get('operation')}, value: {rule.get('value')}")
                        raise ValueError()
                    
                    if rule['operation'] not in self.OPERATIONS.keys(): # check operation
                        logging.error(f"Unknown operation: {rule['operation']}")
                        raise ValueError()

                    path = rule['attribute_path'] # check attribute path syntax TODO check wrappers for attributes
                    assert type(path) is list
                    if len(path) < 2:
                        logging.error(f"Path should be a minumum of two items, the root item and the attribute")
                        raise ValueError()
                    self._validate_attr_path(path)
                    
                    try: # try to cast as float, else leave as is
                        rule['value'] = float(rule['value'])
                    except ValueError:
                        pass 
                    
                    # update tree
                    tree=path_tree
                    for obj in path:
                        assert type(obj) is str
                        if obj not in tree:
                            tree.update({obj:{}})
                        tree=tree[obj]
                
                    if path[-2] in attr_rules:
                        attr_rules[path[-2]].append(tag_rule)
                    else:
                        attr_rules.update({path[-2]:[tag_rule,]})

                    if path[-1] not in attr_names:
                        attr_names.append(path[-1])

            # invalid tagging rule type
            else:
                logging.error(f"Invalid tag rule! rule:{tag_rule}")
                raise ValueError()
        return name_rules, attr_rules, attr_names, path_tree
    

    def _apply_name_rules(self, obj, name_rules):
        """
        Checks name_rules for rules governing this 
        """
        rv = []
        name = obj.getName()
        for rule in name_rules:
            if rule['include_extension'] is True:
                string = name
            else:
                string = name.split('.')[0]
            matches = re.findall(rule['capture'], string) 
            if matches:
                for match in matches:
                    skip = False
                    if type(match) is str:
                        match = [match,]
                    for string in match:
                        if string in rule['blacklist']:
                            skip=True
                    if skip is not True:
                        rv.append(rule['format'].format(*match))
        return rv
        
    def _apply_attr_rules(self, obj, obj_type, attr_rules, attr_names, path_tree):
        """
        Checks attr_rules for rules governing this object_type. 
        RECURSIVE
        """
        keys=list(path_tree.keys())
        tag_vals, false_tag_vals = [], []
        for attr_name in keys:
            # if last, is attribute, generate and use a getter, check rules for this attr and append valid tags
            if attr_name in attr_names:
                getter = self._get_method(obj, attr_name)
                val = getter()
                if hasattr(val, 'getValue'): # autounwrap
                    val = val.getValue()
                
                for tag_rule in attr_rules.get(obj_type, []):
                    follows_rule = True
                    for rule in tag_rule['rules']:
                        if rule['attribute_path'][-1] == attr_name:
                            op = self.OPERATIONS[rule['operation']]
                            const_val = rule['value']
                            if op(val, const_val) is not True:
                                follows_rule = False
                                break
                        else: 
                            follows_rule = None
                            continue
                    if follows_rule is True:
                        tag_vals.append(tag_rule['name'])
                    elif follows_rule is False and tag_rule['absolute'] is True:
                        false_tag_vals.append(tag_rule['name'])

            # else we need to keep walking
            else:
                singlular=self.singular_noun(attr_name)
                if singlular is False:
                    singlular = attr_name

                getter = self._get_method(obj, self.plural_noun(singlular))
                gotten = getter()
                
                for parent_obj in gotten:
                    try:
                        tv, ftv = self._apply_attr_rules(parent_obj, attr_name, attr_names, path_tree[attr_name])
                    except TypeError as e:
                        print(f"Caught error {e}")
                      
                    tag_vals.extend(tv)
                    false_tag_vals.extend(ftv)

        return tag_vals, false_tag_vals
        
    def _create_tag(conn, tag_val):
        tag = gateway.TagAnnotationWrapper(conn)
        tag.setDescription("Autotagged")
        tag.setValue(tag_val)
        tag.save()
        return tag

    def _get_tag(self,tag_val):
        tag = self.tag_map.get(tag_val)
        if tag is None:
            tag=list(self.conn.getObjects('TagAnnotation', attributes={'textValue': tag_val}))
            if not tag:
                tag = self._create_tag(self.conn, tag_val)
            else:
                tag = tag[0]
            
            self.tag_map.update({tag_val:tag})
        return tag

    def apply_rules(self, name_rules=None, attr_rules=None, attr_names=None, path_tree=None):
        if name_rules is None:
            name_rules = self.name_rules
        if attr_rules is None:
            attr_rules = self.attr_rules
        if attr_names is None:
            attr_names = self.attr_names
        if path_tree is None:
            path_tree = self.path_tree

        if dry_run:
            with open('tags.csv', 'a', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['Slide Name', 'True Tags', 'False Tags'])

        for parent_obj_type in path_tree.keys():
            for parent_obj in self.conn.getObjects(parent_obj_type):
                name_tagvals = self._apply_name_rules(parent_obj, name_rules)
                attr_tagvals, remove_tags = self._apply_attr_rules(parent_obj, parent_obj_type, attr_rules, attr_names, path_tree[parent_obj_type])
                
                true_tag_vals, false_tag_vals = [*set([*name_tagvals, *attr_tagvals])], [*set(remove_tags)]

                if dry_run:
                    with open('tags.csv', 'a', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([parent_obj.getName(), ', '.join(true_tag_vals), ', '.join(false_tag_vals)])                    
                    continue
                print(f" {parent_obj.getName()}: TRUE: {true_tag_vals} FALSE: {false_tag_vals}")                            
                existing_links = parent_obj.listAnnotations()
                for tag_val in false_tag_vals:
                    to_delete=[]
                    for ann in existing_links:
                        if type(ann) is gateway.TagAnnotationWrapper:
                            val = ann.getValue()
                            if val == tag_val:
                                to_delete.append(ann.link.id)
                            if val in true_tag_vals:
                                true_tag_vals.remove(val)
                    if to_delete:
                        self.conn.deleteObjects("ImageAnnotationLink", to_delete, wait=True) 

                for tag_val in true_tag_vals:
                    tag = self._get_tag(tag_val)
                    parent_obj.linkAnnotation(tag)

if __name__ == "__main__":
    def establish_connection(server, port, user, password, secure, session_key):
        if session_key is not None:
            conn = gateway.BlitzGateway(host=server, port=port, sessionKey=session_key)
        else:
            conn = gateway.BlitzGateway(user, password, host=server, port=port, secure=secure)

        connected = conn.connect()

        if not connected:
            print('Connection to OMERO server failed. Please check your settings and try again.')
            sys.exit(1)

        return conn
    
    parser = argparse.ArgumentParser(
        description="A command-line interface for the OMERO tagging tool. This tool applies a set of tagging rules to an OMERO database, based on a given YAML file and patch script."
    )
    parser.add_argument(
        'tag_rules',
        #required=True, 
        type=str,
        help='Path to the YAML file containing the tagging rules to be applied.'
    )
    parser.add_argument(
        'patch',
        type=str,
        help='Path to the Python patch script to use for tagging.'
    )
    parser.add_argument(
        '-s', '--server', #host=wss://wsi.lavlab.mcw.edu/omero-wss
        #required=True,
        type=str,
        help='Address of the OMERO server to connect to.'
    )
    parser.add_argument(
        '-p', '--port', #port=443
        required=True,
        type=int,
        help='Port number of the OMERO server to connect to.'
    )
    parser.add_argument(
        '-u', '--user',
        type=str,
        help='Username for the OMERO server. This is required if no session key is provided.'
    )
    parser.add_argument(
        '-w', '--password',
        type=str,
        help='Password for the OMERO server. This is required if no session key is provided.'
    )
    parser.add_argument(
        '-S', '--secure',
        action='store_true',
        default=False,
        help='Whether to establish a secure connection to the server. If not specified, a secure connection is used to login and is switched over to unsecure by default.'
    )
    parser.add_argument(
        '--session',
        type=str,
        help='Session key to use for connecting to the server. If this is provided, username and password are not required.'
    )
    parser.add_argument(
        '--dry',
        action= 'store_true',
        help='Perform a dry run of the autotagger displaying what tags will be added/removed. Output will be sent to csv file'
    )

    args = parser.parse_args()

    # Check if user and password are provided if session is not provided
    if args.session is None and (args.user is None or args.password is None):
            args.user = os.getenv('OMERO_USER')
            args.password = os.getenv('OMERO_PASS')
            args.port = os.getenv('OMERO_PORT')
            args.server = os.getenv('OMERO_SERVER')
            if args.session is None and (args.user is None or args.password is None):
                parser.error("The options --user and --password are required if --session is not provided")

    # os.environ['OMERO_USER'] = 
    # os.environ['OMERO_PASS'] = 
    # os.environ['OMERO_SERVER'] = 
    # os.environ['OMERO_PORT'] = 

    # OMERO_PASS
    # OMERO_USER
    # OMERO_SERVER
    # OMERO_PORT = os.getenv('')
    # args.user = os.getenv('OMERO_USER')
    # args.password = os.getenv('OMERO_PASS')
    # args.port = os.getenv('OMERO_PORT')
    # args.server = os.getenv('OMERO_SERVER')

    if args.dry:
        dry_run = True
        print('This will be a dry run, the tags will not be committed. The output will be sent to a csv file.')
    else:
        dry_run = False

    # Load tag rules from the YAML file
    with open(args.tag_rules, 'r') as file:
        tag_rules = yaml.safe_load(file)

    conn = establish_connection(args.server, args.port, args.user, args.password, args.secure, args.session)

    tagger = OmeroTagger(conn, tag_rules, args.patch)
    tagger.apply_rules()  
    tagger.close()