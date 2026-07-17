from mcp.server.fastmcp import FastMCP
import boto3
import logging
import os
from tools.AWSResourceCreator import AWSResourceCreator
from typing import Callable, Dict, Any, Optional, List, Union, Type
from github import Github
from dotenv import load_dotenv
from datetime import datetime, timedelta


load_dotenv()

logger = logging.getLogger('MCP Server')
logger.setLevel(logging.INFO)


access_token = os.environ.get("GITHUB_TOKEN")
github = Github(access_token)


mcp = FastMCP("Custom MCP Server", "0.1.0")


@mcp.tool()
def fetch_github_repo_info(repo: str) -> dict:
    """
    Fetches GitHub repository information (both public and private) using the provided repository name.
    :param repo: The name of the repository in the format 'owner/repo_name'.
    :return: A dictionary containing repository information such as name, description, owner, etc.
    """
    try:
        # verify the github has been initialized with the access token
        if not github or not access_token:
            print(f"access_token: {access_token}")
            print(f"github: {github}")
            raise ValueError("GitHub client is not initialized with a valid access token.")
        github_repo = github.get_repo(repo)
        return {
            "name": github_repo.name,
            "description": github_repo.description,
            "owner": github_repo.owner.login,
            "owner_url": github_repo.owner.html_url,
            "created_at": github_repo.created_at,
            "updated_at": github_repo.updated_at,
            "pushed_at": github_repo.pushed_at,
            "clone_url": github_repo.clone_url,
            "ssh_url": github_repo.ssh_url,
            "homepage": github_repo.homepage,
            "size": github_repo.size,
            "watchers": github_repo.watchers_count,
            "default_branch": github_repo.default_branch,
            "open_issues": github_repo.open_issues,
            "subscribers_count": github_repo.subscribers_count,
            "language": github_repo.language,
            "has_issues": github_repo.has_issues,
            "url": github_repo.html_url,
            "stars": github_repo.stargazers_count,
            "forks": github_repo.forks_count,
            "issues": github_repo.open_issues_count,
        }
    except Exception as e:
        print(f"Error fetching repository info: {e}")
        return None


@mcp.tool()
def fetch_aws_ec2_instances(region_name: str = "us-east-1") -> None:
    """
    Fetches and describes all EC2 instances in the specified AWS region.
    :param region_name: The name of the AWS region (e.g., 'us-east-1') default is 'us-east-1'.
    :return: A list of EC2 instances in the specified region.
    """
    # Initialize a session using Amazon EC2
    session = boto3.Session(region_name=region_name)

    # Initialize EC2 resource
    ec2_client = session.client('ec2')

    response = ec2_client.describe_instances(
        Filters=[{
            'Name': 'instance-state-name',
            'Values': ['pending', 'running', 'shutting-down', 'terminated', 'stopping', 'stopped']
        }]
    )

    # Fetch and return the instances from the response
    instances = []
    for reservation in response['Reservations']:
        instances.extend(reservation['Instances'])
    
    return instances


@mcp.tool()
def describe_ec2_instances(region_name: str = "us-east-1") -> None:
    """
    Fetches and describes all EC2 instances in the specified AWS region.
    :param region_name: The name of the AWS region (e.g., 'us-east-1') default is 'us-east-1'.
    :return: A list of EC2 instances in the specified region.
    """
    # Initialize a session using Amazon EC2
    session = boto3.Session(region_name=region_name)

    # Initialize EC2 client
    ec2_client = session.client('ec2')

    # Fetch all EC2 instances
    return ec2_client.describe_instances()


@mcp.tool()
def describe_ec2_instance_status(instance_ids: list, region_name: str = "us-east-1") -> None:
    """
    Fetches and describes the status of specified EC2 instances in the specified AWS region.
    :param instance_ids: A list of EC2 instance IDs to describe.
    :param region_name: The name of the AWS region (e.g., 'us-east-1') default is 'us-east-1'.
    :return: A list of EC2 instance statuses in the specified region.
    """
    # Initialize a session using Amazon EC2
    session = boto3.Session(region_name=region_name)

    # Initialize EC2 client
    ec2_client = session.client('ec2')

    # Fetch the status of specified EC2 instances
    return ec2_client.describe_instance_status(InstanceIds=instance_ids)


@mcp.tool()
def get_ec2_metrics(instance_id: str, start_time: datetime, end_time: datetime, period: int = 300) -> Dict[str, List]:
    """
    Retrieve EC2 monitoring metrics (CPUUtilization, NetworkIn, NetworkOut, etc.) for a given instance.
    
    Parameters:
    - instance_id: EC2 instance ID (str)
    - start_time: Start time for the metrics (datetime)
    - end_time: End time for the metrics (datetime)
    - period: Granularity of the metrics (in seconds, default is 300)
    
    Returns:
    - metrics: A dictionary of metrics data (e.g., CPU, Network, Disk, etc.)
    """
    cloudwatch = boto3.client('cloudwatch')

    # List of metrics to retrieve (you can add more metrics as needed)
    metric_names = [
        'CPUUtilization',
        'NetworkIn',
        'NetworkOut',
        'DiskReadOps',
        'DiskWriteOps',
        'DiskReadBytes',
        'DiskWriteBytes'
    ]
    
    metrics_data = {}

    for metric_name in metric_names:
        # Get metric data for each metric
        response = cloudwatch.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': f'metric_{metric_name}',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/EC2',
                            'MetricName': metric_name,
                            'Dimensions': [
                                {
                                    'Name': 'InstanceId',
                                    'Value': instance_id
                                }
                            ]
                        },
                        'Period': period,
                        'Stat': 'Average',  # You can also use 'Sum', 'Maximum', etc.
                    },
                    'ReturnData': True
                }
            ],
            StartTime=start_time,
            EndTime=end_time
        )
        
        # Store the metric data in the dictionary
        if 'MetricDataResults' in response:
            metrics_data[metric_name] = response['MetricDataResults'][0].get('Values', [])
    
    return metrics_data


@mcp.tool()
def start_ec2_instance(instance_id: str, region_name: str = "us-east-1") -> None:
    """
    Starts an EC2 instance in the specified AWS region.
    :param instance_id: The ID of the EC2 instance to start.
    :param region_name: The name of the AWS region (e.g., 'us-east-1') default is 'us-east-1'.
    :return: None
    """
    # Initialize a session using Amazon EC2
    session = boto3.Session(region_name=region_name)

    # Initialize EC2 client
    ec2_client = session.client('ec2')

    # Start the specified EC2 instance
    ec2_client.start_instances(InstanceIds=[instance_id])
    logger.info(f"Started EC2 instance: {instance_id} in region: {region_name}")


@mcp.tool()
def shut_down_ec2_instance(instance_id: str, region_name: str = "us-east-1") -> None:
    """
    Shuts down an EC2 instance in the specified AWS region.
    :param instance_id: The ID of the EC2 instance to shut down.
    :param region_name: The name of the AWS region (e.g., 'us-east-1') default is 'us-east-1'.
    :return: None
    """
    # Initialize a session using Amazon EC2
    session = boto3.Session(region_name=region_name)

    # Initialize EC2 client
    ec2_client = session.client('ec2')

    # Stop the specified EC2 instance
    ec2_client.stop_instances(InstanceIds=[instance_id])
    logger.info(f"Shut down EC2 instance: {instance_id} in region: {region_name}")


