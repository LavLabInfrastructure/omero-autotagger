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