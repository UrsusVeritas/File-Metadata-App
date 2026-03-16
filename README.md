# File Metadata App – DevOps Portfolio Project

A DevOps portfolio project demonstrating an end-to-end CI/CD pipeline on AWS.
The application logic is intentionally simple — the focus is the DevOps workflow.

## Architecture

```
Developer → Jenkins → Docker Build → ECR → ECS Fargate → Services
                           |
                    Terraform (IaC)
                           |
                    VPC / IAM / ECR
```

**Services:**
- `uploader-api` — accepts file uploads, stores them in S3
- `metadata-service` — extracts and returns file metadata (name, size, type, timestamp)
- `browser-api` — lists files stored in an S3 bucket

## DevOps Skills Demonstrated

- CI/CD pipeline with Jenkins (containerized test runner, multi-stage pipeline)
- Docker image builds with multi-stage Dockerfiles and `.dockerignore`
- Pushing container images to Amazon ECR
- Deploying containerized services to Amazon ECS Fargate
- Infrastructure provisioning with Terraform (VPC, subnets, IAM, EC2)
- Terraform validation (fmt + validate) as part of CI
- Scoped IAM roles — Jenkins has only the permissions it needs (no AdministratorAccess)
- IMDSv2 enforced on the Jenkins EC2 instance
- Smoke tests run automatically after each deployment
- Secure AWS access via IAM instance profile — no hardcoded credentials

## Prerequisites

- AWS account with permissions to create VPC, EC2, ECR, ECS, IAM, S3, DynamoDB
- Terraform >= 1.5
- AWS CLI v2
- Docker
- An existing EC2 key pair named `jenkins-ssh-key-for-devops` (or update `jenkins.tf`)
- S3 bucket + DynamoDB table for Terraform state (see `infra/backend.tf`)

## Getting Started

### 1. Clone the repository

```bash
git clone <repo-url>
cd file-devops-project
```

### 2. Configure Terraform

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars — set allowed_cidr to your IP (find it at https://checkip.amazonaws.com/)
```

### 3. Provision infrastructure

```bash
terraform init
terraform plan
terraform apply
```

### 4. Configure Jenkins

After `terraform apply`, copy the public IP of the Jenkins EC2 instance and open:

```
http://<jenkins-ip>:8080
```

Follow the Jenkins setup wizard. Install the suggested plugins plus:
- Docker Pipeline
- AnsiColor

### 5. Run the pipeline

Create a new Pipeline job in Jenkins pointing to this repository. On first run, set the parameters:

| Parameter | Example |
|---|---|
| `AWS_ACCOUNT_ID` | `123456789012` |
| `AWS_REGION` | `us-east-1` |
| `ECR_REPO_UPLOADER` | `file-metadata-uploader-api` |
| `ECR_REPO_METADATA` | `file-metadata-metadata-service` |
| `ECR_REPO_BROWSER` | `file-metadata-browser-api` |
| `ECS_CLUSTER_NAME` | `file-metadata-cluster` |

### 6. Local development

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| uploader-api | http://localhost:5003 |
| metadata-service | http://localhost:5001 |
| browser-api | http://localhost:5002 |

Stop:

```bash
docker compose down
```

## CI/CD Pipeline Stages

| Stage | Description |
|---|---|
| Preflight | Verifies Docker, AWS CLI, Terraform are available |
| Checkout | Pulls source from SCM |
| Compute Build Vars | Sets `IMAGE_TAG` from short Git SHA |
| Unit Tests | Runs tests in `python:3.11-slim` container |
| Terraform fmt & validate | Checks IaC formatting and syntax |
| ECR Login + Ensure repos | Authenticates and creates ECR repos if missing |
| Build & Push Images | Builds Docker images, pushes with SHA tag + `latest` |
| Deploy to ECS | Force-deploys all three services, waits for stability |
| Smoke Tests | Curls `/health` on each service (when URLs configured) |

Images are tagged with both the short Git SHA and `latest` for traceability and easy rollback.

## Cleanup

Destroy all AWS resources to avoid charges:

```bash
cd infra
terraform destroy
```

**Estimated cost while running:** ~$5–10/day (t3.medium EC2 + NAT Gateway + ECS tasks).
Destroy when not in use.

## Project Status

Learning and portfolio project. Not designed for production use.

**Author:** Bogdan Poliiektov
