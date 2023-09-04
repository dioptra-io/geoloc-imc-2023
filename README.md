# Towards a Publicly Available Internet scale IP Geolocation Dataset: a Replication Study

## Introduction

A faire

## How to use ?

The concept of this repository is to run several notebooks to (petit à petit) reconstitute the results of the replication paper.  

Two options are available : you can either use our datasets and results and verify them, or do your own measurements and then check if you have something similar with the paper.  

First clone the repo, make sure you have the good configuration (see just below) and run the notebooks in the following order.  

Option 1 : Do your own measurements
- datasets/create_datasets.ipynb
- measurements/anchor_measurements.ipynb
- measurements/probe_measurements.ipynb
- measurements/probe_and_anchor_measurements.ipynb
- measurements/landmark_traceroutes.ipynb

Option 2 : Only do the analysis
- analysis/million_scale.ipynb
- analysis/tables.ipynb
- plot/plot.ipynb

## Configuration

We used several tools for this project. All the prerequisites you need to run the code are explained in this section.

### Poetry

A faire

### Clickhouse

A faire

### Datasets

Some other online datasets are required. They have been downloaded and are grouped in a zip format.  

#### Option 1 : Use all our datasets.
After cloning the repository, unzip the (TROUVER UN NOM) folder (ET DIRE OU IL EST DISPONIBLE). It contains 4 subfolders :
- analysis_results. Rename the folder as only "results" and move it into the analysis folder.
- datasets. To move directly in the original repository.
- measurements_results. Rename the folder as only "results" and move it into the measurements folder.
- pdf. It contains all the pdf of the paper. You are supposed to get exactmy the same while running the code.

#### Option 2 : Recreate your own datasets.
In that case, most of the data will be regenerated while the code is run eventhough you need few basic files.
After cloning the repository, unzip the (TROUVER UN NOM 2) folder (ET DIRE OU IL SE TROUVE). It contains 2 subfolders.
- geography
- various
Move these two folders into the dataset folder.

### RIPE ATLAS account

Targets and vantage points used in this project are provided by RIPE ATLAS. They can be gotten using RIPE ATLAS API (LIEN).  

WARNING (WARNING) As explained in the paper, you need RIPE ATLAS account and credits to do some measurements.  
The total number of credits used in this project is significant and you may not be able to do as much measurements as us.  
Please consider this issue before doing your own measurements.  

Once you have an account, you have to indicate your credentials in the default.py file.

### Golbal configuration

Some of the algorithms are quite heavy, computationnal, and time consumming. There is an indication for each algorithm that needs from several dozens of minutes to several hours to run.  

The machine used by our team has the following (charactéristiques):
- INDIQUER LES TRUCS DE VENUS
Make sure you have enough (RAM and computationnal power) before running the code.  
Sometimes, we use multiprocessing with the Pool() method. Depending on your computer, you might like changing the number of processor used.  

Furthermore, Linux is recommended but not mandatory.  
If you use Windows, you might have problems with the Windows path while using pyasn.  
You also have something to change in the section "Get population data" of create_datasets.ipynb.