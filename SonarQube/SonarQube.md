## SonarQube (Local Static Analysis)

This repo includes a local SonarQube setup (Docker) plus a ready-to-use [sonar-project.properties](sonar-project.properties).

### 1) Start SonarQube

Then start the services:

```bash
docker compose -f docker-compose.sonarqube.yml up -d
```

Open http://localhost:9000 and log in with:

- Username: `admin`
- Password: `admin`

You'll be prompted to change the password.

### 2) Create a project token

In SonarQube:

- Create (or import) a project named
- Create a user token (Profile → My Account → Security)

### 3) Run a scan for this repo

Use the official scanner container (no local install needed):

```bash
export SONAR_TOKEN="<paste-token-here>"
docker run --rm --network host \
  -e SONAR_TOKEN="$SONAR_TOKEN" \
  -v "$PWD:/usr/src" \
  sonarsource/sonar-scanner-cli:latest \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.token="$SONAR_TOKEN"
```

Then refresh the project in the SonarQube UI to see results.

Optional (coverage): if you generate `coverage.xml` (Python) and/or `lcov.info` (frontend), uncomment the coverage paths in [sonar-project.properties](sonar-project.properties).