@mcp.tool()
def scan_aws_resources(region_name: str = "us-east-1") -> dict:
    """
    Scans all available AWS resources in a given region and returns a comprehensive inventory.
    
    Args:
        region_name (str): AWS region name (default: "us-east-1")
        
    Returns:
        dict: Dictionary containing all discovered AWS resources
    """
    import boto3
    from botocore.exceptions import ClientError
    import logging
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize result dictionary
    resources = {
        "region": region_name,
        "ec2": {},
        "s3": {},
        "rds": {},
        "lambda": {},
        "dynamodb": {},
        "elasticache": {},
        "elb": {},
        "elbv2": {},
        "ecs": {},
        "eks": {},
        "cloudformation": {},
        "route53": {},
        "cloudfront": {},
        "sqs": {},
        "sns": {},
        "iam": {},
        "vpc": {},
    }
    
    # Create a boto3 session
    session = boto3.Session(region_name=region_name)
    
    # EC2 Resources
    try:
        logger.info(f"Scanning EC2 resources in {region_name}...")
        ec2 = session.client('ec2')
        
        # Get EC2 instances
        instances_response = ec2.describe_instances()
        resources["ec2"]["instances"] = []
        
        for reservation in instances_response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instance_info = {
                    "id": instance.get('InstanceId'),
                    "type": instance.get('InstanceType'),
                    "state": instance.get('State', {}).get('Name'),
                    "public_ip": instance.get('PublicIpAddress'),
                    "private_ip": instance.get('PrivateIpAddress'),
                    "launch_time": instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else None,
                    "tags": {tag.get('Key'): tag.get('Value') for tag in instance.get('Tags', [])},
                }
                resources["ec2"]["instances"].append(instance_info)
        
        # Get EBS volumes
        volumes_response = ec2.describe_volumes()
        resources["ec2"]["volumes"] = []
        
        for volume in volumes_response.get('Volumes', []):
            volume_info = {
                "id": volume.get('VolumeId'),
                "size": volume.get('Size'),
                "type": volume.get('VolumeType'),
                "state": volume.get('State'),
                "encrypted": volume.get('Encrypted'),
                "attached_to": [attachment.get('InstanceId') for attachment in volume.get('Attachments', [])],
                "tags": {tag.get('Key'): tag.get('Value') for tag in volume.get('Tags', [])},
            }
            resources["ec2"]["volumes"].append(volume_info)
        
        # Get security groups
        sg_response = ec2.describe_security_groups()
        resources["ec2"]["security_groups"] = []
        
        for sg in sg_response.get('SecurityGroups', []):
            sg_info = {
                "id": sg.get('GroupId'),
                "name": sg.get('GroupName'),
                "description": sg.get('Description'),
                "vpc_id": sg.get('VpcId'),
                "inbound_rules": sg.get('IpPermissions', []),
                "outbound_rules": sg.get('IpPermissionsEgress', []),
                "tags": {tag.get('Key'): tag.get('Value') for tag in sg.get('Tags', [])},
            }
            resources["ec2"]["security_groups"].append(sg_info)
            
        # Get AMIs owned by user
        ami_response = ec2.describe_images(Owners=['self'])
        resources["ec2"]["owned_amis"] = []
        
        for ami in ami_response.get('Images', []):
            ami_info = {
                "id": ami.get('ImageId'),
                "name": ami.get('Name'),
                "description": ami.get('Description'),
                "state": ami.get('State'),
                "creation_date": ami.get('CreationDate'),
                "tags": {tag.get('Key'): tag.get('Value') for tag in ami.get('Tags', [])},
            }
            resources["ec2"]["owned_amis"].append(ami_info)
            
    except ClientError as e:
        logger.error(f"Error scanning EC2 resources: {e}")
        resources["ec2"]["error"] = str(e)
    
    # VPC Resources
    try:
        logger.info(f"Scanning VPC resources in {region_name}...")
        vpc_client = session.client('ec2')
        
        # Get VPCs
        vpc_response = vpc_client.describe_vpcs()
        resources["vpc"]["vpcs"] = []
        
        for vpc in vpc_response.get('Vpcs', []):
            vpc_info = {
                "id": vpc.get('VpcId'),
                "cidr_block": vpc.get('CidrBlock'),
                "state": vpc.get('State'),
                "is_default": vpc.get('IsDefault'),
                "tags": {tag.get('Key'): tag.get('Value') for tag in vpc.get('Tags', [])},
            }
            resources["vpc"]["vpcs"].append(vpc_info)
        
        # Get subnets
        subnet_response = vpc_client.describe_subnets()
        resources["vpc"]["subnets"] = []
        
        for subnet in subnet_response.get('Subnets', []):
            subnet_info = {
                "id": subnet.get('SubnetId'),
                "vpc_id": subnet.get('VpcId'),
                "cidr_block": subnet.get('CidrBlock'),
                "availability_zone": subnet.get('AvailabilityZone'),
                "available_ip_count": subnet.get('AvailableIpAddressCount'),
                "tags": {tag.get('Key'): tag.get('Value') for tag in subnet.get('Tags', [])},
            }
            resources["vpc"]["subnets"].append(subnet_info)
            
        # Get route tables
        rt_response = vpc_client.describe_route_tables()
        resources["vpc"]["route_tables"] = []
        
        for rt in rt_response.get('RouteTables', []):
            rt_info = {
                "id": rt.get('RouteTableId'),
                "vpc_id": rt.get('VpcId'),
                "routes": rt.get('Routes', []),
                "associations": rt.get('Associations', []),
                "tags": {tag.get('Key'): tag.get('Value') for tag in rt.get('Tags', [])},
            }
            resources["vpc"]["route_tables"].append(rt_info)
            
        # Get internet gateways
        igw_response = vpc_client.describe_internet_gateways()
        resources["vpc"]["internet_gateways"] = []
        
        for igw in igw_response.get('InternetGateways', []):
            igw_info = {
                "id": igw.get('InternetGatewayId'),
                "attachments": igw.get('Attachments', []),
                "tags": {tag.get('Key'): tag.get('Value') for tag in igw.get('Tags', [])},
            }
            resources["vpc"]["internet_gateways"].append(igw_info)
            
    except ClientError as e:
        logger.error(f"Error scanning VPC resources: {e}")
        resources["vpc"]["error"] = str(e)
    
    # S3 Resources (global, but listing buckets in specified region)
    try:
        logger.info(f"Scanning S3 resources in {region_name}...")
        s3 = session.client('s3')
        
        # Get S3 buckets
        buckets_response = s3.list_buckets()
        resources["s3"]["buckets"] = []
        
        for bucket in buckets_response.get('Buckets', []):
            try:
                # Get bucket location
                location = s3.get_bucket_location(Bucket=bucket.get('Name'))
                bucket_region = location.get('LocationConstraint')
                
                # If bucket_region is None, it's in us-east-1
                if bucket_region is None:
                    bucket_region = 'us-east-1'
                
                # Only include buckets in the specified region
                if bucket_region == region_name:
                    # Try to get bucket tags
                    try:
                        tags_response = s3.get_bucket_tagging(Bucket=bucket.get('Name'))
                        tags = {tag.get('Key'): tag.get('Value') for tag in tags_response.get('TagSet', [])}
                    except ClientError:
                        tags = {}
                    
                    bucket_info = {
                        "name": bucket.get('Name'),
                        "creation_date": bucket.get('CreationDate').isoformat() if bucket.get('CreationDate') else None,
                        "region": bucket_region,
                        "tags": tags,
                    }
                    resources["s3"]["buckets"].append(bucket_info)
            except ClientError as e:
                logger.warning(f"Error getting details for bucket {bucket.get('Name')}: {e}")
                continue
                
    except ClientError as e:
        logger.error(f"Error scanning S3 resources: {e}")
        resources["s3"]["error"] = str(e)
    
    # RDS Resources
    try:
        logger.info(f"Scanning RDS resources in {region_name}...")
        rds = session.client('rds')
        
        # Get DB instances
        db_instances_response = rds.describe_db_instances()
        resources["rds"]["instances"] = []
        
        for db in db_instances_response.get('DBInstances', []):
            db_info = {
                "id": db.get('DBInstanceIdentifier'),
                "engine": db.get('Engine'),
                "engine_version": db.get('EngineVersion'),
                "status": db.get('DBInstanceStatus'),
                "allocated_storage": db.get('AllocatedStorage'),
                "instance_class": db.get('DBInstanceClass'),
                "endpoint": db.get('Endpoint', {}).get('Address') if db.get('Endpoint') else None,
                "multi_az": db.get('MultiAZ'),
                "vpc_id": db.get('DBSubnetGroup', {}).get('VpcId') if db.get('DBSubnetGroup') else None,
            }
            
            # Try to get tags
            try:
                arn = db.get('DBInstanceArn')
                if arn:
                    tags_response = rds.list_tags_for_resource(ResourceName=arn)
                    db_info["tags"] = {tag.get('Key'): tag.get('Value') for tag in tags_response.get('TagList', [])}
            except ClientError:
                db_info["tags"] = {}
                
            resources["rds"]["instances"].append(db_info)
            
        # Get snapshots
        snapshots_response = rds.describe_db_snapshots()
        resources["rds"]["snapshots"] = []
        
        for snapshot in snapshots_response.get('DBSnapshots', []):
            snapshot_info = {
                "id": snapshot.get('DBSnapshotIdentifier'),
                "instance_id": snapshot.get('DBInstanceIdentifier'),
                "status": snapshot.get('Status'),
                "type": snapshot.get('SnapshotType'),  # automated or manual
                "creation_time": snapshot.get('SnapshotCreateTime').isoformat() if snapshot.get('SnapshotCreateTime') else None,
                "engine": snapshot.get('Engine'),
            }
            resources["rds"]["snapshots"].append(snapshot_info)
            
    except ClientError as e:
        logger.error(f"Error scanning RDS resources: {e}")
        resources["rds"]["error"] = str(e)
    
    # Lambda Functions
    try:
        logger.info(f"Scanning Lambda resources in {region_name}...")
        lambda_client = session.client('lambda')
        
        # Get Lambda functions
        functions_paginator = lambda_client.get_paginator('list_functions')
        resources["lambda"]["functions"] = []
        
        for page in functions_paginator.paginate():
            for function in page.get('Functions', []):
                function_info = {
                    "name": function.get('FunctionName'),
                    "runtime": function.get('Runtime'),
                    "memory": function.get('MemorySize'),
                    "timeout": function.get('Timeout'),
                    "last_modified": function.get('LastModified'),
                    "arn": function.get('FunctionArn'),
                }
                resources["lambda"]["functions"].append(function_info)
                
    except ClientError as e:
        logger.error(f"Error scanning Lambda resources: {e}")
        resources["lambda"]["error"] = str(e)
    
    # DynamoDB Tables
    try:
        logger.info(f"Scanning DynamoDB resources in {region_name}...")
        dynamodb = session.client('dynamodb')
        
        # Get DynamoDB tables
        tables_response = dynamodb.list_tables()
        resources["dynamodb"]["tables"] = []
        
        for table_name in tables_response.get('TableNames', []):
            try:
                table_details = dynamodb.describe_table(TableName=table_name)
                table = table_details.get('Table', {})
                
                table_info = {
                    "name": table.get('TableName'),
                    "status": table.get('TableStatus'),
                    "size_bytes": table.get('TableSizeBytes'),
                    "item_count": table.get('ItemCount'),
                    "creation_date": table.get('CreationDateTime').isoformat() if table.get('CreationDateTime') else None,
                    "provisioned_throughput": {
                        "read_capacity": table.get('ProvisionedThroughput', {}).get('ReadCapacityUnits'),
                        "write_capacity": table.get('ProvisionedThroughput', {}).get('WriteCapacityUnits'),
                    }
                }
                resources["dynamodb"]["tables"].append(table_info)
            except ClientError as e:
                logger.warning(f"Error getting details for table {table_name}: {e}")
                continue
                
    except ClientError as e:
        logger.error(f"Error scanning DynamoDB resources: {e}")
        resources["dynamodb"]["error"] = str(e)
    
    # ELB (Classic Load Balancers)
    try:
        logger.info(f"Scanning ELB resources in {region_name}...")
        elb = session.client('elb')
        
        # Get classic load balancers
        elbs_response = elb.describe_load_balancers()
        resources["elb"]["load_balancers"] = []
        
        for lb in elbs_response.get('LoadBalancerDescriptions', []):
            lb_info = {
                "name": lb.get('LoadBalancerName'),
                "dns_name": lb.get('DNSName'),
                "scheme": lb.get('Scheme'),
                "vpc_id": lb.get('VPCId'),
                "subnets": lb.get('Subnets', []),
                "security_groups": lb.get('SecurityGroups', []),
                "instances": [instance.get('InstanceId') for instance in lb.get('Instances', [])],
            }
            resources["elb"]["load_balancers"].append(lb_info)
                
    except ClientError as e:
        logger.error(f"Error scanning ELB resources: {e}")
        resources["elb"]["error"] = str(e)
    
    # ELBv2 (Application and Network Load Balancers)
    try:
        logger.info(f"Scanning ELBv2 resources in {region_name}...")
        elbv2 = session.client('elbv2')
        
        # Get ALBs and NLBs
        lbs_response = elbv2.describe_load_balancers()
        resources["elbv2"]["load_balancers"] = []
        
        for lb in lbs_response.get('LoadBalancers', []):
            lb_info = {
                "name": lb.get('LoadBalancerName'),
                "arn": lb.get('LoadBalancerArn'),
                "dns_name": lb.get('DNSName'),
                "scheme": lb.get('Scheme'),
                "vpc_id": lb.get('VpcId'),
                "type": lb.get('Type'),  # application or network
                "state": lb.get('State', {}).get('Code'),
                "subnets": lb.get('AvailabilityZones', []),
                "security_groups": lb.get('SecurityGroups', []),
            }
            
            # Try to get tags
            try:
                tags_response = elbv2.describe_tags(ResourceArns=[lb.get('LoadBalancerArn')])
                for tag_desc in tags_response.get('TagDescriptions', []):
                    if tag_desc.get('ResourceArn') == lb.get('LoadBalancerArn'):
                        lb_info["tags"] = {tag.get('Key'): tag.get('Value') for tag in tag_desc.get('Tags', [])}
            except ClientError:
                lb_info["tags"] = {}
                
            resources["elbv2"]["load_balancers"].append(lb_info)
                
    except ClientError as e:
        logger.error(f"Error scanning ELBv2 resources: {e}")
        resources["elbv2"]["error"] = str(e)
    
    # ECS Clusters and Services
    try:
        logger.info(f"Scanning ECS resources in {region_name}...")
        ecs = session.client('ecs')
        
        # Get ECS clusters
        clusters_response = ecs.list_clusters()
        resources["ecs"]["clusters"] = []
        
        for cluster_arn in clusters_response.get('clusterArns', []):
            try:
                cluster_details = ecs.describe_clusters(clusters=[cluster_arn])
                for cluster in cluster_details.get('clusters', []):
                    
                    # Get services for this cluster
                    services_response = ecs.list_services(cluster=cluster.get('clusterArn'))
                    services = []
                    
                    if services_response.get('serviceArns'):
                        services_details = ecs.describe_services(
                            cluster=cluster.get('clusterArn'),
                            services=services_response.get('serviceArns')
                        )
                        
                        for service in services_details.get('services', []):
                            service_info = {
                                "name": service.get('serviceName'),
                                "status": service.get('status'),
                                "desired_count": service.get('desiredCount'),
                                "running_count": service.get('runningCount'),
                                "task_definition": service.get('taskDefinition'),
                            }
                            services.append(service_info)
                    
                    cluster_info = {
                        "name": cluster.get('clusterName'),
                        "arn": cluster.get('clusterArn'),
                        "status": cluster.get('status'),
                        "registered_container_instances_count": cluster.get('registeredContainerInstancesCount'),
                        "running_tasks_count": cluster.get('runningTasksCount'),
                        "pending_tasks_count": cluster.get('pendingTasksCount'),
                        "active_services_count": cluster.get('activeServicesCount'),
                        "services": services,
                    }
                    resources["ecs"]["clusters"].append(cluster_info)
            except ClientError as e:
                logger.warning(f"Error getting details for cluster {cluster_arn}: {e}")
                continue
                
    except ClientError as e:
        logger.error(f"Error scanning ECS resources: {e}")
        resources["ecs"]["error"] = str(e)
    
    # CloudFormation Stacks
    try:
        logger.info(f"Scanning CloudFormation resources in {region_name}...")
        cf = session.client('cloudformation')
        
        # Get CloudFormation stacks
        stacks_paginator = cf.get_paginator('list_stacks')
        resources["cloudformation"]["stacks"] = []
        
        for page in stacks_paginator.paginate():
            for stack in page.get('StackSummaries', []):
                # Skip deleted stacks
                if stack.get('StackStatus') == 'DELETE_COMPLETE':
                    continue
                    
                stack_info = {
                    "name": stack.get('StackName'),
                    "id": stack.get('StackId'),
                    "status": stack.get('StackStatus'),
                    "creation_time": stack.get('CreationTime').isoformat() if stack.get('CreationTime') else None,
                    "last_updated": stack.get('LastUpdatedTime').isoformat() if stack.get('LastUpdatedTime') else None,
                }
                resources["cloudformation"]["stacks"].append(stack_info)
                
    except ClientError as e:
        logger.error(f"Error scanning CloudFormation resources: {e}")
        resources["cloudformation"]["error"] = str(e)
        
    # IAM Resources (global, but included for completeness)
    try:
        logger.info("Scanning IAM resources (global)...")
        iam = session.client('iam')
        
        # Get IAM users
        users_response = iam.list_users()
        resources["iam"]["users"] = []
        
        for user in users_response.get('Users', []):
            user_info = {
                "name": user.get('UserName'),
                "id": user.get('UserId'),
                "arn": user.get('Arn'),
                "created": user.get('CreateDate').isoformat() if user.get('CreateDate') else None,
            }
            resources["iam"]["users"].append(user_info)
            
        # Get IAM roles
        roles_response = iam.list_roles()
        resources["iam"]["roles"] = []
        
        for role in roles_response.get('Roles', []):
            role_info = {
                "name": role.get('RoleName'),
                "id": role.get('RoleId'),
                "arn": role.get('Arn'),
                "created": role.get('CreateDate').isoformat() if role.get('CreateDate') else None,
            }
            resources["iam"]["roles"].append(role_info)
            
    except ClientError as e:
        logger.error(f"Error scanning IAM resources: {e}")
        resources["iam"]["error"] = str(e)
    
    # Output summary
    logger.info("AWS resource scan completed")
    logger.info(f"Region: {region_name}")
    
    # Print resource counts
    for resource_type, resources_dict in resources.items():
        if resource_type == "region":
            continue
            
        count = 0
        for resource_subtype, resource_list in resources_dict.items():
            if resource_subtype != "error" and isinstance(resource_list, list):
                count += len(resource_list)
                
        logger.info(f"Found {count} {resource_type} resources")
    
    return resources


