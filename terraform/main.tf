terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

locals {
  domain_name = "lemaire.tel"
  subdomain   = "pass.${local.domain_name}"
  project     = "lemaire.tel-pass-service"

  common_tags = {
    Project     = local.project
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

data "aws_caller_identity" "current" {}

data "aws_acm_certificate" "lemaire_tel" {
  domain   = local.domain_name
  statuses = ["ISSUED"]
}

data "aws_route53_zone" "main" {
  name         = local.domain_name
  private_zone = false
}