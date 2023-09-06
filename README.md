#  🗺️ GeoScale — Open-source tools for client-independent IP addresses geolocation

GeoScale provides code for reproducing two IP addresses geolocation techniques using active measurements on

1. [Million Scale paper](https://dl.acm.org/doi/abs/10.1145/2398776.2398790?casa_token=8VDXwdGxNbAAAAAA:Aj5Sob6bUjhA0PX4fwtc_5uYZqFQv6iVRH8d_eoW98FA-fdjIJilue0NjZrMEcIimuAF9jeywJr_gQ): Internet scale geolocation technique, large dataset.

2. [Street level paper](https://www.usenix.org/legacy/event/nsdi11/tech/full_papers/Wang_Yong.pdf): Highly precise technique, on reduced dataset.

This project is part of a reproductibility publication, which aims to establish new baselines of these two methods, see: [reproductibility paper](). 

This repository offers the posibility to: 
- reproduce our results "offline" by using our own measurement datasets.
- run experiments on user defined set of targets and vantage points.

Note: Most measurement requires a [RIPE Atlas] account, the plateform we used to run our geolocation measurements.

⚠️ **Measurements on large datasets cost a lot of ressources**, be carefull when running any measurements.


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


### [Requirements](#requirements)

- [Python3.9](https://www.python.org/downloads/) (or above)
- [Poetry](https://python-poetry.org/docs/)
- [Clickhouse](https://clickhouse.com/docs/en/install) (optional for measurements?)

### [Install source files](#install-source-files)

Clone the repository:

```bash
git clone https://github.com/dioptra-io/geoloc-imc-2023.git
cd geoloc-imc-2023
```

GeoScale uses poetry has dependency manager, install the project using:
```bash
poetry shell
poetry lock
poetry install
```

### [RIPE Atlas credentials setup](#ripe-atlas-credentials-setup)

1. set these env variables within a .env file at the root directory of the projects:
```.env
RIPE_USERNAME=<your_username>
RIPE_SECRET_KEY=<your_secret_key>
```
2. Export directly with:
```bash
export RIPE_USERNAME=<your_username>
export RIPE_SECRET_KEY=<your_secret_key>
```

### Clickhouse

TODO: explain setup + insert results files + credentials.

### [Download datasets](#download-datasets)


As mentionned GeoScale can be used to reproduce our results. You can download our measurement using:

```bash
curl -? <some_url_towards_an_uninexting_ftp> # TODO: ftp arborescence
```


### [Further notice](#notice)

#### Test environement

All codes and scripts have been tested on: 
- CentOS (version)
- Coer?
- RAM?
- etc.

⚠️ Some scripts and analysis are heavy consumers, some lasting for hours potentially. Make sure that your configuration is sufficiently robust.

#### Windows

Furthermore, Linux is recommended but not mandatory.  
If you use Windows, you might have problems with the Windows path while using pyasn.  
You also have something to change in the section "Get population data" of create_datasets.ipynb.

## [Publication results analysis](#publication-results-analysis)


Option 2 : Only do the analysis
- analysis/million_scale.ipynb
- analysis/tables.ipynb
- plot/plot.ipynb

Move the measurement to the right directory

Finnally, you can run:
- this notebook for million scale results analysis
- this notebook for street level results analysis

Both notebooks provides results and figures.

TODO : setup processor used number when running some scripts.  


## [Run your own measurements](#run-your-own-measurements)

Option 1 : Do your own measurements
- datasets/create_datasets.ipynb
- measurements/anchor_measurements.ipynb
- measurements/probe_measurements.ipynb
- measurements/probe_and_anchor_measurements.ipynb
- measurements/landmark_traceroutes.ipynb

In that case, most of the data will be regenerated while the code is run eventhough you need few basic files.
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

