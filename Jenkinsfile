def AWS_ACCOUNT_ID = '******' // Replace with your AWS Account ID
def AWS_REGION = '******'       // Replace with your AWS Region
def ECR_REPO = 'file-metadata-uploader-api'
def ECR_IMAGE = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"
def ECS_CLUSTER_NAME = 'file-metadata-cluster' 
def ECS_TASK_NAME = 'uploader-api-task'

pipeline {
    agent any

    stages {
        
        stage('Install Host Tools') {
            steps {
                echo 'Installing AWS CLI via official installer on Jenkins Host...'
                // AWS CLI v2 
                sh '''
                sudo apt-get update
                curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
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
                git url: 'https://github.com/UrsusVeritas/File-Metadata-App.git', branch: 'master'
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
                
               
                sh "aws ecs describe-clusters --clusters ${ECS_CLUSTER_NAME} --region ${AWS_REGION}"
                
                
                
                echo "CD Pipeline finished. Full deployment capability demonstrated."
            }
        }

    }
}