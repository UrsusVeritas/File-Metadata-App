# infra/backend.tf
terraform {
  required_version = ">= 1.0.0"

  backend "s3" {
    bucket         = "devops-project-terraform-state-chedesan" 
    key            = "devops-project/terraform.tfstate"       
    region         = "us-east-1"                             
    encrypt        = true                                     
    dynamodb_table = "terraform-locks"                        
  }
}


provider "aws" {
  region = "us-east-1" # Ваш регион
}