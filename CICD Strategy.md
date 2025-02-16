# Part 2: CI/CD & Deployment Strategy

The following CI/CD strategy can be used to deploy  & manage this project.

## Environment Setup & Configuration

1. The DevOps team should create & utilise development, staging and production environments for the Order Processing service.
2. The environments can be designated AWS accounts or isolated regions in a single AWS account.
      1. For the purposes of simplicity, we will use separate AWS regions for development, staging and production in this strategy.
      2. Each AWS region should contain its own self-contained deployment of the Order Processing service.
3. IAM User credentials in the AWS account should be created to facilitate the Azure DevOps pipeline to assume into the account.
4. To safely manage credentials (such as database credentials or API keys) use [Azure Key Vault](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/key-vault-in-own-project?view=azure-devops&tabs=portal%2Cmanagedidentity).
5. Once the Azure Key Vault is configured the secrets can be [queried in the Azure DevOps pipeline](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/key-vault-in-own-project?view=azure-devops&tabs=portal%2Cmanagedidentity).
6. To safely handle database schema migrations the DevOps team can use database migrations tools such as [Redgate Flyway](https://documentation.red-gate.com/fd/getting-started-with-flyway-184127223.html) or [Liquidbase](https://www.liquibase.com/on-demand-demo) as part of the CI/CD process. These tools will allow the DevOps team to version, apply and rollback schema changes in a controlled manner.
7. Automated RDS backups can also be utilised to restore the database to a previously known good state should a problem arise.

## Continous Integration & Continous Delivery Process

1. The source code for the service should be stored in a shared code repository (such as GitHub).
2. The DevOps team should utilise Trunk-based development for the Order Processing service.
3. Team members should develop small code updates on Feature Branches that are merged to the Main branch frequently.
   1. Feature flags should be utilised to control the activation/disablement of the new code execution paths.
4. Azure DevOps pipelines should be configured with Stages to control the testing, building and release of new code to development, staging and production environments.
5. Azure DevOps pipelines should be configured to perform steps whenever it detects a merge to a branch.
   1. Merging to a feature branch can perform different steps compared to main.
6. When a merge to a feature branch is detected, Azure DevOps pipeline should be configured with steps to:
   1. Perform code formatting & type testing.
   2. Perform unit testing.
   3. Perform static code analysis testing to detect security risks.
   4. Docker image build testing.
7. When a merge to the main branch is detected, Azure DevOps pipeline should be configured with steps to:
   1. Build the Docker image and push to AWS ECR or other image repository.
   2. Deploy new code to the development environment.
   3. Use a Feature Flag configured in the Fargate service code to disable processing of messages from the development SQS queue.
   4. Use Flyway or Liquidbase to perform schema validation and apply database migrations (if detected).
   5. Enable a Feature Flag configured in the Fargate service code to test writes to the database work as expected.
   6. Perform Integration and/or End-to-End testing.
      1. If a problem is detected:
         1. Use Flyway or Liquidbase to automatically rollback the database migration.
         2. Enable a Feature Flag configured in the development environment Fargate service to begin normal processing of messages from the development SQS queue again.
      2. If all tests pass and writes to the database work correctly:
         1. Enable a Feature Flag configured in the development environment Fargate service to begin normal processing of messages from the development SQS queue again.
   7. The DevOps team can perform manual verification in the development environment at this stage if necessary.
8. Azure DevOps pipeline should be configured with a manual [Approvals](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops&tabs=check-pass) step to approve the release of new code to the staging environment.
   1. The approvers could be multiple senior members of the DevOps team.
9. Once the staging release is approved, the pipeline builds the Docker image and pushes to AWS ECR or other image repository.
10. Deploy new code to the staging environment.
11. Use a Feature Flag configured in the staging environment Fargate service code to disable processing of messages from the staging SQS queue.
12. Use Flyway or Liquidbase to perform schema validation and apply database migrations (if detected).
13. Enable a Feature Flag configured in the staging environment Fargate service code to test writes to the database work as expected.
14. Perform Integration and/or End-to-End testing.
    1. If a problem is detected writing to the database:
       1. Use Flyway or Liquidbase to automatically rollback the database migration.
       2. Enable a Feature Flag configured in the staging environment Fargate service to enable processing of messages from the staging SQS queue again.
    2. If all tests pass and writes to the database work correctly:
       1. Enable a Feature Flag configured in the staging environment Fargate service to enable processing of messages from the staging SQS queue again.
15. The DevOps team can then perform any further testing of the new code in the staging environment.
16. A final manual step in the Azure DevOps pipeline is necessary to approve the deployment to the production environment.
    1. This step allows senior members of the team to perform final review before its deployment to production.
17. Once the production release is approved, the pipeline builds the Docker image and pushes to AWS ECR or other image repository.
18. The new code is deployed to the production environment.
19. Use a Feature Flag configured in the production environment Fargate service code to disable processing of messages from the production SQS queue.
20. Use Flyway or Liquidbase to perform schema validation and apply database migrations (if detected).
21. Enable a Feature Flag configured in the production environment Fargate service code to test writes to the database work as expected.
22. Perform Integration and/or End-to-End testing.
    1. If a problem is detected writing to the database:
       1. Use Flyway or Liquidbase to automatically rollback the database migration.
       2. Enable a Feature Flag configured in the production environment Fargate service to enable processing of messages from the production SQS queue again.
    2. If all tests pass and writes to the database work correctly:
       1. Enable a Feature Flag configured in the production environment Fargate service to enable processing of messages from the production SQS queue again.

## Continous Deployment

1. Once the DevOps team has automated all steps necessary to release to production safely the manual approval/release steps can be removed.
2. This means that the Azure DevOps pipeline can be configured to automatically deploy new code to the Development, Staging and Production environments without the need for a manual approval/release step. Only a failed test in a previous step will stop the deployment of new code to the various environments.
