variable "allowed_cidr" {
  description = "CIDR allowed to reach Jenkins SSH (22) and UI (8080). Set to your IP, e.g. 203.0.113.5/32"
  type        = string
  default     = "0.0.0.0/0" # Override in terraform.tfvars
}

resource "aws_security_group" "jenkins_sg" {
  name        = "jenkins-security-group"
  description = "Allow SSH and Jenkins port 8080"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "SSH Access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
  }

  ingress {
    description = "Jenkins HTTP"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "Jenkins-SG"
  }
}


resource "aws_iam_role" "jenkins_instance_role" {
  name = "JenkinsInstanceRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "ec2.amazonaws.com"
      },
    }],
  })
}

# Least-privilege policy — only the permissions Jenkins actually needs
resource "aws_iam_policy" "jenkins_scoped_policy" {
  name        = "JenkinsScopedPolicy"
  description = "Scoped CI/CD permissions: ECR push/pull, ECS deploy, S3 state, DynamoDB locks"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid      = "ECRAuth"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Sid    = "ECRRepoAccess"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:CreateRepository",
          "ecr:DescribeRepositories",
          "ecr:ListImages",
          "ecr:DescribeImages",
        ]
        Resource = "arn:aws:ecr:*:*:repository/file-metadata-*"
      },
      {
        Sid    = "ECSAccess"
        Effect = "Allow"
        Action = [
          "ecs:DescribeClusters",
          "ecs:DescribeServices",
          "ecs:UpdateService",
          "ecs:DescribeTaskDefinition",
          "ecs:RegisterTaskDefinition",
          "ecs:ListTasks",
          "ecs:DescribeTasks",
        ]
        Resource = "*"
      },
      {
        Sid    = "S3StateAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
        ]
        Resource = [
          "arn:aws:s3:::devops-project-terraform-state-chedesan",
          "arn:aws:s3:::devops-project-terraform-state-chedesan/*",
        ]
      },
      {
        Sid    = "DynamoDBLocks"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
        ]
        Resource = "arn:aws:dynamodb:*:*:table/terraform-locks"
      },
      {
        Sid      = "IAMPassRole"
        Effect   = "Allow"
        Action   = ["iam:PassRole"]
        Resource = "arn:aws:iam::*:role/ecs-task-*"
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "jenkins_role_policy_attach" {
  role       = aws_iam_role.jenkins_instance_role.name
  policy_arn = aws_iam_policy.jenkins_scoped_policy.arn
}


resource "aws_iam_instance_profile" "jenkins_instance_profile" {
  name = "JenkinsInstanceProfile"
  role = aws_iam_role.jenkins_instance_role.name
}

resource "aws_instance" "jenkins_server" {
  # Ubuntu 22.04 LTS (HVM)
  ami           = "ami-0ecb62995f68bb549"
  instance_type = "t3.medium"

  subnet_id                   = module.vpc.public_subnets[0]
  associate_public_ip_address = true

  key_name = "jenkins-ssh-key-for-devops"

  vpc_security_group_ids = [aws_security_group.jenkins_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.jenkins_instance_profile.name

  # Enforce IMDSv2 to prevent SSRF-based metadata credential theft
  metadata_options {
    http_tokens = "required"
  }

  user_data = <<-EOF
              #!/bin/bash

              sudo apt update -y

              sudo apt install openjdk-17-jre -y

              sudo apt install docker.io -y
              sudo usermod -aG docker ubuntu
              sudo usermod -aG docker jenkins

              curl -fsSL https://pkg.jenkins.io/debian/jenkins.io-2023.key | sudo tee \
                /usr/share/keyrings/jenkins-keyring.asc > /dev/null
              echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
                https://pkg.jenkins.io/debian binary/ | sudo tee \
                /etc/apt/sources.list.d/jenkins.list > /dev/null
              sudo apt-get update -y
              sudo apt-get install jenkins -y

              sudo systemctl start jenkins
              sudo systemctl enable jenkins
              EOF

  tags = {
    Name    = "Jenkins-Server"
    Project = "FileMetadata"
  }
}
