#!/usr/bin/env python3
import os

import aws_cdk as cdk
from flexischools.flexischools_stack import FlexischoolsStack


app = cdk.App()
FlexischoolsStack(
    app,
    "FlexischoolsStack",
    env=cdk.Environment(account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")),
)

app.synth()
