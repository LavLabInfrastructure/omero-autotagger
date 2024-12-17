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