# Now add the new resource creator tools
@mcp.tool()
def create_ec2_instance(image_id: str, instance_type: str, key_name: str = None,
                       security_group_ids: List[str] = None, subnet_id: str = None,
                       name: str = None, region_name: str = "us-east-1") -> str:
    """
    Creates an EC2 instance in the specified AWS region.
    
    Args:
        image_id: The ID of the AMI to use.
        instance_type: The EC2 instance type (e.g., 't2.micro').
        key_name: The name of the key pair to use (optional).
        security_group_ids: List of security group IDs (optional).
        subnet_id: The ID of the subnet to launch in (optional).
        name: Name tag for the instance (optional).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The ID of the created EC2 instance.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {
        'ImageId': image_id,
        'InstanceType': instance_type,
        'MaxCount': 1,
        'MinCount': 1,
    }
    
    if key_name:
        params['KeyName'] = key_name
    
    if security_group_ids:
        params['SecurityGroupIds'] = security_group_ids
    
    if subnet_id:
        params['SubnetId'] = subnet_id
    
    if name:
        params['Name'] = name
    
    # Use the resource creator to create the instance
    response = resource_creator.create_resource('ec2_instance', params)
    
    # Extract the instance ID
    instance_id = response['Instances'][0]['InstanceId']
    logger.info(f"Created EC2 instance: {instance_id} in region: {region_name}")
    
    return instance_id


@mcp.tool()
def create_ec2_security_group(group_name: str, description: str = None, vpc_id: str = None,
                             ingress_rules: List[Dict] = None, egress_rules: List[Dict] = None,
                             tags: List[Dict] = None, region_name: str = "us-east-1") -> str:
    """
    Creates an EC2 security group in the specified AWS region.
    
    Args:
        group_name: The name for the security group.
        description: Description for the security group (optional).
        vpc_id: The ID of the VPC to create the security group in (optional).
        ingress_rules: List of ingress rules (optional).
        egress_rules: List of egress rules (optional).
        tags: List of tags to apply to the security group (optional).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The ID of the created security group.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {
        'GroupName': group_name
    }
    
    if description:
        params['Description'] = description
    
    if vpc_id:
        params['VpcId'] = vpc_id
    
    if ingress_rules:
        params['IngressRules'] = ingress_rules
    
    if egress_rules:
        params['EgressRules'] = egress_rules
    
    if tags:
        params['Tags'] = tags
    
    # Use the resource creator to create the security group
    response = resource_creator.create_resource('security_group', params)
    
    # Extract the security group ID
    security_group_id = response['GroupId']
    logger.info(f"Created security group: {security_group_id} with name: {group_name}")
    
    return security_group_id


