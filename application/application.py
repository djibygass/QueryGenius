from flask import Flask, request, render_template, session, redirect, url_for, flash
import os
import mysql.connector
from openai import OpenAI
from google.cloud import bigquery
from google.oauth2 import service_account
import pymysql

application = Flask(__name__)

application.secret_key = 'secure_secret'

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise RuntimeError("OPENAI_API_KEY is not set in the environment")


client = OpenAI(api_key=api_key)

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=session['db_details']['host'],
            database=session['db_details']['database'],
            user=session['db_details']['user'],
            password=session['db_details']['password']
        )
        return conn
    except mysql.connector.Error as err:
        flash(f"Error connecting to database: {err}", 'danger')
        return None


def get_bigquery_client(credentials_path):
    credentials = service_account.Credentials.from_service_account_file(credentials_path)
    return bigquery.Client(credentials=credentials, project=credentials.project_id)

@application.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@application.route('/generate-sql', methods=['POST'])
def generate_sql():
    error = None
    sql_query = None
    user_prompt = request.form['sql_prompt']
    sql_dialect = request.form['sql_dialect']
    schemas = session.get('schemas', {})

    full_prompt = f"Using the schemas {schemas}, generate a SQL query for: {user_prompt}"
    try:
        completion = client.chat.completions.create(
            model="ft:gpt-3.5-turbo-0125:personal:text-to-sql:9NiqfkTN",
            messages=[{"role": "user", "content": full_prompt}]
        )
        sql_query = completion.choices[0].message.content
    except Exception as e:
        error = f"Error generating SQL: {e}"
    
    return render_template('home.html', sql_query=sql_query, error=error, user_prompt=user_prompt, sql_dialect=sql_dialect)

@application.route('/connect', methods=['GET', 'POST'])
def connect():
    error = None
    tables = []
    schemas = {}
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
            elif sql_dialect == 'Standard SQL':
                session['db_details'] = {
                    'host': request.form['host'],
                    'database': request.form['database'],
                    'user': request.form['user'],
                    'password': request.form['password']
                }
                try:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s", (session['db_details']['database'],))
                    tables = [{'TABLE_NAME': table[0].decode() if isinstance(table[0], bytearray) else table[0]} for table in cur.fetchall()]
                    cur.close()
                    conn.close()
                except mysql.connector.Error as err:
                    error = f"Database connection failed: {err}"
        
        elif 'fetch_schema' in request.form:
            selected_tables = request.form.getlist('table_select')
            sql_dialect = session.get('sql_dialect')

            if sql_dialect == 'BigQuery':
                try:
                    credentials_path = session['credentials_path']
                    client_bigquery = get_bigquery_client(credentials_path)

                    for table_name in selected_tables:
                        table_ref = client_bigquery.dataset(session['bigquery_dataset']).table(table_name)
                        table = client_bigquery.get_table(table_ref)
                        schema = [{'COLUMN_NAME': field.name, 'DATA_TYPE': field.field_type} for field in table.schema]
                        schemas[table_name] = schema

                    session['schemas'] = schemas
                except Exception as err:
                    error = f"Error fetching BigQuery schema: {err}"
            elif sql_dialect == 'Standard SQL':
                try:
                    conn = get_db_connection()
                    cur = conn.cursor(dictionary=True)
                    
                    for table_name in selected_tables:
                        cur.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = %s", (table_name,))
                        table_schema = cur.fetchall()
                        # Decode byte strings to regular strings
                        table_schema = [
                            {key: (value.decode() if isinstance(value, (bytes, bytearray)) else value) for key, value in column.items()}
                            for column in table_schema
                        ]
                        schemas[table_name] = table_schema

                    cur.close()
                    conn.close()
                    session['schemas'] = schemas
                except mysql.connector.Error as err:
                    error = f"Error fetching schema: {err}"
        
        elif 'generate_sql' in request.form:
            error = None
            sql_query = None
            query_results = []
            user_prompt = request.form['sql_prompt']
            sql_dialect = session.get('sql_dialect')
            schemas = session.get('schemas', {})

            full_prompt = f"Using the schemas {schemas}, generate a SQL query for: {user_prompt}"
            try:
                completion = client.chat.completions.create(
                    model="ft:gpt-3.5-turbo-0125:personal:text-to-sql:9NiqfkTN",
                    messages=[{"role": "user", "content": full_prompt}]
                )
                sql_query = completion.choices[0].message.content

                if sql_dialect == 'BigQuery':
                    try:
                        credentials_path = session['credentials_path']
                        client_bigquery = get_bigquery_client(credentials_path)
                        query_job = client_bigquery.query(sql_query)
                        query_results = [dict(row) for row in query_job.result()]
                    except Exception as err:
                        error = f"Error executing BigQuery SQL: {err}"
                elif sql_dialect == 'Standard SQL':
                    try:
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

    return render_template('connect.html', tables=tables, schemas=schemas, sql_query=sql_query, query_results=query_results, error=error)


@application.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    sql_prompt = request.form['sql_prompt']
    sql_generated = request.form['sql_generated']
    feedback = int(request.form['feedback']) 

    # Insert feedback into the database
    fb_host = os.getenv('FB_MYSQL_HOST')
    fb_database = os.getenv('FB_MYSQL_DATABASE')
    fb_username = os.getenv('FB_MYSQL_USER')
    fb_password = os.getenv('FB_MYSQL_PASSWORD')

    if not fb_host:
        raise RuntimeError("FB_MYSQL_HOST is not set in the environment")
    elif not fb_database:
        raise RuntimeError("FB_MYSQL_DATABASE is not set in the environment")
    elif not fb_username:
        raise RuntimeError("FB_MYSQL_USER is not set in the environment")
    elif not fb_password:
        raise RuntimeError("FB_MYSQL_PASSWORD is not set in the environment")

    
    db = pymysql.connect(
        host = os.getenv('FB_MYSQL_HOST'),
        database = os.getenv('FB_MYSQL_DATABASE'),
        user = os.getenv('FB_MYSQL_USER'), 
        password = os.getenv('FB_MYSQL_PASSWORD'),
        )
    
    cur = db.cursor()  
    
    try:
        cur.execute(
            "INSERT INTO feedback_table (sql_prompt, sql_generated, feedback) VALUES (%s, %s, %s)",
            (sql_prompt, sql_generated, feedback)
        )
        cur.connection.commit()
        flash('Thank you for your feedback!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error saving feedback: {err}", 'danger')

    finally:
        cur.close()
        db.close()

    return redirect(url_for('connect'))


if __name__ == '__main__':
    application.run(debug=True)

