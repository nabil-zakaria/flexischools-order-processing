from aws_cdk import (
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_iam as iam,
    aws_ecr as ecr,
    aws_ecs as ecs,
    aws_sqs as sqs,
    aws_ecs_patterns as ecs_patterns,
)
from constructs import Construct
import os


class FlexischoolsStack(Stack):
    """Deploys the Flexischools Serverless Order Processing Stack"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a VPC
        vpc = ec2.Vpc(self, id="FlexischoolsVPC", max_azs=2)

        # Security Group for RDS
        rds_sg = ec2.SecurityGroup(
            self,
            id="RdsSecurityGroup",
            vpc=vpc,
            description="Allow PostgreSQL access",
            allow_all_outbound=True,
        )

        # Security Group for Fargate
        fargate_sg = ec2.SecurityGroup(self, id="FargateSecurityGroup", vpc=vpc)

        # Allow Fargate to connect to RDS on port 5432 (PostgreSQL)
        rds_sg.add_ingress_rule(fargate_sg, ec2.Port.tcp(5432), "Allow Fargate to connect to RDS")

        # Creates Credentials with a password generated and stored in Secrets Manager.
        db_secret = rds.Credentials.from_generated_secret("flexischoolsuser")

        # Create the RDS Instance
        db = rds.DatabaseInstance(
            self,
            id="FlexischoolsRdsInstance",
            instance_identifier="Flexischools-DB",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_17_2),
            vpc=vpc,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            allocated_storage=20,
            security_groups=[rds_sg],
            database_name="FlexischoolsDB",
            credentials=db_secret,
            multi_az=True,
            publicly_accessible=False,
            storage_encrypted=True,
        )

        # Create an SQS Dead Letter Queue to store orders that failed to be processed
        dlq = sqs.Queue(
            self,
            "FlexischoolsDeadLetterQueue",
            queue_name="Flexischools-DLQ",
            retention_period=Duration.days(14),
        )

        # Create SQS used for storing orders
        queue = sqs.Queue(
            self,
            id="FlexischoolsQueue",
            queue_name="Flexischools-orders-queue",
            visibility_timeout=Duration.seconds(300),
            dead_letter_queue=sqs.DeadLetterQueue(queue=dlq, max_receive_count=5),
        )

        # Create ECS Cluster
        cluster = ecs.Cluster(self, id="FlexischoolsCluster", cluster_name="Flexischools-cluster", vpc=vpc)

        # Create Docker Image
        image = ecs.ContainerImage.from_asset(
            directory=os.path.join(os.getcwd()),
            asset_name="OrderProcessing",
        )

        # Create the ALB Task Image
        task_image_options = ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
            image=image,
            container_name="Flexschools-container",
            environment={
                "DB_HOST": db.db_instance_endpoint_address,
                "DB_NAME": "FlexischoolsDB",
                "DB_USER": "flexischoolsuser",
                "QUEUE_URL": queue.queue_url,
            },
            log_driver=ecs.LogDrivers.aws_logs(
                stream_prefix="OrderProcessing",
                mode=ecs.AwsLogDriverMode.NON_BLOCKING,
            ),
        )

        # Create the ALB Fargate Service
        load_balanced_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            id="FlexischoolsFargateService",
            cluster=cluster,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=1,
            task_image_options=task_image_options,
            public_load_balancer=False,
            min_healthy_percent=100,
            assign_public_ip=False,
            load_balancer_name="Flexschools-LoadBalancer",
            service_name="Flexischools-service",
            security_groups=[fargate_sg],
        )

        # Configure the healthcheck path used by the ALB Target Group
        load_balanced_fargate_service.target_group.configure_health_check(path="/health")

        # Configure the ALB Fargate Service Min & Max Capacity
        scalable_target = load_balanced_fargate_service.service.auto_scale_task_count(min_capacity=1, max_capacity=20)

        # Configure AutoScaling for the Fargate Service based on CPU Utilization
        scalable_target.scale_on_cpu_utilization(id="CpuScaling", target_utilization_percent=50)

        # Configure AutoScaling for the Fargate Service based on Memory
        scalable_target.scale_on_memory_utilization(id="MemoryScaling", target_utilization_percent=50)

        # Grant permissions to the Fargate Task Role to consume message from the SQS queue
        queue.grant_consume_messages(load_balanced_fargate_service.task_definition.task_role)

        # Grant permisions to the Fargate Task Role to write to the RDS Instance
        load_balanced_fargate_service.task_definition.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["rds-db:connect"],
                resources=[
                    f"arn:aws:rds-db:{self.region}:{self.account}:dbuser:{db.instance_identifier}/flexischoolsuser"
                ],
            )
        )
