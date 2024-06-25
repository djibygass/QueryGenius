from flask import Flask, request, render_template, session, redirect, url_for, flash
import os
import mysql.connector
from dotenv import load_dotenv
from openai import OpenAI
from google.cloud import bigquery
from google.oauth2 import service_account

app = Flask(__name__)
app.secret_key = 'your_very_secure_secret'  # Ensure you have a secure secret key
load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_db_connection():
    # Retrieve connection details from the session
    conn = mysql.connector.connect(
        host=session['db_details']['host'],
        database=session['db_details']['database'],
        user=session['db_details']['user'],
        password=session['db_details']['password']
    )
    return conn

def get_bigquery_client(credentials_path):
    credentials = service_account.Credentials.from_service_account_file(credentials_path)
    return bigquery.Client(credentials=credentials, project=credentials.project_id)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/generate-sql', methods=['POST'])
def generate_sql():
    error = None
    sql_query = None
    user_prompt = request.form['sql_prompt']
    sql_dialect = request.form['sql_dialect']

    full_prompt = f"Generate a {sql_dialect} SQL query for: {user_prompt}"
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

    return render_template('home.html', sql_query=sql_query, error=error, user_prompt=user_prompt, sql_dialect=sql_dialect)

@app.route('/connect', methods=['GET', 'POST'])
def connect():
    error = None
    tables = []
    schema = []
    sql_query = None
    query_results = []

    if request.method == 'POST':
        if 'fetch_tables' in request.form:
            sql_dialect = request.form['sql_dialect']
            session['sql_dialect'] = sql_dialect

            if sql_dialect == 'BigQuery':
                if 'credentials' not in request.files:
                    flash('No file part for credentials')
                    return redirect(request.url)
                
                file = request.files['credentials']
                if file.filename == '':
                    flash('No selected file for credentials')
                    return redirect(request.url)
                
                if file:
                    credentials_path = os.path.join('/tmp', file.filename)
                    file.save(credentials_path)
                    session['bigquery_project'] = request.form['project']
                    session['bigquery_dataset'] = request.form['dataset']
                    session['credentials_path'] = credentials_path

                    try:
                        client_bigquery = get_bigquery_client(credentials_path)
                        dataset_ref = client_bigquery.dataset(session['bigquery_dataset'])
                        tables = list(client_bigquery.list_tables(dataset_ref))
                        tables = [{'TABLE_NAME': table.table_id} for table in tables]
                    except Exception as err:
                        error = f"BigQuery connection failed: {err}"
            else:
                # Store connection details in session after successful connection
                session['db_details'] = {
                    'host': request.form['host'],
                    'database': request.form['database'],
                    'user': request.form['user'],
                    'password': request.form['password']
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
            sql_dialect = session.get('sql_dialect')

            if sql_dialect == 'BigQuery':
                try:
                    credentials_path = session['credentials_path']
                    client_bigquery = get_bigquery_client(credentials_path)
                    table_ref = client_bigquery.dataset(session['bigquery_dataset']).table(table_name)
                    table = client_bigquery.get_table(table_ref)
                    schema = [{'COLUMN_NAME': field.name, 'DATA_TYPE': field.field_type} for field in table.schema]
                    session['schema'] = schema  # Store schema in session for further use
                except Exception as err:
                    error = f"Error fetching BigQuery schema: {err}"
            else:
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
            sql_dialect = session.get('sql_dialect')

            full_prompt = f"Using the schema {schema} of table {table_name}, generate a SQL query for: {user_prompt}"
            try:
                completion = client.chat.completions.create(
                    model="ft:gpt-3.5-turbo-0125:personal:text-to-sql:9NiqfkTN",
                    messages=[
                        {"role": "user", "content": full_prompt}
                    ]
                )
                sql_query = completion.choices[0].message.content

                if sql_dialect == 'BigQuery':
                    # Qualify the table names in the generated SQL query
                    qualified_table_name = f"`{session['bigquery_project']}.{session['bigquery_dataset']}.{table_name}`"
                    sql_query = sql_query.replace(table_name, qualified_table_name)

                    try:
                        credentials_path = session['credentials_path']
                        client_bigquery = get_bigquery_client(credentials_path)
                        query_job = client_bigquery.query(sql_query)
                        query_results = [dict(row) for row in query_job.result()]
                    except Exception as err:
                        error = f"Error executing BigQuery SQL: {err}"
                else:
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
