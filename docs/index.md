# OMERO.AutoTagger

## Description
OMERO.AutoTagger is a utility that allows you to define a set of tagging rules in a YAML file. These rules are then used to traverse the OMERO object model. Each parent object (primarily images) and its children are checked to see if they match a set of parameters. If a match is found, the image is tagged with the corresponding tag name. A very common use case is tagging images based on the number of ROIs.

## Quick Links
-  Getting Started
    - [Installation](installation.md)
    - [Requirements](requirements.md)
- [Usage](usage.md)
- [Attribute-Based Tagging](attribute.md)
- [Capture-Based Tagging](capture.md)
- [Python Patch Script](patch.md)
