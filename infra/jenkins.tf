resource "aws_security_group" "jenkins_sg" {
  name        = "jenkins-security-group"
  description = "Allow SSH and Jenkins port 8080"
  vpc_id      = module.vpc.vpc_id # Используем ID VPC, созданный на предыдущем шаге

  # Разрешить SSH-доступ (порт 22) отовсюду (0.0.0.0/0)
  ingress {
    description = "SSH Access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] 
  }

  # Разрешить доступ к веб-интерфейсу Jenkins (порт 8080) отовсюду
  ingress {
    description = "Jenkins HTTP"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Разрешить весь исходящий трафик (по умолчанию)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # Все протоколы
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "Jenkins-SG"
  }
}

# 2. Роль IAM для сервера Jenkins
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
    }, ],
  })
}

# 3. Присоединение политики администратора к роли
resource "aws_iam_role_policy_attachment" "jenkins_role_policy_attach" {
  role       = aws_iam_role.jenkins_instance_role.name
  # Даем Jenkins полные права администратора для управления проектом
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess" 
}

# 4. Профиль экземпляра (Instance Profile) для передачи роли на EC2
resource "aws_iam_instance_profile" "jenkins_instance_profile" {
  name = "JenkinsInstanceProfile"
  role = aws_iam_role.jenkins_instance_role.name
}
# 5. Сам сервер EC2 для Jenkins
resource "aws_instance" "jenkins_server" {
  # Ubuntu 22.04 LTS (HVM) - Найдено для региона us-east-1
  ami           = "ami-0ecb62995f68bb549" 
  instance_type = "t3.medium" # t3.medium - хороший баланс между ценой и производительностью для Jenkins

  # Размещаем в ПУБЛИЧНОЙ подсети (чтобы мы могли до него достучаться)
  subnet_id = module.vpc.public_subnets[0]
  associate_public_ip_address = true 

  # Ключевая пара для SSH (убедитесь, что у вас есть этот ключ в AWS!)
  key_name      = "jenkins-ssh-key-for-devops" # <--- ВАЖНО: ЗАМЕНИТЕ НА ИМЯ ВАШЕГО SSH-КЛЮЧА В AWS!

  # Прикрепляем группу безопасности и IAM-роль
  vpc_security_group_ids = [aws_security_group.jenkins_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.jenkins_instance_profile.name

  # Установка Jenkins, Docker и Java (скрипт запуска)
  user_data = <<-EOF
              #!/bin/bash
              # Обновление системы
              sudo apt update -y
              
              # Установка Java 17 (требуется для Jenkins)
              sudo apt install openjdk-17-jre -y
              
              # Установка Docker
              sudo apt install docker.io -y
              sudo usermod -aG docker ubuntu
              sudo usermod -aG docker jenkins
              
              # Установка Jenkins
              curl -fsSL https://pkg.jenkins.io/debian/jenkins.io-2023.key | sudo tee \
                /usr/share/keyrings/jenkins-keyring.asc > /dev/null
              echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
                https://pkg.jenkins.io/debian binary/ | sudo tee \
                /etc/apt/sources.list.d/jenkins.list > /dev/null
              sudo apt-get update -y
              sudo apt-get install jenkins -y
              
              # Запуск Jenkins
              sudo systemctl start jenkins
              sudo systemctl enable jenkins
              EOF

  tags = {
    Name = "Jenkins-Server"
    Project = "FileMetadata"
  }
}