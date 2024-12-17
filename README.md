# OMERO.AutoTagger

## Description
OMERO.AutoTagger is a utility that allows you to define a set of tagging rules in a YAML file. These rules are then used to traverse the OMERO object model. Each parent object (primarily images) and its children are checked to see if they match a set of parameters. If a match is found, the image is tagged with the corresponding tag name. A very common use case is tagging images based on the number of ROIs.

## Requirements
- Python 3.8 or above
- Python packages: `pyyaml`, `inflect`, `omero-py`

These dependencies can be installed via pip:
```sh
pip3 install omero-py PyYAML inflect
```
zeroc-ice, an omero-py dependency, is troublesome on apple silicon, installing our lavlab-python-utils package streamlines the installation process
```sh
python3 -m pip install https://github.com/laviolette-lab/lavlab-python-utils/releases/latest/download/lavlab_python_utils-latest-py3-none-any.whl
python3 -m pip install 'lavlab-python-utils[all]'
python3 -m pip install inflect
```

## Usage

1. Define your tag rules in a YAML file. See the provided example file for the required structure and syntax.

2. Run the script from the command line using the following syntax:
### From Install: (pypi coming soon)
```
python3 -m omero_autotagger <path to tag_rules.yml> [path to patch.py] -s <server> -p <port> -u [user] -w [password] -S [secure] --session [session_key]
```
### From Source:
```
python3 src/omero_autotagger <path to tag_rules.yml> [path to patch.py] -s <server> -p <port> -u [user] -w [password] -S [secure] --session [session_key]
```

Here is a brief explanation of each argument:

- `tag_rules.yml`: Required. Path to the YAML file containing the tagging rules to be applied.
- `patch.py`: Path to the Python patch script to use for tagging.
- `server`: Required. Address of the OMERO server to connect to.
- `port`: Required. Port number of the OMERO server to connect to.
    * With the increased adoption of OMERO API over websockets, we decided to make this required, may be assumed in future updates.
- `user`: Username for the OMERO server. This is required if no session key is provided.
- `password`: Password for the OMERO server. This is required if no session key is provided.
- `secure`: Establishes a secure connection to the server. If not specified, a secure connection is used to login and then switched to unsecure by default.
- `session`: Session key to use for connecting to the server. If this is provided, username and password will be ignored.

## Example Usage

Given a YAML file `tag_rules.yaml` and patch script `patch.py`:

```
python3 -m omero_autotagger rules.yml patch.py -s myserver.com -p 4064 -u myuser -w mypassword
```

Or using a session key:

```
python3 -m omero_autotagger rules.yml patch.py -s myserver.com -p 4064 --session mysesskey
```

This will establish a connection to the specified OMERO server, load the tagging rules from the provided YAML file, apply these rules using the provided patch script (if any), and tag the images accordingly.

## YAML Rules Structure for Capture Based Tagging

For capture-based tagging, your YAML file can include rule sets that define the following parameters:

- `capture`: A string that specifies a regular expression (Python flavor). This expression is used to capture specific groups of text from object names, which will then be used as tags. For instance, `([^_.]+)` will capture all underscore-delimited groups from names and tag them separately.

- `include_extension`: An optional boolean value. If set to `True`, the file extension will be included in the capture process. If set to `False`, or omitted, the extension will be trimmed before applying the regex.

- `object`: An optional string that specifies the type of the object to tag. If omitted, the default object type is 'Image'.

- `format`: An optional string that serves as a Python format template. It's used for formatting the captured group before tagging. If omitted, the default is no formatting.

- `blacklist`: An optional list of string values. If a captured value matches any value in the blacklist, it will not be used as a tag.

Here is an example:

```yaml
- capture: "([^_.]+)"
  include_extension: False
  object: 'image'
  format: '{}'
  blacklist:
    - Large
    - Deeper
    - Deeper2
    - Deeper3
    - Deeper4  
```

In this example, any text that is separated by underscores or periods in the names of image files will be captured and used as a tag, except for the terms listed in the blacklist.

## YAML Rules Structure for Attribute Based Tagging

For attribute-based tagging, your YAML file can include rule sets that define the following parameters:

- `name`: A string that specifies the name of the tag to apply.

- `absolute`: An optional boolean value. If set to `True`, the tag will be unset if the rules are not fulfilled. If omitted, the default is `True`.

- `rules`: A list of dictionaries, where each dictionary includes the following keys:

    - `attribute_path`: A list of strings that specifies the hierarchical path to the attribute that should be checked.
    
    - `operation`: A string that specifies the comparison operation to use. It can be one of the following: eq (equal), ne (not equal), gt (greater than), ge (greater than or equal), lt (less than), le (less than or equal), or match (regex match).
    
    - `value`: Specifies the value to compare the attribute value against. It can be any data type that is appropriate for the operation being performed.

Here is an example:

```yaml
- name: Annotate 
  absolute: True
  rules:
    - attribute_path: ["image","roicount"]
      operation: lt
      value: 1
```

In this example, the tag `Annotate` will be applied to any image that has a "roiCount" of 0. If the image's "roi count" is more than 1, the tag `Annotate` will be removed (since `absolute` is `True`). While generated collection attributes may be useful, the logic has not been implemented. instead patch your desired parent object to have a getter for that attribute. (see below)
## Python Patch Script

The `patch.py` file should be a Python script that contains definitions for custom methods. These methods are intended to be added to OMERO gateway wrapper classes to extend their functionality. This is commonly known as "monkey patching".

Here's a basic outline of how you can structure your `patch.py`:

```python
def getROIs(self):
    # This is just a placeholder. Replace the code here with whatever functionality.
    pass

def getOtherAttributes(self):
    # Another placeholder function. Add your code here.
    pass

# Assign the new methods to the relevant OMERO classes
import omero.gateway
omero.gateway.ImageWrapper.getROIs = getROIs
omero.gateway.ImageWrapper.getOtherAttributes = getOtherAttributes
```

In the script above, we define two methods: `getROIs()` and `getOtherAttributes()`. Each of these methods should only accept `self` as a parameter, meaning they are instance methods.

We then assign these methods to the `ImageWrapper` class of the `omero.gateway` module, thereby extending the functionality of this class. When instances of this class are used within the OMERO.AutoTagger application, they will now have access to these additional methods.

Ensure your patch script is tailored to your requirements and correctly interfaces with the existing OMERO objects you are working with.