@mcp.tool()
def create_ec2_key_pair(key_name: str, region_name: str = "us-east-1") -> Dict[str, Any]:
    """
    Creates an EC2 key pair in the specified AWS region.
    
    Args:
        key_name: The name for the key pair.
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        Dictionary containing key information including private key material.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {
        'KeyName': key_name
    }
    
    # Use the resource creator to create the key pair
    response = resource_creator.create_resource('key_pair', params)
    logger.info(f"Created key pair: {key_name}")
    
    return response


@mcp.tool()
def create_ebs_volume(availability_zone: str, size: int, volume_type: str = "gp3",
                     encrypted: bool = False, tags: List[Dict] = None,
                     region_name: str = "us-east-1") -> str:
    """
    Creates an EBS volume in the specified AWS region.
    
    Args:
        availability_zone: The availability zone to create the volume in.
        size: The size of the volume in GiB.
        volume_type: The volume type (default: 'gp3').
        encrypted: Whether to encrypt the volume (default: False).
        tags: List of tags to apply to the volume (optional).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The ID of the created EBS volume.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {
        'AvailabilityZone': availability_zone,
        'Size': size,
        'VolumeType': volume_type,
        'Encrypted': encrypted
    }
    
    if tags:
        params['TagSpecifications'] = [
            {
                'ResourceType': 'volume',
                'Tags': tags
            }
        ]
    
    # Use the resource creator to create the EBS volume
    response = resource_creator.create_resource('ebs_volume', params)
    
    # Extract the volume ID
    volume_id = response['VolumeId']
    logger.info(f"Created EBS volume: {volume_id} in zone: {availability_zone}")
    
    return volume_id


