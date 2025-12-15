# infra/main.tf

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0" 

  name = "devops-project-vpc"
  cidr = "10.0.0.0/16" 

  # --- (High Availability) ---
  azs              = ["us-east-1b", "us-east-1a"] 
  
  # --- Subnets ---
  public_subnets   = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets  = ["10.0.3.0/24", "10.0.4.0/24"]

  # ---  NAT Gateway ---
  enable_nat_gateway = true   
  single_nat_gateway = true   

  # ---  DNS ---
  enable_dns_hostnames = true
  enable_dns_support   = true

  # --- tags ---
  tags = {
    Terraform = "true"
    Environment = "DevOps"
    Project = "FileMetadata"
  }
}