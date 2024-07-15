Detailed Documentation for QueryGenius Application
Overview
QueryGenius is a web application that converts natural language text into SQL queries. It supports multiple SQL dialects, including Standard SQL and BigQuery. The application allows users to connect to databases, fetch table schemas, generate SQL queries based on user prompts, and provide feedback on the generated queries.

Application Structure
application.py: The main Flask application file containing routes and business logic.
Templates:
home.html: The homepage template.
connect.html: The connection and interaction page template.
Static Files:
css/style.css: Custom styles for the application.
Requirements:
requirements.txt: List of Python dependencies.
Docker:
Dockerfile: Instructions to build the Docker image.
Dockerrun.aws.json: Configuration for AWS Elastic Beanstalk.
Application Functionality
Home Page (/):

Display an interface for the user to select an SQL dialect and enter a SQL prompt.
Generate and display SQL queries based on user input.
Connect Page (/connect):

Allow users to connect to a database by providing connection details.
Fetch and display table schemas for the selected tables.
Generate SQL queries based on user prompts and display the results.
Provide feedback on the generated SQL queries.
Feedback Submission (/submit-feedback):

Store user feedback on generated SQL queries in a database.
Deployment Steps
1. Setup AWS Elastic Beanstalk (EB) and ECR

Elastic Beanstalk Setup

Initialize Elastic Beanstalk:
Ensure you are in your project root directory.

sh
Copier le code
eb init -p python-3.8 <app-name> --region <region>
Follow the prompts to complete the initialization.

Create an Environment:

sh
Copier le code
eb create <env-name>
Set Environment Variables:

sh
Copier le code
eb setenv OPENAI_API_KEY=your_openai_api_key 
2. Requirements

Ensure your requirements.txt has the following versions to avoid conflicts:

text
Copier le code
botocore>=1.23.41,<1.32.0  # Ensure compatibility with awsebcli and s3transfer
awsebcli==3.20.10  # This ensures you are using a compatible version of awsebcli
s3transfer>=0.3.0,<0.5.0  # Ensure compatibility with botocore
3. Docker

Create your Dockerfile: Ensure your Dockerfile is set up to build your application.
Build the Docker Image:
sh
Copier le code
docker build -t <your-app> .
Run the Docker Container Locally:
sh
Copier le code
docker run -p 5000:5000 <your-app>  # Test the app locally
4. Docker Hub

Login to Docker Hub:

sh
Copier le code
docker login
Follow the prompts to enter your Docker Hub username and password.

Tag and Push the Image:

sh
Copier le code
docker tag <image-name> <dockerhub-username>/<image-name>
docker push <dockerhub-username>/<image-name>
5. AWS ECR

Create an ECR Repository:

Open the Amazon ECR console and create a new repository.
Authenticate Docker to ECR:

sh
Copier le code
aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin <your-account-id.dkr.ecr.your-region.amazonaws.com>
Tag and Push the Image:

sh
Copier le code
docker tag <image-name>:latest <ecr-repo-uri>
docker push <ecr-repo-uri>:latest
6. Elastic Beanstalk Deployment

Initialize Elastic Beanstalk with Docker:
sh
Copier le code
eb init -p docker <docker-image-name>
Create an Environment:
sh
Copier le code
eb create <env-name>
Set Environment Variables:
sh
Copier le code
eb setenv OPENAI_API_KEY=your_openai_api_key
7. Create Dockerrun.aws.json File

Place the Dockerrun.aws.json file in your project root directory:

json
Copier le code
{
  "AWSEBDockerrunVersion": 2,
  "containerDefinitions": [
    {
      "name": "query-genius",
      "image": "your-account-id.dkr.ecr.eu-west-3.amazonaws.com/query-genius:latest",
      "essential": true,
      "memory": 512,
      "portMappings": [
        {
          "hostPort": 5000,
          "containerPort": 5000
        }
      ]
    }
  ]
}
8. Push to AWS ECR

Make sure your Docker image is pushed to AWS ECR before creating the environment in Elastic Beanstalk.

9. Update the Environment Variables

Ensure all necessary environment variables are set in your Elastic Beanstalk environment configuration:

OPENAI_API_KEY
FB_MYSQL_HOST
FB_MYSQL_DATABASE
FB_MYSQL_USER
FB_MYSQL_PASSWORD
10. Access the Application

After deployment, access your application via the Elastic Beanstalk environment URL provided in the AWS console.

Notes
Database Access: Ensure that the database instances (both for your main database and the feedback database) are accessible from your Elastic Beanstalk environment.
Permissions: Ensure that the IAM roles and policies attached to your Elastic Beanstalk environment have the necessary permissions to pull images from ECR and access other AWS resources.
Testing: Thoroughly test the application locally using Docker before deploying it to the cloud to ensure that all functionalities work as expected.
