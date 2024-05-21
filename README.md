# Text-to-SQL Web Application

## Overview
This project is a web application designed to convert natural language text into SQL queries using a fine-tuned OpenAI GPT model. It features a web-based interface for easy interaction, API connectivity for model access, cloud-based data storage, and the use of deep reinforcement learning for continual model improvement.

## Features
- **Model FineTuning**: Fine tune an openai model with sql queries.
- **API Integration**: Utilizes a fine-tuned OpenAI GPT model through an API.
- **Cloud Storage**: Stores session data and user queries securely in the cloud using AWS services.
- **Reinforcement Learning**: Implements deep reinforcement learning to refine and improve the model based on user interactions and feedback.

## Prerequisites
- Python 3.8+
- Flask for the web framework
- OpenAI API for accessing the GPT model
- AWS SDK (Boto3) for cloud interactions
- Reinforcement learning libraries (such as Tensorflow or PyTorch)
