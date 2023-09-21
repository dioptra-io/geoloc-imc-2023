# pull the docker image
docker pull clickhouse/clickhouse-server:22.6


# start the server using docker
docker run --rm -d \
    -v ./clickhouse_files/data:/var/lib/clickhouse/ \
    -v ./clickhouse_files/logs:/var/log/clickhouse-server/ \
    -v ./clickhouse_files/users.d:/etc/clickhouse-server/users.d:ro \
    -v ./clickhouse_files/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh \
    -p 8123:8123 \
    -p 9000:9000 \
    --ulimit nofile=262144:262144 \
    clickhouse/clickhouse-server:22.6

# download clickhouse client binary
curl https://clickhouse.com/ | sh
mv clickhouse ./clickhouse_files/

# install source files
poetry lock 
poetry install

# run clickhouse db installer for table init
poetry run python scripts/utils/clickhouse_installer.py