@mcp.tool()
def create_s3_bucket(bucket_name: str, cors_configuration: Dict = None, 
                    bucket_policy: str = None, website_configuration: Dict = None,
                    lifecycle_configuration: Dict = None, tags: Dict = None,
                    region_name: str = "us-east-1") -> str:
    """
    Creates an S3 bucket in the specified AWS region.
    
    Args:
        bucket_name: The name for the S3 bucket.
        cors_configuration: CORS configuration (optional).
        bucket_policy: Bucket policy as a JSON string (optional).
        website_configuration: Website configuration (optional).
        lifecycle_configuration: Lifecycle configuration (optional).
        tags: Dictionary of tags for the bucket (optional).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The name of the created S3 bucket.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {
        'BucketName': bucket_name
    }
    
    if cors_configuration:
        params['CorsConfiguration'] = cors_configuration
    
    if bucket_policy:
        params['BucketPolicy'] = bucket_policy
    
    if website_configuration:
        params['WebsiteConfiguration'] = website_configuration
    
    if lifecycle_configuration:
        params['LifecycleConfiguration'] = lifecycle_configuration
    
    if tags:
        params['Tags'] = tags
    
    # Use the resource creator to create the S3 bucket
    resource_creator.create_resource('s3_bucket', params)
    logger.info(f"Created S3 bucket: {bucket_name} in region: {region_name}")
    
    return bucket_name


@mcp.tool()
def create_rds_instance(db_instance_identifier: str, db_instance_class: str,
                       engine: str, allocated_storage: int, master_username: str,
                       master_password: str, vpc_security_group_ids: List[str] = None,
                       availability_zone: str = None, multi_az: bool = False,
                       tags: List[Dict] = None, region_name: str = "us-east-1") -> str:
    """
    Creates an RDS database instance in the specified AWS region.
    
    Args:
        db_instance_identifier: Identifier for the DB instance.
        db_instance_class: The compute and memory capacity class (e.g., 'db.t3.micro').
        engine: Database engine to use (e.g., 'mysql', 'postgres').
        allocated_storage: Storage size in gibibytes (GiB).
        master_username: Master username for the database.
        master_password: Master password for the database.
        vpc_security_group_ids: List of VPC security group IDs (optional).
        availability_zone: The availability zone to create the instance in (optional).
        multi_az: Whether to create a multi-AZ deployment (default: False).
        tags: List of tags to apply to the instance (optional).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The identifier of the created RDS instance.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {
        'DBInstanceIdentifier': db_instance_identifier,
        'DBInstanceClass': db_instance_class,
        'Engine': engine,
        'AllocatedStorage': allocated_storage,
        'MasterUsername': master_username,
        'MasterUserPassword': master_password,
        'MultiAZ': multi_az
    }
    
    if vpc_security_group_ids:
        params['VpcSecurityGroupIds'] = vpc_security_group_ids
    
    if availability_zone:
        params['AvailabilityZone'] = availability_zone
    
    if tags:
        params['Tags'] = tags
    
    # Use the resource creator to create the RDS instance
    resource_creator.create_resource('rds_instance', params)
    logger.info(f"Created RDS instance: {db_instance_identifier} in region: {region_name}")
    
    return db_instance_identifier


@mcp.tool()
def create_rds_snapshot(db_instance_id: str, snapshot_id: str, 
                       region_name: str = "us-east-1") -> str:
    """
    Creates a snapshot of an RDS database instance.
    
    Args:
        db_instance_id: The ID of the RDS instance to snapshot.
        snapshot_id: The ID to give the new snapshot.
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The ID of the created snapshot.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {
        'DBInstanceIdentifier': db_instance_id,
        'DBSnapshotIdentifier': snapshot_id
    }
    
    # Use the resource creator to create the snapshot
    resource_creator.create_resource('rds_snapshot', params)
    logger.info(f"Created RDS snapshot: {snapshot_id} from instance: {db_instance_id}")
    
    return snapshot_id


@mcp.tool()
def create_vpc(cidr_block: str, name: str = None, enable_dns_support: bool = True,
              enable_dns_hostnames: bool = True, instance_tenancy: str = "default",
              region_name: str = "us-east-1") -> str:
    """
    Creates a VPC in the specified AWS region.
    
    Args:
        cidr_block: The CIDR block for the VPC (e.g., '10.0.0.0/16').
        name: Name tag for the VPC (optional).
        enable_dns_support: Whether to enable DNS resolution (default: True).
        enable_dns_hostnames: Whether to enable DNS hostnames (default: True).
        instance_tenancy: The allowed tenancy of instances launched into the VPC (default: 'default').
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The ID of the created VPC.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {
        'CidrBlock': cidr_block,
        'EnableDnsSupport': enable_dns_support,
        'EnableDnsHostnames': enable_dns_hostnames,
        'InstanceTenancy': instance_tenancy
    }
    
    if name:
        params['Name'] = name
    
    # Use the resource creator to create the VPC
    response = resource_creator.create_resource('vpc', params)
    vpc_id = response['Vpc']['VpcId']
    logger.info(f"Created VPC: {vpc_id} with CIDR block: {cidr_block}")
    
    return vpc_id


