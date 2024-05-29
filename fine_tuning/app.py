from openai import OpenAI
from dotenv import load_dotenv
from datasets import load_dataset
import os

load_dotenv()

client = OpenAI()

completion = client.chat.completions.create(
  model="ft:gpt-3.5-turbo-0125:personal:text-to-sql:9NiqfkTN",
  messages=[
    {"role": "user", 
     "content": "How many marine species are found in the Southern Ocean ?"
     }
  ]
)

print(completion.choices[0].message.content)