from flask import Flask, request, render_template
from openai import OpenAI
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

client = OpenAI()

@app.route('/', methods=['GET', 'POST'])
def index():
    sql_query = None
    user_prompt = ""  # Default empty string
    sql_dialect = "Standard SQL"  # Default SQL dialect
    db_schema = ""  # Default empty database schema

    if request.method == 'POST':
        user_prompt = request.form['prompt']
        sql_dialect = request.form['sql_dialect']
        db_schema = request.form['db_schema']  # Retrieve the database schema from the form

        # Create a tailored prompt including the SQL dialect and database schema
        full_prompt = f"Using {db_schema} schema, generate a {sql_dialect} query for: {user_prompt}"

        completion = client.chat.completions.create(
            model="ft:gpt-3.5-turbo-0125:personal:text-to-sql:9NiqfkTN",
            messages=[
                {"role": "user", "content": full_prompt}
            ]
        )
        sql_query = completion.choices[0].message.content

    return render_template('index.html', sql_query=sql_query, user_prompt=user_prompt, sql_dialect=sql_dialect, db_schema=db_schema)

if __name__ == '__main__':
    app.run(debug=True)