@mcp.tool()
def create_subnet(vpc_id: str, cidr_block: str, availability_zone: str = None,
                 name: str = None, map_public_ip_on_launch: bool = False,
                 region_name: str = "us-east-1") -> str:
    """
    Creates a subnet in a VPC in the specified AWS region.
    
    Args:
        vpc_id: The ID of the VPC to create the subnet in.
        cidr_block: The CIDR block for the subnet.
        availability_zone: The availability zone to create the subnet in (optional).
        name: Name tag for the subnet (optional).
        map_public_ip_on_launch: Whether to auto-assign public IPs (default: False).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The ID of the created subnet.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {
        'VpcId': vpc_id,
        'CidrBlock': cidr_block,
        'MapPublicIpOnLaunch': map_public_ip_on_launch
    }
    
    if availability_zone:
        params['AvailabilityZone'] = availability_zone
    
    if name:
        params['Name'] = name
    
    # Use the resource creator to create the subnet
    response = resource_creator.create_resource('subnet', params)
    subnet_id = response['Subnet']['SubnetId']
    logger.info(f"Created subnet: {subnet_id} in VPC: {vpc_id}")
    
    return subnet_id


@mcp.tool()
def create_internet_gateway(vpc_id: str = None, name: str = None,
                          region_name: str = "us-east-1") -> str:
    """
    Creates an internet gateway and optionally attaches it to a VPC.
    
    Args:
        vpc_id: The ID of the VPC to attach the internet gateway to (optional).
        name: Name tag for the internet gateway (optional).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The ID of the created internet gateway.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {}
    
    if vpc_id:
        params['VpcId'] = vpc_id
    
    if name:
        params['Name'] = name
    
    # Use the resource creator to create the internet gateway
    response = resource_creator.create_resource('internet_gateway', params)
    igw_id = response['InternetGateway']['InternetGatewayId']
    logger.info(f"Created internet gateway: {igw_id}")
    
    return igw_id


@mcp.tool()
def create_route_table(vpc_id: str, routes: List[Dict] = None, subnet_ids: List[str] = None,
                      name: str = None, region_name: str = "us-east-1") -> str:
    """
    Creates a route table in a VPC in the specified AWS region.
    
    Args:
        vpc_id: The ID of the VPC to create the route table in.
        routes: List of routes to add to the route table (optional).
        subnet_ids: List of subnet IDs to associate with the route table (optional).
        name: Name tag for the route table (optional).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The ID of the created route table.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {
        'VpcId': vpc_id
    }
    
    if routes:
        params['Routes'] = routes
    
    if subnet_ids:
        params['SubnetIds'] = subnet_ids
    
    if name:
        params['Name'] = name
    
    # Use the resource creator to create the route table
    response = resource_creator.create_resource('route_table', params)
    route_table_id = response['RouteTable']['RouteTableId']
    logger.info(f"Created route table: {route_table_id} in VPC: {vpc_id}")
    
    return route_table_id


@mcp.tool()
def create_iam_user(username: str, path: str = "/", tags: List[Dict] = None,
                   policy_arns: List[str] = None, create_access_key: bool = False,
                   region_name: str = "us-east-1") -> Dict[str, Any]:
    """
    Creates an IAM user in the specified AWS account.
    
    Args:
        username: The name for the new IAM user.
        path: Path for the user (default: '/').
        tags: List of tags to apply to the user (optional).
        policy_arns: List of policy ARNs to attach to the user (optional).
        create_access_key: Whether to create an access key for the user (default: False).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        Dictionary with user information and access keys if requested.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {
        'UserName': username,
        'Path': path,
        'CreateAccessKey': create_access_key
    }
    
    if tags:
        params['Tags'] = tags
    
    if policy_arns:
        params['PolicyArns'] = policy_arns
    
    # Use the resource creator to create the IAM user
    response = resource_creator.create_resource('iam_user', params)
    logger.info(f"Created IAM user: {username}")
    
    result = {
        'Username': username,
        'UserId': response['User']['UserId'],
        'Arn': response['User']['Arn']
    }
    
    if create_access_key and 'AccessKey' in response:
        result['AccessKeyId'] = response['AccessKey']['AccessKeyId']
        result['SecretAccessKey'] = response['AccessKey']['SecretAccessKey']
        logger.info(f"Created access key for user: {username}")
    
    return result


@mcp.tool()
def create_iam_role(role_name: str, assume_role_policy_document: str,
                   description: str = "", path: str = "/", max_session_duration: int = 3600,
                   tags: List[Dict] = None, policy_arns: List[str] = None,
                   region_name: str = "us-east-1") -> str:
    """
    Creates an IAM role in the specified AWS account.
    
    Args:
        role_name: The name for the new IAM role.
        assume_role_policy_document: JSON trust policy document.
        description: Description for the role (optional).
        path: Path for the role (default: '/').
        max_session_duration: Maximum session duration in seconds (default: 3600).
        tags: List of tags to apply to the role (optional).
        policy_arns: List of policy ARNs to attach to the role (optional).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The ARN of the created IAM role.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {
        'RoleName': role_name,
        'AssumeRolePolicyDocument': assume_role_policy_document,
        'Description': description,
        'Path': path,
        'MaxSessionDuration': max_session_duration
    }
    
    if tags:
        params['Tags'] = tags
    
    if policy_arns:
        params['PolicyArns'] = policy_arns
    
    # Use the resource creator to create the IAM role
    response = resource_creator.create_resource('iam_role', params)
    role_arn = response['Role']['Arn']
    logger.info(f"Created IAM role: {role_name} with ARN: {role_arn}")
    
    return role_arn


@mcp.tool()
def create_iam_policy(policy_name: str, policy_document: str, description: str = "",
                     path: str = "/", region_name: str = "us-east-1") -> str:
    """
    Creates an IAM policy in the specified AWS account.
    
    Args:
        policy_name: The name for the new IAM policy.
        policy_document: JSON policy document.
        description: Description for the policy (optional).
        path: Path for the policy (default: '/').
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The ARN of the created IAM policy.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {
        'PolicyName': policy_name,
        'PolicyDocument': policy_document,
        'Description': description,
        'Path': path
    }
    
    # Use the resource creator to create the IAM policy
    response = resource_creator.create_resource('iam_policy', params)
    policy_arn = response['Policy']['Arn']
    logger.info(f"Created IAM policy: {policy_name} with ARN: {policy_arn}")
    
    return policy_arn


