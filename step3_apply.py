import datetime
import pandas as pd
import sqlite3
import os
import shutil

# import global variables
import variables.global_variables as global_vars
from utilities.gobal_functions import get_config_value_from_key

# import functions
# N/A

# Set Today
today = datetime.date.today()

# Connect to the database
conn = sqlite3.connect(global_vars.sqlite_db_file)

# Create a cursor
cursor = conn.cursor()

# Convert data to a pandas dataframe
df = pd.read_sql_query("SELECT * "
                       "FROM job_applications "
                       "WHERE status = 'Step 3 - Apply' "
                       "AND date_applied IS NOT NULL", conn)

# Loop through the filtered records
for index, row in df.iterrows():
    # Get required data from the record
    job_company = row['company_name']
    job_title = row['job_title']

    # Remove temp files
    file_name = f'{job_company}-{job_title}'

    # Define the files to be modified
    docx_resume_file = f"temp/resumes/docx/{file_name}-Resume.docx"
    pdf_resume_file = f"temp/resumes/pdf/{file_name}-Resume.pdf"

    # Create subdirectories for the current date for data/applied
    current_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    dst_dir = os.path.join('data/applied', current_date_str)
    os.makedirs(dst_dir, exist_ok=True)  # Create dir if it doesn't exist

    # Move DOCX and PDF files with error handling
    for src_file in (docx_resume_file, pdf_resume_file):
        try:
            shutil.move(src_file, os.path.join(dst_dir, f'{file_name}{os.path.splitext(src_file)[1]}'))
            print(f"{src_file} moved to {dst_dir} successfully.")
        except OSError as error:
            print(f"ERROR moving {src_file} to {dst_dir}: {error}")
    pass

    # Update Database
    cursor.execute("UPDATE job_applications SET status = ? WHERE job_application_id = ?",
                   ('Step 4 - DM', row['job_application_id']))
    conn.commit()

cursor.close()
conn.close()
