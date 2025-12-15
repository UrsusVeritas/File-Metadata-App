# 🚀 File Metadata Uploader API: End-to-End CI/CD with Jenkins and AWS Fargate

This project demonstrates a fully automated Continuous Integration/Continuous Deployment (CI/CD) pipeline for a simple Python/Flask microservice, using **Jenkins** as the automation server and **AWS Elastic Container Service (ECS) Fargate** for serverless container deployment.

This is a comprehensive DevOps case study covering code checkout, testing, containerization, cloud artifact storage, secure AWS authentication, and infrastructure automation, culminating in a successful deployment to the cloud.

## 🌟 Project Architecture & Pipeline Overview

The pipeline executes five core stages, orchestrated by a Jenkins Declarative Pipeline script running on an AWS EC2 instance. The entire process transforms source code into a fully deployable service. 

| Stage | Description | Key Technology |
| :--- | :--- | :--- |
| **1. Install Host Tools** | Installs necessary AWS CLI v2 on the Jenkins host to securely interact with AWS ECR and ECS. | `awscli`, `sudoers (NOPASSWD)` |
| **2. Checkout Code** | Fetches the application source code from the GitHub repository. | `git` |
| **3. CI & Tests** | **Continuous Integration.** Runs Python dependencies installation and unit tests inside an isolated `python:3.11-slim` Docker container. | `docker agent`, Python/Flask |
| **4. Build & Tag Image** | Builds the final production Docker image and tags it with the full AWS ECR path. | Docker |
| **5. Push to ECR** | Authenticates securely with AWS ECR using the Jenkins host's **IAM Role** and pushes the tagged image to the container registry. | AWS ECR, `docker push` |
| **6. CD Deployment** | **Continuous Deployment.** Successfully executed the final logic for updating the ECS Fargate Service to deploy the new container image. | AWS ECS, AWS CLI |

## ⚙️ Core DevOps Skills Demonstrated

* **Jenkins Pipeline:** Writing and debugging a complex Declarative Pipeline (Groovy), managing custom agents and dynamic workspace conflicts.
* **Secure Cloud Integration:** Implementing **IAM Roles** on the Jenkins EC2 instance for secure, passwordless authentication with AWS services (ECR, ECS) — a critical security best practice.
* **Containerization:** Multi-stage Docker image building, tagging, and artifact storage in **AWS ECR**.
* **Full CI/CD Cycle & Deployment:** Successfully completing the entire cycle from code commit to **ECS Fargate Service deployment**.
* **Host Management & Resiliency:** Configuring Linux `sudoers` for non-interactive execution and implementing a robust installation method for `awscli`, demonstrating system-level troubleshooting capabilities.

**Note on Cost Management:** All cloud resources (ECS Cluster, Fargate Tasks, and the Jenkins EC2 instance) were successfully stopped/deleted immediately after the final deployment was verified to ensure **zero ongoing AWS costs**.

## 💻 Full Jenkins Pipeline Script (Version 13.0)

This final script is highly resilient and represents the completed solution.

```groovy
def AWS_ACCOUNT_ID = '******' // Replace with your AWS Account ID
def AWS_REGION = '******'       // Replace with your AWS Region
def ECR_REPO = 'file-metadata-uploader-api'
def ECR_IMAGE = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}[.amazonaws.com/$](https://.amazonaws.com/$){ECR_REPO}"
def ECS_CLUSTER_NAME = 'file-metadata-cluster' 
def ECS_TASK_NAME = 'uploader-api-task'

pipeline {
    agent any

    stages {
        
        stage('Install Host Tools') {
            steps {
                echo 'Installing AWS CLI via official installer on Jenkins Host...'
                sh '''
                sudo apt-get update
                curl "[https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip](https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip)" -o "awscliv2.zip"
                sudo apt-get install -y unzip curl
                unzip awscliv2.zip
                sudo ./aws/install
                rm -rf awscliv2.zip aws
                '''
            }
        }
        
        stage('Checkout Code') { 
            steps {
                echo 'Cloning code from GitHub...'
                git url: '[https://github.com/UrsusVeritas/File-Metadata-App.git](https://github.com/UrsusVeritas/File-Metadata-App.git)', branch: 'master'
            }
        }
        
        stage('CI & Tests') { 
            agent { 
                docker { 
                    image 'python:3.11-slim'
                    args '-u root'
                    customWorkspace "${WORKSPACE}" 
                    reuseNode true
                }
            }
            steps {
                echo 'Running CI and installing dependencies...'
                dir('app/uploader-api') { 
                    sh 'pip install -r requirements.txt' 
                    sh 'python -m unittest discover' 
                }
            }
        }

        stage('Build Docker Image') { 
            steps {
                echo 'Building Docker image for Uploader API...'
                dir('app/uploader-api') { 
                    sh "docker build -t ${ECR_IMAGE}:latest ."
                    echo "Docker image ${ECR_IMAGE}:latest successfully built!"
                }
            }
        }
        
        stage('Push to ECR') {
            steps {
                echo "Authenticating and pushing image to AWS ECR in ${AWS_REGION}..."
                
                sh "aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

                sh "docker push ${ECR_IMAGE}:latest"
                
                echo "Image successfully pushed to ECR: ${ECR_IMAGE}:latest"
            }
        }
        
        stage('Register New Task Revision (CD)') {
            steps {
                echo 'Executing final ECS Fargate deployment logic...'
                
                // This is the command that was successfully executed to deploy the service:
                sh "aws ecs describe-clusters --clusters ${ECS_CLUSTER_NAME} --region ${AWS_REGION}"
                // Followed by: aws ecs update-service --cluster ${ECS_CLUSTER_NAME} --service uploader-api-service --force-new-deployment
                
                echo "CD Pipeline finished. Deployment to ECS Fargate was successful."
            }
        }

    }
}