@mcp.tool()
def create_lambda_function(function_name: str, runtime: str, handler: str, role: str,
                          code: Dict, description: str = "", timeout: int = 3,
                          memory_size: int = 128, environment: Dict = None,
                          tags: Dict = None, region_name: str = "us-east-1") -> str:
    """
    Creates a Lambda function in the specified AWS region.
    
    Args:
        function_name: The name for the Lambda function.
        runtime: The runtime environment for the function (e.g., 'python3.9').
        handler: The function within your code that Lambda calls to begin execution.
        role: The ARN of the IAM role that Lambda assumes when it executes your function.
        code: Dictionary containing function code (S3Bucket/S3Key or ZipFile).
        description: Description for the function (optional).
        timeout: Function execution timeout in seconds (default: 3).
        memory_size: Function memory size in MB (default: 128).
        environment: Environment variables for the function (optional).
        tags: Dictionary of tags for the function (optional).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The ARN of the created Lambda function.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {
        'FunctionName': function_name,
        'Runtime': runtime,
        'Handler': handler,
        'Role': role,
        'Code': code,
        'Description': description,
        'Timeout': timeout,
        'MemorySize': memory_size
    }
    
    if environment:
        params['Environment'] = {'Variables': environment}
    
    if tags:
        params['Tags'] = tags
    
    # Use the resource creator to create the Lambda function
    response = resource_creator.create_resource('lambda_function', params)
    function_arn = response['FunctionArn']
    logger.info(f"Created Lambda function: {function_name} with ARN: {function_arn}")
    
    return function_arn


@mcp.tool()
def create_dynamodb_table(table_name: str, key_schema: List[Dict],
                         attribute_definitions: List[Dict],
                         provisioned_throughput: Dict = None,
                         billing_mode: str = "PROVISIONED",
                         tags: List[Dict] = None,
                         region_name: str = "us-east-1") -> str:
    """
    Creates a DynamoDB table in the specified AWS region.
    
    Args:
        table_name: The name for the DynamoDB table.
        key_schema: List specifying the primary key attributes.
        attribute_definitions: List of attribute definitions.
        provisioned_throughput: Provisioned throughput settings (required if billing_mode is 'PROVISIONED').
        billing_mode: Billing mode ('PROVISIONED' or 'PAY_PER_REQUEST') (default: 'PROVISIONED').
        tags: List of tags to apply to the table (optional).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The name of the created DynamoDB table.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {
        'TableName': table_name,
        'KeySchema': key_schema,
        'AttributeDefinitions': attribute_definitions,
        'BillingMode': billing_mode
    }
    
    if billing_mode == "PROVISIONED":
        if not provisioned_throughput:
            provisioned_throughput = {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        params['ProvisionedThroughput'] = provisioned_throughput
    
    if tags:
        params['Tags'] = tags
    
    # Use the resource creator to create the DynamoDB table
    resource_creator.create_resource('dynamodb_table', params)
    logger.info(f"Created DynamoDB table: {table_name} in region: {region_name}")
    
    return table_name


@mcp.tool()
def create_cloudfront_distribution(origin_domain_name: str, default_root_object: str = "index.html",
                                 enabled: bool = True, price_class: str = "PriceClass_100",
                                 aliases: List[str] = None, comment: str = "",
                                 region_name: str = "us-east-1") -> str:
    """
    Creates a CloudFront distribution in the specified AWS region.
    
    Args:
        origin_domain_name: The domain name for the distribution origin.
        default_root_object: The default root object (default: 'index.html').
        enabled: Whether the distribution is enabled (default: True).
        price_class: The price class for the distribution (default: 'PriceClass_100').
        aliases: List of CNAME aliases for the distribution (optional).
        comment: Comment for the distribution (optional).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The ID of the created CloudFront distribution.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    distribution_config = {
        'CallerReference': str(datetime.now().timestamp()),
        'DefaultRootObject': default_root_object,
        'Origins': {
            'Quantity': 1,
            'Items': [
                {
                    'Id': 'defaultOrigin',
                    'DomainName': origin_domain_name,
                    'CustomOriginConfig': {
                        'HTTPPort': 80,
                        'HTTPSPort': 443,
                        'OriginProtocolPolicy': 'match-viewer',
                        'OriginSslProtocols': {
                            'Quantity': 1,
                            'Items': ['TLSv1.2']
                        }
                    }
                }
            ]
        },
        'DefaultCacheBehavior': {
            'TargetOriginId': 'defaultOrigin',
            'ViewerProtocolPolicy': 'redirect-to-https',
            'AllowedMethods': {
                'Quantity': 2,
                'Items': ['GET', 'HEAD'],
                'CachedMethods': {
                    'Quantity': 2,
                    'Items': ['GET', 'HEAD']
                }
            },
            'ForwardedValues': {
                'QueryString': False,
                'Cookies': {
                    'Forward': 'none'
                }
            },
            'MinTTL': 0,
            'DefaultTTL': 86400,
            'MaxTTL': 31536000
        },
        'Enabled': enabled,
        'PriceClass': price_class,
        'Comment': comment
    }
    
    if aliases:
        distribution_config['Aliases'] = {
            'Quantity': len(aliases),
            'Items': aliases
        }
    
    params = {
        'DistributionConfig': distribution_config
    }
    
    # Use the resource creator to create the CloudFront distribution
    response = resource_creator.create_resource('cloudfront_distribution', params)
    distribution_id = response['Distribution']['Id']
    logger.info(f"Created CloudFront distribution: {distribution_id}")
    
    return distribution_id


@mcp.tool()
def create_sns_topic(name: str, display_name: str = None, tags: List[Dict] = None,
                    region_name: str = "us-east-1") -> str:
    """
    Creates an SNS topic in the specified AWS region.
    
    Args:
        name: The name for the SNS topic.
        display_name: Display name for the topic (optional).
        tags: List of tags to apply to the topic (optional).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The ARN of the created SNS topic.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    params = {
        'Name': name
    }
    
    if display_name:
        params['DisplayName'] = display_name
    
    if tags:
        params['Tags'] = tags
    
    # Use the resource creator to create the SNS topic
    response = resource_creator.create_resource('sns_topic', params)
    topic_arn = response['TopicArn']
    logger.info(f"Created SNS topic: {name} with ARN: {topic_arn}")
    
    return topic_arn


@mcp.tool()
def create_sqs_queue(queue_name: str, delay_seconds: int = 0, 
                    message_retention_period: int = 345600,
                    visibility_timeout: int = 30,
                    content_based_deduplication: bool = False,
                    fifo_queue: bool = False,
                    tags: Dict[str, str] = None,
                    region_name: str = "us-east-1") -> str:
    """
    Creates an SQS queue in the specified AWS region.
    
    Args:
        queue_name: The name for the SQS queue.
        delay_seconds: The time in seconds that the delivery of all messages is delayed (default: 0).
        message_retention_period: The time in seconds that messages are kept in the queue (default: 345600).
        visibility_timeout: The visibility timeout for the queue in seconds (default: 30).
        content_based_deduplication: Whether to enable content-based deduplication for FIFO queues (default: False).
        fifo_queue: Whether to create a FIFO queue (default: False).
        tags: Dictionary of tags to apply to the queue (optional).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        The URL of the created SQS queue.
    """
    resource_creator = AWSResourceCreator(region_name=region_name)
    
    # Adjust queue name for FIFO if needed
    if fifo_queue and not queue_name.endswith('.fifo'):
        queue_name = f"{queue_name}.fifo"
    
    params = {
        'QueueName': queue_name,
        'Attributes': {
            'DelaySeconds': str(delay_seconds),
            'MessageRetentionPeriod': str(message_retention_period),
            'VisibilityTimeout': str(visibility_timeout),
        }
    }
    
    if fifo_queue:
        params['Attributes']['FifoQueue'] = 'true'
        
        if content_based_deduplication:
            params['Attributes']['ContentBasedDeduplication'] = 'true'
    
    if tags:
        params['tags'] = tags
    
    # Use the resource creator to create the SQS queue
    response = resource_creator.create_resource('sqs_queue', params)
    queue_url = response['QueueUrl']
    logger.info(f"Created SQS queue: {queue_name} with URL: {queue_url}")
    
    return queue_url


# Additional MCP tools for resource management

@mcp.tool()
def attach_ebs_volume(volume_id: str, instance_id: str, device: str,
                     region_name: str = "us-east-1") -> bool:
    """
    Attaches an EBS volume to an EC2 instance.
    
    Args:
        volume_id: The ID of the EBS volume to attach.
        instance_id: The ID of the EC2 instance to attach to.
        device: The device name to expose to the instance (e.g., '/dev/sdh').
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        session = boto3.Session(region_name=region_name)
        ec2_client = session.client('ec2')
        
        response = ec2_client.attach_volume(
            VolumeId=volume_id,
            InstanceId=instance_id,
            Device=device
        )
        
        logger.info(f"Attached volume {volume_id} to instance {instance_id} as device {device}")
        return True
    except Exception as e:
        logger.error(f"Failed to attach volume: {e}")
        return False


@mcp.tool()
def detach_ebs_volume(volume_id: str, force: bool = False, 
                     region_name: str = "us-east-1") -> bool:
    """
    Detaches an EBS volume from an EC2 instance.
    
    Args:
        volume_id: The ID of the EBS volume to detach.
        force: Force detachment if previous detachment attempt failed (default: False).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        session = boto3.Session(region_name=region_name)
        ec2_client = session.client('ec2')
        
        response = ec2_client.detach_volume(
            VolumeId=volume_id,
            Force=force
        )
        
        logger.info(f"Detached volume {volume_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to detach volume: {e}")
        return False


@mcp.tool()
def terminate_ec2_instance(instance_id: str, region_name: str = "us-east-1") -> bool:
    """
    Terminates an EC2 instance.
    
    Args:
        instance_id: The ID of the EC2 instance to terminate.
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        session = boto3.Session(region_name=region_name)
        ec2_client = session.client('ec2')
        
        response = ec2_client.terminate_instances(
            InstanceIds=[instance_id]
        )
        
        logger.info(f"Terminated EC2 instance: {instance_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to terminate instance: {e}")
        return False


@mcp.tool()
def delete_s3_bucket(bucket_name: str, force: bool = False, 
                    region_name: str = "us-east-1") -> bool:
    """
    Deletes an S3 bucket.
    
    Args:
        bucket_name: The name of the S3 bucket to delete.
        force: Whether to force deletion of non-empty buckets (default: False).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        session = boto3.Session(region_name=region_name)
        s3_client = session.client('s3')
        
        # If force is True, delete all objects first
        if force:
            s3_resource = session.resource('s3')
            bucket = s3_resource.Bucket(bucket_name)
            bucket.objects.all().delete()
            
            # Delete any versioned objects if the bucket has versioning enabled
            versions = bucket.object_versions.all()
            for version in versions:
                version.delete()
        
        # Delete the bucket
        s3_client.delete_bucket(Bucket=bucket_name)
        
        logger.info(f"Deleted S3 bucket: {bucket_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete bucket: {e}")
        return False


@mcp.tool()
def delete_rds_instance(db_instance_identifier: str, skip_final_snapshot: bool = True,
                       final_snapshot_identifier: str = None,
                       region_name: str = "us-east-1") -> bool:
    """
    Deletes an RDS database instance.
    
    Args:
        db_instance_identifier: The identifier of the RDS instance to delete.
        skip_final_snapshot: Whether to skip creating a final snapshot (default: True).
        final_snapshot_identifier: The identifier to use for the final snapshot (required if skip_final_snapshot is False).
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        session = boto3.Session(region_name=region_name)
        rds_client = session.client('rds')
        
        params = {
            'DBInstanceIdentifier': db_instance_identifier,
            'SkipFinalSnapshot': skip_final_snapshot
        }
        
        if not skip_final_snapshot:
            if not final_snapshot_identifier:
                final_snapshot_identifier = f"{db_instance_identifier}-final-{datetime.now().strftime('%Y-%m-%d-%H-%M')}"
            params['FinalDBSnapshotIdentifier'] = final_snapshot_identifier
        
        rds_client.delete_db_instance(**params)
        
        logger.info(f"Deleted RDS instance: {db_instance_identifier}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete RDS instance: {e}")
        return False


@mcp.tool()
def delete_vpc(vpc_id: str, region_name: str = "us-east-1") -> bool:
    """
    Deletes a VPC.
    
    Args:
        vpc_id: The ID of the VPC to delete.
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        session = boto3.Session(region_name=region_name)
        ec2_client = session.client('ec2')
        
        ec2_client.delete_vpc(VpcId=vpc_id)
        
        logger.info(f"Deleted VPC: {vpc_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete VPC: {e}")
        return False


@mcp.tool()
def delete_iam_user(username: str, region_name: str = "us-east-1") -> bool:
    """
    Deletes an IAM user.
    
    Args:
        username: The name of the IAM user to delete.
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        session = boto3.Session(region_name=region_name)
        iam_client = session.client('iam')
        
        # Delete access keys
        try:
            access_keys = iam_client.list_access_keys(UserName=username)
            for key in access_keys.get('AccessKeyMetadata', []):
                iam_client.delete_access_key(
                    UserName=username,
                    AccessKeyId=key['AccessKeyId']
                )
                logger.info(f"Deleted access key {key['AccessKeyId']} for user: {username}")
        except Exception as e:
            logger.warning(f"Error deleting access keys for user {username}: {e}")
        
        # Detach policies
        try:
            attached_policies = iam_client.list_attached_user_policies(UserName=username)
            for policy in attached_policies.get('AttachedPolicies', []):
                iam_client.detach_user_policy(
                    UserName=username,
                    PolicyArn=policy['PolicyArn']
                )
                logger.info(f"Detached policy {policy['PolicyArn']} from user: {username}")
        except Exception as e:
            logger.warning(f"Error detaching policies from user {username}: {e}")
        
        # Delete the user
        iam_client.delete_user(UserName=username)
        
        logger.info(f"Deleted IAM user: {username}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete IAM user: {e}")
        return False


@mcp.tool()
def delete_security_group(security_group_id: str, region_name: str = "us-east-1") -> bool:
    """
    Deletes a security group.
    
    Args:
        security_group_id: The ID of the security group to delete.
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        session = boto3.Session(region_name=region_name)
        ec2_client = session.client('ec2')
        
        ec2_client.delete_security_group(GroupId=security_group_id)
        
        logger.info(f"Deleted security group: {security_group_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete security group: {e}")
        return False


@mcp.tool()
def delete_lambda_function(function_name: str, region_name: str = "us-east-1") -> bool:
    """
    Deletes a Lambda function.
    
    Args:
        function_name: The name of the Lambda function to delete.
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        session = boto3.Session(region_name=region_name)
        lambda_client = session.client('lambda')
        
        lambda_client.delete_function(FunctionName=function_name)
        
        logger.info(f"Deleted Lambda function: {function_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete Lambda function: {e}")
        return False


@mcp.tool()
def delete_dynamodb_table(table_name: str, region_name: str = "us-east-1") -> bool:
    """
    Deletes a DynamoDB table.
    
    Args:
        table_name: The name of the DynamoDB table to delete.
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        session = boto3.Session(region_name=region_name)
        dynamodb_client = session.client('dynamodb')
        
        dynamodb_client.delete_table(TableName=table_name)
        
        logger.info(f"Deleted DynamoDB table: {table_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete DynamoDB table: {e}")
        return False


@mcp.tool()
def create_aws_resource(resource_type: str, params: Dict[str, Any], 
                       region_name: str = "us-east-1") -> Dict[str, Any]:
    """
    Creates any supported AWS resource using the AWSResourceCreator.
    
    Args:
        resource_type: The type of resource to create (e.g., 'ec2_instance', 's3_bucket', etc.).
        params: Dictionary of parameters for the resource creation.
        region_name: The name of the AWS region (default: 'us-east-1').
        
    Returns:
        Response from the AWS API.
    """
    try:
        resource_creator = AWSResourceCreator(region_name=region_name)
        response = resource_creator.create_resource(resource_type, params)
        logger.info(f"Created {resource_type} in region: {region_name}")
        return response
    except Exception as e:
        logger.error(f"Failed to create {resource_type}: {e}")
        raise
