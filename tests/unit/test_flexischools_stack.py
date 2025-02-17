import aws_cdk as core
import aws_cdk.assertions as assertions
import pytest

from flexischools.flexischools_stack import FlexischoolsStack


@pytest.fixture
def app():
    return core.App()


@pytest.fixture
def test_stack(app):
    return FlexischoolsStack(app, "flexischools")


@pytest.fixture
def template(test_stack):
    return assertions.Template.from_stack(test_stack)


def test_vpc_created(template):
    template.has_resource_properties(
        "AWS::EC2::VPC", {"CidrBlock": "10.0.0.0/16", "EnableDnsSupport": True, "EnableDnsHostnames": True}
    )


def test_db_created(template):
    template.has_resource_properties(
        "AWS::RDS::DBInstance",
        {
            "DBInstanceIdentifier": "flexischools-db",
            "Engine": "postgres",
            "EngineVersion": "17.2",
            "DBInstanceClass": "db.t3.micro",
            "DBName": "FlexischoolsDB",
            "PubliclyAccessible": False,
            "StorageEncrypted": True,
            "Port": "5500",
        },
    )


def test_dlq_created(template):
    template.has_resource_properties(
        "AWS::SQS::Queue",
        {
            "QueueName": "Flexischools-DLQ",
            "MessageRetentionPeriod": 1209600,  # 14 days in seconds
        },
    )


def test_queue_created(template):
    template.has_resource_properties(
        "AWS::SQS::Queue",
        {
            "QueueName": "Flexischools-orders-queue",
            "VisibilityTimeout": 300,
            "RedrivePolicy": {"maxReceiveCount": 5},
        },
    )


def test_cluster_created(template):
    template.has_resource_properties("AWS::ECS::Cluster", {"ClusterName": "Flexischools-cluster"})


def test_fargate_service_created(template):
    template.has_resource_properties(
        "AWS::ECS::Service",
        {
            "LaunchType": "FARGATE",
            "DesiredCount": 1,
            "ServiceName": "Flexischools-service",
            "NetworkConfiguration": {"AwsvpcConfiguration": {"AssignPublicIp": "DISABLED"}},
        },
    )

    template.has_resource_properties(
        "AWS::ElasticLoadBalancingV2::LoadBalancer", {"Name": "Flexschools-LoadBalancer", "Scheme": "internal"}
    )


def test_fargate_scaling(template):
    template.has_resource_properties(
        "AWS::ApplicationAutoScaling::ScalableTarget",
        {
            "MinCapacity": 1,
            "MaxCapacity": 20,
        },
    )
