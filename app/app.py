from flask import Flask, request, render_template, session
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
from openai import OpenAI

app = Flask(__name__)
load_dotenv()
app.secret_key = 'your_secret_key_here'  # Required for session management

client = OpenAI()

@app.route('/', methods=['GET', 'POST'])
def index():
    sql_query = None
    table_schema = None
    mode = request.args.get('mode', 'query')  # Default mode

    if request.method == 'POST':
        if 'action' in request.form and request.form['action'] == 'generate_sql':
            user_prompt = request.form.get('prompt', '')
            sql_dialect = request.form.get('sql_dialect', 'Standard SQL')
            db_schema = request.form.get('db_schema', '')
            full_prompt = f"Using {db_schema} schema, generate a {sql_dialect} query for: {user_prompt}"
            completion = client.chat.completions.create(
                model="ft:gpt-3.5-turbo-0125:personal:text-to-sql:9NiqfkTN",
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )
            sql_query = completion.choices[0].message.content

        elif 'action' in request.form and request.form['action'] == 'fetch_schema':
            try:
                conn = mysql.connector.connect(
                    host=request.form['rds_endpoint'],
                    database=request.form['db_name'],
                    user=request.form['username'],
                    password=request.form['password']
                )
                if conn.is_connected():
                    cursor = conn.cursor()
                    cursor.execute(f"DESCRIBE {request.form['table_name']};")
                    schema_details = cursor.fetchall()
                    table_schema = '\n'.join([f"{row[0]}: {row[1]}" for row in schema_details])
                    session['db_schema'] = request.form['table_name']  # Store the table name as the schema name
            except Error as e:
                table_schema = f"Failed to fetch schema: {str(e)}"
            finally:
                if conn.is_connected():
                    conn.close()

    return render_template('index.html', sql_query=sql_query, table_schema=table_schema, mode=mode)

if __name__ == '__main__':
    app.run(debug=True)