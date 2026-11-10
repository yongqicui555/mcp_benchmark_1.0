import boto3
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AWSResourceCreator:
    """
    A utility class for creating various AWS resources using boto3.
    """
    
    def __init__(self, region_name: str = 'us-east-1', profile_name: Optional[str] = None):
        """
        Initialize the AWSResourceCreator with AWS credentials.
        
        Args:
            region_name: AWS region to create resources in
            profile_name: AWS CLI profile name to use (optional)
        """
        self.region_name = region_name
        
        # Create a boto3 session
        if profile_name:
            self.session = boto3.Session(profile_name=profile_name, region_name=region_name)
        else:
            self.session = boto3.Session(region_name=region_name)
        
        # Dictionary of service clients
        self.clients = {}
        
    def _get_client(self, service_name: str) -> boto3.client:
        """
        Get or create a boto3 client for the specified AWS service.
        
        Args:
            service_name: Name of the AWS service (e.g., 'ec2', 's3', 'rds')
            
        Returns:
            boto3.client: A boto3 client for the service
        """
        if service_name not in self.clients:
            self.clients[service_name] = self.session.client(service_name)
        return self.clients[service_name]
    
    def create_resource(self, resource_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an AWS resource of the specified type with the given parameters.
        
        Args:
            resource_type: Type of resource to create (e.g., 'ec2_instance', 's3_bucket')
            params: Dictionary of parameters for resource creation
            
        Returns:
            Dict[str, Any]: Response from the AWS API containing created resource details
            
        Raises:
            ValueError: If the resource_type is not supported
            ClientError: If AWS API returns an error
        """
        # Map resource types to creation methods
        resource_handlers = {
            # EC2 resources
            'ec2_instance': self._create_ec2_instance,
            'ec2_security_group': self._create_security_group,
            'ec2_key_pair': self._create_key_pair,
            'ec2_volume': self._create_ebs_volume,
            
            # S3 resources
            's3_bucket': self._create_s3_bucket,
            
            # RDS resources
            'rds_instance': self._create_rds_instance,
            'rds_snapshot': self._create_rds_snapshot,
            
            # VPC resources
            'vpc': self._create_vpc,
            'subnet': self._create_subnet,
            'internet_gateway': self._create_internet_gateway,
            'route_table': self._create_route_table,
            
            # IAM resources
            'iam_user': self._create_iam_user,
            'iam_role': self._create_iam_role,
            'iam_policy': self._create_iam_policy,
            
            # Other resources
            'lambda_function': self._create_lambda_function,
            'dynamodb_table': self._create_dynamodb_table,
            'cloudfront_distribution': self._create_cloudfront_distribution,
            'sns_topic': self._create_sns_topic,
            'sqs_queue': self._create_sqs_queue,
        }
        
        # Check if the resource type is supported
        if resource_type not in resource_handlers:
            supported_types = list(resource_handlers.keys())
            raise ValueError(f"Unsupported resource type: {resource_type}. Supported types: {supported_types}")
        
        # Call the appropriate handler function
        try:
            logger.info(f"Creating {resource_type} with parameters: {params}")
            response = resource_handlers[resource_type](params)
            logger.info(f"Successfully created {resource_type}")
            return response
        except ClientError as e:
            logger.error(f"Failed to create {resource_type}: {e}")
            raise
    
    # EC2 Resource Handlers
    
    def _create_ec2_instance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an EC2 instance."""
        client = self._get_client('ec2')
        
        # Set default values for required parameters if not provided
        if 'MaxCount' not in params:
            params['MaxCount'] = 1
        if 'MinCount' not in params:
            params['MinCount'] = 1
            
        response = client.run_instances(**params)
        
        # Tag the instance if name is provided
        if 'Name' in params and response['Instances']:
            instance_id = response['Instances'][0]['InstanceId']
            client.create_tags(
                Resources=[instance_id],
                Tags=[{'Key': 'Name', 'Value': params['Name']}]
            )
            
        return response
    
    def _create_security_group(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an EC2 security group."""
        client = self._get_client('ec2')
        
        # Create security group
        create_params = {
            'Description': params.get('Description', 'Security Group created by AWSResourceCreator'),
            'GroupName': params['GroupName']
        }
        
        if 'VpcId' in params:
            create_params['VpcId'] = params['VpcId']
            
        response = client.create_security_group(**create_params)
        
        # Add ingress rules if provided
        security_group_id = response['GroupId']
        if 'IngressRules' in params:
            client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=params['IngressRules']
            )
            
        # Add egress rules if provided
        if 'EgressRules' in params:
            client.authorize_security_group_egress(
                GroupId=security_group_id,
                IpPermissions=params['EgressRules']
            )
            
        # Add tags if provided
        if 'Tags' in params:
            client.create_tags(
                Resources=[security_group_id],
                Tags=params['Tags']
            )
            
        return response
    
    def _create_key_pair(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an EC2 key pair."""
        client = self._get_client('ec2')
        return client.create_key_pair(**params)
    
    def _create_ebs_volume(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an EBS volume."""
        client = self._get_client('ec2')
        return client.create_volume(**params)
    
    # S3 Resource Handlers
    
    def _create_s3_bucket(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an S3 bucket."""
        client = self._get_client('s3')
        
        # Extract bucket name
        bucket_name = params.pop('BucketName')
        
        # Set up create_bucket parameters
        create_params = {'Bucket': bucket_name}
        
        # Add region configuration if not using us-east-1
        if self.region_name != 'us-east-1':
            create_params['CreateBucketConfiguration'] = {
                'LocationConstraint': self.region_name
            }
            
        # Create the bucket
        response = client.create_bucket(**create_params)
        
        # Configure bucket properties if specified
        if 'CorsConfiguration' in params:
            client.put_bucket_cors(
                Bucket=bucket_name,
                CORSConfiguration=params['CorsConfiguration']
            )
            
        if 'BucketPolicy' in params:
            client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=params['BucketPolicy']
            )
            
        if 'WebsiteConfiguration' in params:
            client.put_bucket_website(
                Bucket=bucket_name,
                WebsiteConfiguration=params['WebsiteConfiguration']
            )
            
        if 'LifecycleConfiguration' in params:
            client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=params['LifecycleConfiguration']
            )
            
        # Add bucket tags if specified
        if 'Tags' in params:
            tag_set = [{'Key': k, 'Value': v} for k, v in params['Tags'].items()]
            client.put_bucket_tagging(
                Bucket=bucket_name,
                Tagging={'TagSet': tag_set}
            )
            
        return response
    
    # RDS Resource Handlers
    
    def _create_rds_instance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an RDS database instance."""
        client = self._get_client('rds')
        return client.create_db_instance(**params)
    
    def _create_rds_snapshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an RDS database snapshot."""
        client = self._get_client('rds')
        return client.create_db_snapshot(**params)
    
    # VPC Resource Handlers
    
    def _create_vpc(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a VPC."""
        client = self._get_client('ec2')
        
        # Create VPC
        response = client.create_vpc(
            CidrBlock=params['CidrBlock'],
            AmazonProvidedIpv6CidrBlock=params.get('AmazonProvidedIpv6CidrBlock', False),
            InstanceTenancy=params.get('InstanceTenancy', 'default')
        )
        
        vpc_id = response['Vpc']['VpcId']
        
        # Add name tag if provided
        if 'Name' in params:
            client.create_tags(
                Resources=[vpc_id],
                Tags=[{'Key': 'Name', 'Value': params['Name']}]
            )
            
        # Enable DNS support and hostnames if requested
        if params.get('EnableDnsSupport', True):
            client.modify_vpc_attribute(
                VpcId=vpc_id,
                EnableDnsSupport={'Value': True}
            )
            
        if params.get('EnableDnsHostnames', True):
            client.modify_vpc_attribute(
                VpcId=vpc_id,
                EnableDnsHostnames={'Value': True}
            )
            
        return response
    
    def _create_subnet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a subnet in a VPC."""
        client = self._get_client('ec2')
        
        # Create subnet
        response = client.create_subnet(
            VpcId=params['VpcId'],
            CidrBlock=params['CidrBlock'],
            AvailabilityZone=params.get('AvailabilityZone')
        )
        
        subnet_id = response['Subnet']['SubnetId']
        
        # Add name tag if provided
        if 'Name' in params:
            client.create_tags(
                Resources=[subnet_id],
                Tags=[{'Key': 'Name', 'Value': params['Name']}]
            )
            
        # Configure public IP auto-assignment if specified
        if 'MapPublicIpOnLaunch' in params:
            client.modify_subnet_attribute(
                SubnetId=subnet_id,
                MapPublicIpOnLaunch={'Value': params['MapPublicIpOnLaunch']}
            )
            
        return response
    
    def _create_internet_gateway(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an internet gateway and optionally attach it to a VPC."""
        client = self._get_client('ec2')
        
        # Create internet gateway
        response = client.create_internet_gateway()
        
        igw_id = response['InternetGateway']['InternetGatewayId']
        
        # Add name tag if provided
        if 'Name' in params:
            client.create_tags(
                Resources=[igw_id],
                Tags=[{'Key': 'Name', 'Value': params['Name']}]
            )
            
        # Attach to VPC if specified
        if 'VpcId' in params:
            client.attach_internet_gateway(
                InternetGatewayId=igw_id,
                VpcId=params['VpcId']
            )
            
        return response
    
    def _create_route_table(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a route table in a VPC."""
        client = self._get_client('ec2')
        
        # Create route table
        response = client.create_route_table(VpcId=params['VpcId'])
        
        route_table_id = response['RouteTable']['RouteTableId']
        
        # Add name tag if provided
        if 'Name' in params:
            client.create_tags(
                Resources=[route_table_id],
                Tags=[{'Key': 'Name', 'Value': params['Name']}]
            )
            
        # Add routes if provided
        if 'Routes' in params:
            for route in params['Routes']:
                route_params = {'RouteTableId': route_table_id}
                route_params.update(route)
                client.create_route(**route_params)
                
        # Associate with subnets if provided
        if 'SubnetIds' in params:
            for subnet_id in params['SubnetIds']:
                client.associate_route_table(
                    RouteTableId=route_table_id,
                    SubnetId=subnet_id
                )
                
        return response
    
    # IAM Resource Handlers
    
    def _create_iam_user(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an IAM user."""
        client = self._get_client('iam')
        
        # Create user
        response = client.create_user(
            UserName=params['UserName'],
            Path=params.get('Path', '/'),
            Tags=params.get('Tags', [])
        )
        
        user_name = params['UserName']
        
        # Attach policies if provided
        if 'PolicyArns' in params:
            for policy_arn in params['PolicyArns']:
                client.attach_user_policy(
                    UserName=user_name,
                    PolicyArn=policy_arn
                )
                
        # Create access key if requested
        if params.get('CreateAccessKey', False):
            access_key_response = client.create_access_key(UserName=user_name)
            response['AccessKey'] = access_key_response['AccessKey']
            
        return response
    
    def _create_iam_role(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an IAM role."""
        client = self._get_client('iam')
        
        # Create role
        response = client.create_role(
            RoleName=params['RoleName'],
            AssumeRolePolicyDocument=params['AssumeRolePolicyDocument'],
            Description=params.get('Description', ''),
            Path=params.get('Path', '/'),
            MaxSessionDuration=params.get('MaxSessionDuration', 3600),
            Tags=params.get('Tags', [])
        )
        
        role_name = params['RoleName']
        
        # Attach policies if provided
        if 'PolicyArns' in params:
            for policy_arn in params['PolicyArns']:
                client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy_arn
                )
                
        return response
    
    def _create_iam_policy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an IAM policy."""
        client = self._get_client('iam')
        return client.create_policy(
            PolicyName=params['PolicyName'],
            PolicyDocument=params['PolicyDocument'],
            Description=params.get('Description', ''),
            Path=params.get('Path', '/')
        )
    
    # Lambda Resource Handlers
    
    def _create_lambda_function(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Lambda function."""
        client = self._get_client('lambda')
        return client.create_function(**params)
    
    # DynamoDB Resource Handlers
    
    def _create_dynamodb_table(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a DynamoDB table."""
        client = self._get_client('dynamodb')
        return client.create_table(**params)
    
    # CloudFront Resource Handlers
    
    def _create_cloudfront_distribution(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a CloudFront distribution."""
        client = self._get_client('cloudfront')
        return client.create_distribution(**params)
    
    # SNS Resource Handlers
    
    def _create_sns_topic(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an SNS topic."""
        client = self._get_client('sns')
        return client.create_topic(**params)
    
    # SQS Resource Handlers
    
    def _create_sqs_queue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an SQS queue."""
        client = self._get_client('sqs')
        return client.create_queue(**params)