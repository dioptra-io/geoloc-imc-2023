#  🗺️ GeoScale — Towards a Publicly Available Internet scale IP Geolocation Dataset: a Replication Study
GeoScale provides code for reproducing two IP addresses geolocation techniques using active measurements on

1. [Million Scale paper](https://dl.acm.org/doi/abs/10.1145/2398776.2398790?casa_token=8VDXwdGxNbAAAAAA:Aj5Sob6bUjhA0PX4fwtc_5uYZqFQv6iVRH8d_eoW98FA-fdjIJilue0NjZrMEcIimuAF9jeywJr_gQ): Internet scale geolocation technique, large dataset.

2. [Street level paper](https://www.usenix.org/legacy/event/nsdi11/tech/full_papers/Wang_Yong.pdf): Highly precise technique, on reduced dataset.

This project is part of a reproducibility publication, which aims to establish new baselines of these two methods, see: [reproductibility paper](). 

This repository offers the possibility to: 
- reproduce our results "offline" by using our own measurement datasets.
- run experiments on user defined set of targets and vantage points.

Note: Most measurement requires a [RIPE Atlas] account, the platform we used to run our geolocation measurements.

⚠️ **Measurements on large datasets cost a lot of resources**, be careful when running any measurements.


## Table of contents

- [Installation](#installation)
  - [Requirements](#requirements)
  - [Install source files](#install-source-files)
  - [RIPE Atlas credentials setup](#ripe-atlas-credentials-setup)
  - [Clickhouse](#clickhouse)
  - [Download datasets](#download-datasets)
  - [Further notice](#further-notice)
- [Publication results analysis](#publication-results-analysis)
- [Run your own measurements](#run-your-own-measurements)

## [Installation](#installation)

### [Download datasets](#download-datasets)

To reproduce our experiences analysis, you can download all necessary files with:
```bash
curl -? <some_url_towards_an_uninexting_ftp> # TODO: ftp arborescence
```
TODO: explain which files are being downloaded (their purpose) and where to set them.

### [Requirements](#requirements)

- [Python3.9](https://www.python.org/downloads/) (or above)
- [Poetry](https://python-poetry.org/docs/)
- [Docker](https://docs.docker.com/engine/install/)

### [Clone the reprository](#clone_the_reprository)

```bash
git clone https://github.com/dioptra-io/geoloc-imc-2023.git
cd geoloc-imc-2023
```

### [Installer](#installer)

You can use the script **install.sh** to:
- Pull the clickhouse docker image.
- Start the clickhouse server.
- Install python project using poetry.
- Create all tables and populate the database with our measurements.

```bash
source install.sh
```
If the installation fails, all necessary steps to use geoScale are described below.

### [Install source files](#install-source-files)

GeoScale uses poetry has dependency manager, install the project using:
```bash
poetry shell
poetry lock
poetry install
```

### [Clickhouse](#clickhouse)

We use docker to run clickhouse server, by default server is listening on localhost on port 8123 and tcp9000. If you prefer using your own docker configuration, please also modify [default.py](#)
```bash

# pull the docker image
docker pull clickhouse/clickhouse-server:22.6

# start the server
docker run --rm -d \
    -v ./clickhouse_files/data:/var/lib/clickhouse/ \
    -v ./clickhouse_files/logs:/var/log/clickhouse-server/ \
    -v ./clickhouse_files/users.d:/etc/clickhouse-server/users.d:ro \
    -v ./clickhouse_files/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh \
    -p 8123:8123 \
    -p 9000:9000 \
    --ulimit nofile=262144:262144 \
    clickhouse/clickhouse-server:22.6
```

You can either install [clickhouse-client](#https://clickhouse.com/docs/en/install) or download clikhouse client binary (by default, [install.sh](#) download binary file).
```bash
curl https://clickhouse.com/ | sh
mv clickhouse ./clickhouse_files/
```

Finally, create all necessary tables and populate it with our own measurements with:
```bash
python scripts/utils/clickhouse_installer.py 
```


### [Setttings](#settings)

Our tool relies on ENV variables for configuring Clickhouse or interracting with RIPE Atlas API.
An example of necessary ENV variables is given in [.env.example](#). Create your own
env file with following values:
```.env
RIPE_USERNAME=
RIPE_SECRET_KEY=
```

⚠️ **IF** you used, your own clickhouse configuration, you can modify the following ENV:
```
# clickhouse settings
CLICKHOUSE_CLIENT=
CLICKHOUSE_HOST=
CLICKHOUSE_DB=
CLICKHOUSE_USER=
CLICKHOUSE_PASSWORD=
```
### [Further notice](#notice)

#### Test environement

The project has been tested on:
- CentOS v.X.X.X
- MacOs vY.Y.Y
- Ubuntu?


⚠️ Some scripts and analysis are heavy consumers, some lasting for hours. Make sure that your configuration is sufficiently robust.


## [Reproduction](#publication-results-analysis)

You can reproduce our experimentation with the two notebooks in /analysis:
- [anaysis/million_scale.ipynb](#)
- [analysis/street_level.ipynb](#)

Both notebooks will generate all result files necessary for producing all the
figures published in the paper. You can plot them by running the jupyter notebook:
- [plot/plot.ipynb](#)

Finally, tables can be generated using jupyter notebook:
- [tables/tables.ipynb](#)


## [Run your own measurements](#run-your-own-measurements)

TODO:

Option 1 : Do your own measurements
- datasets/create_datasets.ipynb
- measurements/anchor_measurements.ipynb
- measurements/probe_measurements.ipynb
- measurements/probe_and_anchor_measurements.ipynb
- measurements/landmark_traceroutes.ipynb

In that case, most of the data will be regenerated while the code is run even though you need few basic files.
After cloning the repository, unzip the (TROUVER UN NOM 2) folder (ET DIRE OU IL SE TROUVE). It contains 2 subfolders.
- geography -> cities? to remove? 
- various -> various what?
Move these two folders into the dataset folder.

## 📚 Publications

```bibtex
@inproceedings{UponValidation,
  title={Towards a Publicly Available Internet scale IP
  Geolocation Dataset: a Replication Study},
  author={Darwich, Rimlinger, Dreyfus, Gouel, Vermeulen},
  booktitle={Proceedings of the 2023 Internet Measurement Conference},
  pages={404--404},
  year={2023}
}
```


## 🧑‍💻 Authors

This project is the result of a collaboration between the [LAAS-CNRS](https://www.laas.fr/public/) and [Sorbonne Université](https://www.sorbonne-universite.fr/).

