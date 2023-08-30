# geoloc-imc-2023
reproducement paper source code

# Omar code
## To run other server
* ensure that all precess stopped in both servers
* run split_servers() mutli_server_help.py script
* push all to repo
* pull locally
* delete every json in other server rm *.json
* get all json to local computer
* scp all json from computer to other server
* for the two above points and for pushing changes to the server use the script split_work.sh on local computer
* in test_v2.py change SERVER1_ANCHORS_FILE_PATH to SERVER2_ANCHORS_FILE_PATH
* in env_project.py comment the first line with IP_TO_ASN_FILE_PATH and uncomment the second

## To get result from other server
* run get_db_ids() and save res in MISSING_TRACEROUTES_IDS_FILE_PATH using the mutli_server_help.py script
* go to local machin and run fetch_results.sh
* go main server and run combine_results(), fill_db() and optinaly fill_negative_rtt() from multi_server_help.py
