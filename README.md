# File Metadata App – DevOps Portfolio Project

This repository is a DevOps portfolio project created to demonstrate basic and practical DevOps skills: CI/CD automation, Docker, AWS (ECS and ECR), and Infrastructure as Code using Terraform.

The application logic is intentionally simple. The main focus of this project is the DevOps workflow rather than application complexity.


Developer
   |
   v
 Jenkins
   |
   +--> Docker Build
   |
   +--> ECR
   |
   +--> ECS Fargate
   |
   +--> Services (uploader / metadata / browser)


DevOps skills demonstrated in this project:
- CI/CD pipeline implemented with Jenkins
- Docker image build and containerization
- Pushing container images to Amazon ECR
- Deploying containerized services to Amazon ECS Fargate
- Infrastructure provisioning and management with Terraform
- Terraform code validation (fmt and validate) as part of CI
- Secure AWS access using IAM roles without hardcoded credentials
- Cost awareness through full infrastructure teardown capability

Local development:
The application can be started locally using Docker Compose.

docker compose up --build

To stop the application:

docker compose down

CI/CD pipeline overview:
The Jenkins pipeline performs the following actions:
- verifies required tools on the Jenkins agent
- checks out the source code
- runs unit tests in a containerized environment
- validates Terraform configuration
- builds Docker images
- pushes images to Amazon ECR
- triggers a new deployment on Amazon ECS
- waits for services to become stable

Docker images are tagged with both the short Git commit SHA and the "latest" tag to allow traceability and easy rollbacks.

Infrastructure:
Terraform is used to manage all AWS infrastructure required for this project, including ECS services, ECR repositories, IAM roles, and supporting resources.

Cleanup:
All AWS resources can be destroyed to avoid unnecessary costs by running:

cd infra
terraform destroy

Project status:
This is a learning and portfolio project intended to demonstrate DevOps fundamentals. It is not designed for production use.

Author:
Bogdan Poliiektov
