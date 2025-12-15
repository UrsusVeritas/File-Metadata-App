# infra/backend.tf
terraform {
  required_version = ">= 1.0.0"

  backend "s3" {
    bucket         = "devops-project-terraform-state-chedesan" # Ваше имя бакета
    key            = "devops-project/terraform.tfstate"       # Путь к файлу состояния внутри бакета
    region         = "us-east-1"                              # Ваш регион (предполагаем us-east-1, если другой - замените)
    encrypt        = true                                     # Шифрование данных в S3
    dynamodb_table = "terraform-locks"                        # Имя таблицы для блокировки
  }
}

# Настройка провайдера AWS (для всех остальных ресурсов)
provider "aws" {
  region = "us-east-1" # Ваш регион
}