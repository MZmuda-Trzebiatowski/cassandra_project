# Cassandra Project
## Maksymilian Żmuda-Trzebiatowski 156 051
### Description:
Cassandra Project is a project that uses docker to simulate a distributed Cassandra file system. Then there is a CLI that can be used regularely or run stress tests.
### How to run:
* download the project from the Github rpo
* in the project directory run `docker compose up --build`
* wait for the nodes to fully start, you can check if they started by running: `docker exec -it cassandra-node1 nodetool status`, there should be two nodes up
* run `docker exec -it app-node1 bash` and inside that docker run `python cli.py`
* to shut down exit the program and run `docker-compose down -v --remove-orphans`
