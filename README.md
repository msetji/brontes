<div align="center">
  <div>
  <a href="https://syyclops.com">
    <p align="center">
      <img height=150 src="./docs/assets/logo192.png"/>
    </p>
  </a>
</div>

<h3>

[Documentation](/docs/)

</h3>

[![Tests](https://github.com/syyclops/open-operator/actions/workflows/test.yml/badge.svg)](https://github.com/syyclops/open-operator/actions/workflows/test.yml)

</div>

---

**Brontes** is a platform to bring buildings to life. It organizes and makes sense of diverse building information.

- Organize and correlate all data sources from the building
- Talk to your building like its a person
- Your building can reach out to you when things might be going wrong

## Demo

_Example chat with a building. [See code here](./scripts/chat.py)_

https://github.com/syyclops/open-operator/assets/70538060/e9a833bd-b1e5-4a81-aef5-083f8b163144

## Project Structure

The project is organized within a single base directory named brontes/, which contains all the components of the project:

- **application/**: Manages API endpoints, orchestrating the flow between the user and domain logic.
- **domain/**: The core layer where business logic lives. It includes:
  - **model/**: Defines the business entities and their behaviors.
  - **repository/**: Interfaces for data access and manipulation.
  - **service/**: Contains business operations and logic.
- **infrastructure/**: Supports the application with database access, external API communication, and other technical capabilities.

The project aims to adhere to Domain Drive Design (DDD) principles as closely as possible, structuring the codebase to mirror real-world business scenarios and ensuring it remains aligned with business goals.

To learn more about DDD and its benefits, here are some resources:

["Domain-Driven Design: Tackling Complexity in the Heart of Software"](https://fabiofumarola.github.io/nosql/readingMaterial/Evans03.pdf) by Eric Evans <br>
["Implementing Domain-Driven Design"](https://dl.ebooksworld.ir/motoman/AW.Implementing.Domain-Driven.Design.www.EBooksWorld.ir.pdf) by Vaughn Vernon

## Quickstart

### Prerequisites

1. [Install Docker](https://docs.docker.com/engine/install/)

2. ```sh
   # Install poetry
   curl -sSL https://install.python-poetry.org | python3 -
   ```

### Install brontes

```sh
# Clone the repo and navigate into the brontes directory
git clone https://github.com/syyclops/brontes.git
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

- **[Unit Tests](./tests/unit/)**: Focus on parts of the applicaiton in isolation, primarily domain models and services. These test buisness rules, model validation, and behaviors of services without external dependencies

- **[Integration Tests](./tests/integration/)**: To ensure that various parts of the system work together as expected

  We are using [testcontainers](https://testcontainers.com/) for integration tests. When running locally we need to build some images that will be used:

  1. Neo4j with apoc and neosemantics plugins: `docker build -f Dockerfile.neo4j -t neo4j_with_plugins .`
  2. Postgres with timescaledb and vector extensions: `docker build -f Dockerfile.pg -t pg .`

- End-to-End: TBD

Run all tests: `pytest`

## Useful Resources

1. [What is COBie?](https://www.thenbs.com/knowledge/what-is-cobie)
2. [Brick Schema](https://brickschema.org/)
3. [Data-Driven Smart Buildings: State-of-the-Art Review](https://github.com/syyclops/open-operator/files/14202864/Annex.81.State-of-the-Art.Report.final.pdf)
