from flask import Flask, request, render_template, session, redirect, url_for
import os
import mysql.connector
from dotenv import load_dotenv
from openai import OpenAI

app = Flask(__name__)
app.secret_key = 'your_very_secure_secret'  # Ensure you have a secure secret key
load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_db_connection():
    # Retrieve connection details from the session
    conn = mysql.connector.connect(
        host=session['db_details']['host'],
        user=session['db_details']['user'],
        password=session['db_details']['password'],
        database=session['db_details']['database']
    )
    return conn

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/generate-sql', methods=['POST'])
def generate_sql():
    error = None
    sql_query = None
    user_prompt = request.form['sql_prompt']
    
    full_prompt = f"Generate a SQL query for: {user_prompt}"
    try:
        completion = client.chat.completions.create(
            model="ft:gpt-3.5-turbo-0125:personal:text-to-sql:9NiqfkTN",
            messages=[
                {"role": "user", "content": full_prompt}
            ]
        )
        sql_query = completion.choices[0].message.content
    except Exception as e:
        error = f"Error generating SQL: {e}"

    return render_template('home.html', sql_query=sql_query, error=error, user_prompt=user_prompt)

@app.route('/connect', methods=['GET', 'POST'])
def connect():
    error = None
    tables = []
    schema = []
    sql_query = None
    query_results = []

    if request.method == 'POST':
        if 'fetch_tables' in request.form:
            # Store connection details in session after successful connection
            session['db_details'] = {
                'host': request.form['host'],
                'user': request.form['user'],
                'password': request.form['password'],
                'database': request.form['database']
            }
            try:
                conn = get_db_connection()
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s", (session['db_details']['database'],))
                tables = cur.fetchall()
                cur.close()
                conn.close()
            except mysql.connector.Error as err:
                error = f"Database connection failed: {err}"
        
        elif 'fetch_schema' in request.form:
            table_name = request.form['table_select']
            session['table_name'] = table_name
            try:
                conn = get_db_connection()
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = %s", (table_name,))
                schema = cur.fetchall()
                cur.close()
                conn.close()
                session['schema'] = schema  # Store schema in session for further use
            except mysql.connector.Error as err:
                error = f"Error fetching schema: {err}"
        
        elif 'generate_sql' in request.form:
            user_prompt = request.form['sql_prompt']
            schema = session.get('schema', [])
            table_name = session.get('table_name', '')

            full_prompt = f"Using the schema {schema} of table {table_name}, generate a SQL query for: {user_prompt}"
            try:
                completion = client.chat.completions.create(
                    model="ft:gpt-3.5-turbo-0125:personal:text-to-sql:9NiqfkTN",
                    messages=[
                        {"role": "user", "content": full_prompt}
                    ]
                )
                sql_query = completion.choices[0].message.content
                
                # Execute the generated SQL query
                conn = get_db_connection()
                cur = conn.cursor(dictionary=True)
                cur.execute(sql_query)
                query_results = cur.fetchall()
                cur.close()
                conn.close()
            except mysql.connector.Error as err:
                error = f"Error executing SQL: {err}"
            except Exception as e:
                error = f"Error generating SQL: {e}"

    return render_template('connect.html', tables=tables, schema=schema, sql_query=sql_query, query_results=query_results, error=error)

if __name__ == '__main__':
    app.run(debug=True)
