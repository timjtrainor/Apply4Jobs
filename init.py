import sqlite3

import variables.global_variables as global_vars

# Create the SQLite Database
# Define Job Application table name and columns
job_app_table_name = "job_applications"
job_app_columns = [
    "job_application_id integer not null constraint job_applications_pk primary key autoincrement",
    "company_name           TEXT                                 not null",
    "job_title              TEXT                                 not null",
    "link                   TEXT",
    "job_description        BLOB",
    "company_mission        BLOB",
    "company_values         BLOB",
    "recent_news            BLOB",
    "date_applied           TEXT",
    "status                 TEXT    default 'Step 1 - JD Review' not null",
    "original_fit_score     integer",
    "final_fit_score        integer",
    "ai_requirements        BLOB",
    "keywords               BLOB",
    "guidance               BLOB",
    "resume_summary         BLOB",
    "resume_summary_bullets BLOB",
    "resume                 BLOB",
    "linkedin_post_url      TEXT",
    "linkedin_comment       BLOB",
    "email                  BLOB",
    "followup               BLOB",
    "date_resume_created    TEXT",
    "date_jd_review         TEXT",
    "date_created           INTEGER default current_date",
    "date_emailed           TEXT",
    "date_email_followup    TEXT",
    "constraint job_applications_business_key unique(company_name, job_title)",
]

# Create a connection to the database
conn = sqlite3.connect(global_vars.sqlite_db_file)
cursor = conn.cursor()

# Create Job Applications table with CREATE TABLE statement and commit
create_table_statement = f"CREATE TABLE IF NOT EXISTS {job_app_table_name} ({', '.join(job_app_columns)})"
print (create_table_statement)
create_table_sql = f"CREATE TABLE IF NOT EXISTS {job_app_table_name} ({', '.join(job_app_columns)})"
cursor.execute(create_table_sql)
conn.commit()

# Define config table name and columns
config_table_name = "config"
config_columns = [
    "key TEXT not null constraint config_pk unique",
    "value TEXT not null"
]
# Create config table with CREATE TABLE statement and commit
create_config_table_sql = f"CREATE TABLE IF NOT EXISTS {config_table_name} ({', '.join(config_columns)})"
cursor.execute(create_config_table_sql)
conn.commit()

# Setup Affinda API
setup_affinda_api = input("Setup Affinda API? (y/n): ")
if setup_affinda_api.lower() == "y":
    affinda_token = input("Enter your Affinda API token (null to skip): ")
    if affinda_token is not None:
        # Store a password for a service
        cursor.execute('INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET key = ?',
                       ('affinda_token', affinda_token, affinda_token))
        conn.commit()
    affinda_workspace_id = input("Enter your Affinda Workspace ID (null to skip): ")
    if affinda_workspace_id is not None:
        # Store a workspace for a service
        cursor.execute('INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET key = ?',
                       ('affinda_workspace_id', affinda_workspace_id, affinda_workspace_id))
        conn.commit()
    affinda_collection_id = input("Enter your Affinda Collection ID (null to skip): ")
    if affinda_collection_id is not None:
        # Store a collection for a service
        cursor.execute('INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET key = ?',
                       ('affinda_collection_id', affinda_collection_id, affinda_collection_id))
        conn.commit()
# Setup Google API
setup_google_api = input("Setup Google API? (y/n): ")
if setup_google_api.lower() == "y":
    google_token = input("Enter your Google AI API Key (null to skip): ")
    if google_token is not None:
        # Store a password for a service
        cursor.execute('INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET key = ?',
                       ('google_token', google_token, google_token))
        conn.commit()

# Set Full Resume File Name
full_resume_file_name = input("Enter your Full Resume File Name excluding extension: ")
if full_resume_file_name is not None:
    # Store full resumefile name
    cursor.execute('INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET key = ?',
                   ('full_resume_file_name', full_resume_file_name, full_resume_file_name))
    conn.commit()

# Close the cursor and connection
cursor.close()
conn.close()