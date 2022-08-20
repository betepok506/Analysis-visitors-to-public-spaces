FROM postgres
COPY sql/park.sql /docker-entrypoint-initdb.d/