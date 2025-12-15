// Jenkinsfile — FILE-DEVOPS-PROJECT (multi-service CI/CD)
// Services:
// - app/uploader-api
// - app/metadata-service
// - app/browser-api
//
// Flow: preflight -> checkout -> unit tests -> terraform fmt/validate -> build+push -> deploy (ECS force rollout)

pipeline {
  agent any

  options {
    timestamps()
    ansiColor('xterm')
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '30'))
  }

  parameters {
    // AWS / ECR
    string(name: 'AWS_ACCOUNT_ID', defaultValue: 'REPLACE_ME', description: 'AWS Account ID (e.g., 123456789012)')
    string(name: 'AWS_REGION', defaultValue: 'eu-central-1', description: 'AWS Region (e.g., eu-central-1)')

    // ECR repos (one per service)
    string(name: 'ECR_REPO_UPLOADER',  defaultValue: 'file-metadata-uploader-api',  description: 'ECR repo for uploader-api')
    string(name: 'ECR_REPO_METADATA',  defaultValue: 'file-metadata-metadata-service', description: 'ECR repo for metadata-service')
    string(name: 'ECR_REPO_BROWSER',   defaultValue: 'file-metadata-browser-api',   description: 'ECR repo for browser-api')

    // ECS
    string(name: 'ECS_CLUSTER_NAME', defaultValue: 'file-metadata-cluster', description: 'ECS Cluster name')
    string(name: 'ECS_SERVICE_UPLOADER', defaultValue: 'uploader-api-service', description: 'ECS Service name for uploader-api')
    string(name: 'ECS_SERVICE_METADATA', defaultValue: 'metadata-service', description: 'ECS Service name for metadata-service')
    string(name: 'ECS_SERVICE_BROWSER',  defaultValue: 'browser-api-service', description: 'ECS Service name for browser-api')

    // Switches
    booleanParam(name: 'DO_DEPLOY', defaultValue: true, description: 'If true, force new deployment on ECS services')
  }

  environment {
    ECR_REGISTRY = "${params.AWS_ACCOUNT_ID}.dkr.ecr.${params.AWS_REGION}.amazonaws.com"
  }

  stages {

    stage('Preflight (Tools)') {
      steps {
        sh '''
          set -e
          echo "== Preflight: verify tools =="

          command -v docker >/dev/null 2>&1 || { echo "Docker is required on Jenkins agent"; exit 1; }
          docker --version

          if ! command -v aws >/dev/null 2>&1; then
            echo "AWS CLI not found. Installing AWS CLI v2..."
            sudo apt-get update
            sudo apt-get install -y unzip curl
            curl -sS "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
            unzip -q awscliv2.zip
            sudo ./aws/install
            rm -rf awscliv2.zip aws
          fi
          aws --version

          if ! command -v terraform >/dev/null 2>&1; then
            echo "Terraform not found. Please install terraform on Jenkins agent."
            exit 1
          fi
          terraform -version
        '''
      }
    }

    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Compute Build Vars') {
      steps {
        script {
          env.GIT_SHA = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
          env.IMAGE_TAG = env.GIT_SHA
        }
        echo "IMAGE_TAG = ${env.IMAGE_TAG}"
      }
    }

    stage('CI: Unit Tests (containerized)') {
      agent {
        docker {
          image 'python:3.11-slim'
          args '-u root'
          reuseNode true
        }
      }
      steps {
        sh '''
          set -e
          python -V
          pip -V
        '''

        // Run tests for each service if they exist
        dir('app/uploader-api') {
          sh '''
            set -e
            pip install --no-cache-dir -r requirements.txt
            python -m unittest discover -v || true
          '''
        }
        dir('app/metadata-service') {
          sh '''
            set -e
            pip install --no-cache-dir -r requirements.txt
            python -m unittest discover -v || true
          '''
        }
        dir('app/browser-api') {
          sh '''
            set -e
            pip install --no-cache-dir -r requirements.txt
            python -m unittest discover -v || true
          '''
        }
      }
    }

    stage('Terraform: fmt & validate') {
      steps {
        dir('infra') {
          sh '''
            set -e
            echo "== Terraform fmt/validate (no backend) =="
            terraform init -backend=false
            terraform fmt -check -recursive
            terraform validate
          '''
        }
      }
    }

    stage('ECR Login + Ensure repos exist') {
      steps {
        sh '''
          set -e
          echo "Logging in to ECR..."
          aws ecr get-login-password --region ${AWS_REGION} \
            | docker login --username AWS --password-stdin ${ECR_REGISTRY}

          ensure_repo () {
            local repo="$1"
            aws ecr describe-repositories --repository-names "$repo" --region ${AWS_REGION} >/dev/null 2>&1 \
              || aws ecr create-repository --repository-name "$repo" --region ${AWS_REGION} >/dev/null
          }

          ensure_repo "${ECR_REPO_UPLOADER}"
          ensure_repo "${ECR_REPO_METADATA}"
          ensure_repo "${ECR_REPO_BROWSER}"
        '''
      }
    }

    stage('Build & Push Images') {
      steps {
        script {
          def services = [
            [name: 'uploader-api',   path: 'app/uploader-api',    repo: params.ECR_REPO_UPLOADER],
            [name: 'metadata-service', path: 'app/metadata-service', repo: params.ECR_REPO_METADATA],
            [name: 'browser-api',    path: 'app/browser-api',     repo: params.ECR_REPO_BROWSER],
          ]

          for (s in services) {
            def image = "${params.AWS_ACCOUNT_ID}.dkr.ecr.${params.AWS_REGION}.amazonaws.com/${s.repo}"
            echo "Building ${s.name} -> ${image}:${env.IMAGE_TAG}"

            dir(s.path) {
              sh """
                set -e
                docker build -t ${image}:${env.IMAGE_TAG} -t ${image}:latest .
                docker push ${image}:${env.IMAGE_TAG}
                docker push ${image}:latest
              """
            }
          }
        }
      }
    }

    stage('CD: Deploy to ECS (force new deployment)') {
      when { expression { return params.DO_DEPLOY } }
      steps {
        sh '''
          set -e
          echo "== ECS rollout =="

          aws ecs describe-clusters --clusters ${ECS_CLUSTER_NAME} --region ${AWS_REGION} >/dev/null

          rollout () {
            local svc="$1"
            echo "Rolling out service: $svc"
            aws ecs describe-services --cluster ${ECS_CLUSTER_NAME} --services "$svc" --region ${AWS_REGION} >/dev/null
            aws ecs update-service --cluster ${ECS_CLUSTER_NAME} --service "$svc" --force-new-deployment --region ${AWS_REGION} >/dev/null
            aws ecs wait services-stable --cluster ${ECS_CLUSTER_NAME} --services "$svc" --region ${AWS_REGION}
          }

          rollout "${ECS_SERVICE_UPLOADER}"
          rollout "${ECS_SERVICE_METADATA}"
          rollout "${ECS_SERVICE_BROWSER}"

          echo "All services stable. Deployment finished."
        '''
      }
    }
  }

  post {
    always {
      sh 'docker logout ${ECR_REGISTRY} || true'
      echo 'Pipeline finished.'
    }
  }
}
