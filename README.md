# Text-to-SQL Web Application

## Overview
This project is a web application designed to convert natural language text into SQL queries using a fine-tuned OpenAI GPT model. It features a web-based interface for easy interaction, API connectivity for model access, cloud-based data storage, and the use of deep reinforcement learning for continual model improvement.

## Prerequisites
- Flask for the web framework
- OpenAI API for accessing the GPT model
- AWS SDK (Boto3) for cloud interactions
- Reinforcement learning libraries (such as Tensorflow)

  
## Features
- **Model FineTuning**: Fine tune an openai model with sql queries.
- **API Integration**: Utilizes a fine-tuned OpenAI GPT model through an API.
- **Cloud Storage**: Stores session data and user queries securely in the cloud using AWS services.
- **Reinforcement Learning**: Implements deep reinforcement learning to refine and improve the model based on user interactions and feedback.


## CI/CD Integration
### Continuous Integration (CI)
- **GitHub Actions**: Automatically runs tests and builds the application upon each commit to the main branch, ensuring that changes are properly integrated and tested before deployment.
- **Linting and Testing**: Integrates code linting and unit tests to maintain code quality and functionality.

### Continuous Deployment (CD)
- **AWS CodePipeline**: Manages the deployment pipeline starting from code changes up to production deployment.
- **AWS CodeBuild**: Compiles code, runs tests, and produces ready-to-deploy artifacts.
- **AWS CodeDeploy**: Automatically deploys the application to specified AWS services, ensuring that the application is always up-to-date with the latest changes.
