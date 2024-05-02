<div align="center">
  <div>
  
  <a href="https://syyclops.com">
    <p align="center">
      <img height=65 src="./docs/assets/logo192.png"/>
    </p>
  </a>

</div>

<h3>

[Documentation](/docs/)

</h3>

[![Tests](https://github.com/syyclops/open-operator/actions/workflows/test.yml/badge.svg)](https://github.com/syyclops/open-operator/actions/workflows/test.yml)

</div>

## What is Brontes

Brontes is open source infrastructure for managing digital twins of facilites and their complex systems.

## What is a digital twin?

"a personalized, dynamically evolving model of a physical system." [Karen Willcox](https://www.youtube.com/watch?v=r2_VWdjxchY&t=40s&ab_channel=TED)

Digital twins come from combining data from a real world asset (eg. sensors, maintenance logs) with models grounded in physics to create a simulator that represents the asset.

## Levels of Digital Twin

1. Descriptive - Virtual Replica of assets. (BIM modeling)
2. Informative - Integrations with sensors, IT, and business software. Insights into basic conditions and performance.
3. Predictive - Advanced analytics, identity patterns and provide early warnings before they happen. Smart building schedules. (predict when a space will need to be heated or cooled)
4. Comprehensive - Physics based modeling, what if scenarios, prescriptive analytics.
5. Autonomous – Ability to take actions and fix issues autonomously.

## Demo

https://github.com/syyclops/brontes/assets/70538060/591f94ec-cd20-4ba5-8dd3-72e4319fb6ba

## Project Structure

```
- brontes/
  - application/
    - api/                      # Manages API endpoints
    - services/                 # Application services: handle user input, validate data, and interact with domain + infrastructure layers
    - dtos/                     # Data transfer objects
  - domain/
    - models/                   # Entities and value objects
    - services/                 # Domain services: business rules, calculations, or other logic spanning across multiple domain entities
  - infrastructure/
    - repos/                    # Data fetching + persistence
    - db/                       # Database connections + configs
    - external/                 # API or other integrations
- tests/
  - integration/                # Integration tests
  - unit/                       # Unit tests
```

The project aims to follow Domain Drive Design (DDD). To learn more, here are some resources:

["Domain-Driven Design: Tackling Complexity in the Heart of Software"](https://fabiofumarola.github.io/nosql/readingMaterial/Evans03.pdf) by Eric Evans <br>
[Domain Driven Design and Python: David Seddon](https://www.youtube.com/watch?v=4XKhH9whNX0&list=WL&index=1&ab_channel=PyConUK)

## Quickstart

### Prerequisites

1. [Install Docker](https://docs.docker.com/engine/install/)

2. ```sh
   # Install poetry
   curl -sSL https://install.python-poetry.org | python3 -
   ```

### Install brontes

```sh
git clone https://github.com/syyclops/brontes.git --config core.autocrlf=false # Config makes sure LF formatting is used in the .sh scripts so they run properly in docker containers
cd brontes
poetry install
```

_To make poetry create a virtualenv in the project: `poetry config virtualenvs.in-project true`_

### Set the required environment variables

_Use .env.example file as a starting point_

```sh
cp .env.example .env
export OPENAI_API_KEY=<your secret key>
export AZURE_STORAGE_CONNECTION_STRING=<your azure storage container>
export AZURE_CONTAINER_NAME=<your azure container name>
export API_TOKEN_SECRET=<your api secret key>
```

### Build and start the docker containers

_This will start postgres, neo4j, unstructured, and the brontes api server_

```sh
docker compose up -d --build
```

### View the [swagger docs](http://localhost:8080/docs)

## Testing

- **[Unit Tests](./tests/unit/)**

- **[Integration Tests](./tests/integration/)**

  We are using [testcontainers](https://testcontainers.com/) for integration tests. When running locally we need to build some images that will be used:

  1. Neo4j with apoc and neosemantics plugins: `docker build -f Dockerfile.neo4j -t neo4j_with_plugins .`
  2. Postgres with timescaledb and vector extensions: `docker build -f Dockerfile.pg -t pg .`

- End-to-End: TBD

Run all tests: `pytest`

## Useful Resources

1. [COBieOWL_CameraReady_VE.pdf](https://github.com/syyclops/brontes/files/15070251/COBieOWL_CameraReady_VE.pdf)
2. [What is COBie?](https://www.thenbs.com/knowledge/what-is-cobie)
3. [Brick Schema](https://brickschema.org/)
4. [Data-Driven Smart Buildings: State-of-the-Art Review](https://github.com/syyclops/open-operator/files/14202864/Annex.81.State-of-the-Art.Report.final.pdf)
