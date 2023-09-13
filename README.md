#  🗺️ Replication: Towards a Publicly Available Internet scale IP Geolocation Dataset (IMC 2023)
This repository contains the code needed to reproduce and replicate our results in our [IMC 2023 paper](). 

Our study replicates the methodology of two papers that obtained outstanding results on geolocating IP addresses in terms of coverage and accuracy in nowadays Internet on the largest publicly available measurement platform, RIPE Atlas. 
These two papers are: 

1. [Towards geolocation of millions of IP addresses (IMC 2012)](https://dl.acm.org/doi/abs/10.1145/2398776.2398790)

2. [Towards Street-Level Client-Independent IP Geolocation (NSDI 2011)](https://www.usenix.org/legacy/event/nsdi11/tech/full_papers/Wang_Yong.pdf).

They are called million scale and street level papers throughout this README, as done in our paper. 

Our code offers the possibility to: 
1. reproduce our results using our measurement datasets.
2. replicate our methodology with different targets and vantage points. For now, only RIPE Atlas vantage points are supported, but it should not be difficult to adapt the code to handle other vantage points and targets. 

## Prerequisites
Our code performs measurements on RIPE Atlas, so be sure to have an account if you want to replicate our methodology with your own RIPE Atlas measurements.

⚠️ **To replicate our RIPE Atlas measurements, you will need a lot of credits (millions)**. 


## Table of contents

- [Installation](#installation)
  - [Requirements](#requirements)
  - [Download datasets](#download-datasets)
  - [Clone the repository](#clone-the-repository)
  - [Installer](#installer)
  - [Install source files](#install-source-files)
  - [Clickhouse](#clickhouse)
  - [Settings](#settings)
  - [Further notice](#further-notice)
- [Reproduction](#reproduction)
- [Run your own measurements](#run-your-own-measurements)

## [Installation](#installation)

### [Requirements](#requirements)

- [Python3.9](https://www.python.org/downloads/) (or above)
- [Poetry](https://python-poetry.org/docs/)
- [Docker](https://docs.docker.com/engine/install/)


### [Download datasets](#download-datasets)

To reproduce our experiences analysis, you can download all necessary files with:
```bash
curl -? <some_url_towards_ftp> # TODO: ftp arborescence
# all files necessary are located in /srv/hugo/geoloc-imc-2023
```
TODO: explain which files are being downloaded (their purpose) and where to set them.

### [Clone the reprository](#clone-the-repository)

```bash
git clone https://github.com/dioptra-io/geoloc-imc-2023.git
cd geoloc-imc-2023
```

### [Installer](#installer)

You can use the script **install.sh** to:
- Pull the clickhouse docker image.
- Start the clickhouse server.
- Download clickhouse-client binary.
- Install python project using poetry.
- Create all tables and populate the database with our measurements.

```bash
source install.sh
```
If the installation fails, all necessary steps to use the project are described below.

### [Install source files](#install-source-files)

GeoScale uses poetry has dependency manager, install the project using:
```bash
poetry shell
poetry lock
poetry install
```

### [Clickhouse](#clickhouse)

We use docker to run clickhouse server, by default server is listening on localhost on port 8123 and tcp9000. If you prefer using your own docker configuration, please also modify [default.py](default.py)
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

You can either install [clickhouse-client](https://clickhouse.com/docs/en/install) or download clikhouse client binary (by default, [install.sh](install.sh) download binary file).
```bash
curl https://clickhouse.com/ | sh
mv clickhouse ./clickhouse_files/
```

Finally, create all necessary tables and populate it with our own measurements with:
```bash
python scripts/utils/clickhouse_installer.py 
```


### [Setttings](#settings)

Our tool relies on ENV variables for configuring clickhouse or interacting with RIPE Atlas API.
An example of necessary ENV variables is given in [.env.example](.env.example). Create your own
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

#### Test environment

The project has been run on:
- CentOS 7.5
- Python 3.9
- Server with 64GB RAM, 32 cores.
  
⚠️ Some scripts and analysis can use a lot of CPU and RAM (tens of GB) and last for hours.


## [Reproducing our results](#reproduction)

We provide python scripts and jupyter notebooks to reproduce the results and the graphs that we got in replicating the million scale and the street level papers.

### Million Scale

You can reproduce Million scale results using a jupyter notebook: [million_scale.ipynb](./analysis/million_scale.ipynb)

Alternatively you can also use the python script in background, as some steps are vey long to execute (several hours):
```bash
nohup python analysis/million_scale.py > output.log &
```

All analysis results can be found in **./analysis/results**

### Street level

⚠️ The tier 1 of the Street-level replication (See the paper for more details) relies on results calculated by the million scale technique. You need to run the million scale notebook/scripts **before** running those of street-level. 

No additional steps are necessary to reproduce the street-level experiment.

### Generating figures

You can directly use notebooks [plot.ipynb](./analysis/plot.ipynb) and [tables.ipynb](./analysis/tables.ipynb) to produce the figures and tables of our paper. 
 
## [Run your own measurements](#run-your-own-measurements)

You can also run your own measurements on custom datasets of targets (anchors) and vantage points (probes).

### First step: generate targets and vantage points datasets

The jupyter notebook [create_dataset](./datasets/create_datasets.ipynb) will generate:
- the set of probes (used as vantage points)
- the set of anchors (used as targets)
- filter both sets by removing problematic probes (wrongly geolocated for example)

All generated files will be placed in /datasets/user_datasets.

### Second step: run measurements

With [million_scale_measurements.ipynb](./measurements/million_scale_measurements.ipynb), you can select a subset of vantage points and targets and run measurements on RIPE Atlas.

This script will start measurements for:
  1. towards all targets from all vantage points
  2. towards 3 responsive addresses for each target from all vantage points

⚠️ These measurements might cost a lot of RIPE Atlas credits and time if you run them on large datasets (default is only 2 targets and 4 vantage points).

### Third step: analyze your results

Perform the analysis by using the same step described previously on your own measurements results and datasets by setting the boolean variable ```repro = True```, at the beginning of [million_scale.ipynb](./analysis/million_scale.ipynb) (or [million_scale.py](./analysis/million_scale.py) if you are using the script).



TODO: Street level

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

