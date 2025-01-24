#---------------------------------------------------------------
# EKS Cluster
#---------------------------------------------------------------
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.11"

  cluster_name                   = local.name
  cluster_version                = local.cluster_version
  cluster_endpoint_public_access = true
  kms_key_enable_default_policy  = true

  # Give the Terraform identity admin access to the cluster
  # which will allow resources to be deployed into the cluster
  enable_cluster_creator_admin_permissions = true

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_addons = {
    aws-ebs-csi-driver = {
      most_recent              = true
      service_account_role_arn = module.ebs_csi_driver_irsa.iam_role_arn
    }
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      before_compute = true # Ensure the addon is configured before compute resources are created
      most_recent    = true
    }
    eks-pod-identity-agent = {
      most_recent = true
    } 
  }

  # for production cluster, add a node group for add-ons that should not be inerrupted such as coredns
  eks_managed_node_groups = {
    initial = {
      instance_types = ["m6i.large", "m5.large", "m5n.large", "m5zn.large"]
      capacity_type  = var.capacity_type # defaults to SPOT
      min_size       = 1
      max_size       = 5
      desired_size   = 3
      subnet_ids     = module.vpc.private_subnets
    }
  }

  tags = local.tags

  depends_on = [module.vpc]
}

resource "kubectl_manifest" "configmap" {
  yaml_body = templatefile("${path.module}/configmap.yaml", {
    awsAccountID = data.aws_caller_identity.current.account_id
    eksOIDC      = module.eks.oidc_provider
    vpcID        = module.vpc.vpc_id
    subnetIDs    = join(",", module.vpc.private_subnets)
    clusterName  = module.eks.cluster_name
    region       = local.region
  })

  depends_on = [module.eks]
}