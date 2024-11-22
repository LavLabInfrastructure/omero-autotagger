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