import datetime
import pandas as pd
import sqlite3

# import global variables
import variables.global_variables as global_vars

# import functions
from utilities.gemini_functions import setup_model, call_generative_api_with_retries
from utilities.gobal_functions import get_config_value_from_key

# Connect to the database
conn = sqlite3.connect(global_vars.sqlite_db_file)

# Create a cursor
cursor = conn.cursor()

# Get Values from config table
google_ai_key = get_config_value_from_key(cursor, "google_token")

# Setup the Gemini model
model = setup_model(google_ai_key)  # Use default settings

# Convert data to a pandas dataframe
df = pd.read_sql_query("SELECT * FROM job_applications WHERE status = 'Step 5 - Email'", conn)

# Loop through the filtered records
for index, row in df.iterrows():
    # Get required data from the record
    job_company = row['company_name']
    job_title = row['job_title']
    job_company_mission = str(row['company_mission'])
    job_company_values = str(row['company_values'])
    job_company_recent_news = str(row['recent_news'])
    resume = str(row['resume'])

    email_prompt_parts = [
        "Input: \n"
        "Resume: " + resume + "\n"
        "Company: " + job_company + "\n"
        "Job Title: " + job_title + "\n"
        "Company Mission: " + job_company_mission + "\n"
        "Company Values: " + job_company_values + "\n"
        "Company Recent News: " + job_company_recent_news + "\n\n"
        "Task: \n"
        "Craft a personalized Cover Letter expressing my enthusiasm for "
        "the @job_title role at @company in under 350 words.\n"
        "It should: \n"
        "* Highlight my passion for company's mission and my skills relevant to the job "
        "(e.g., 'protecting data integrity' for @company_mission) "
        "Include the top 3 most important achievements from my work experience included in the resume_template"
        "* Align my values with company values "
        "* Optionally, incorporate recent news from @company_recent_news in the fashion of someone following them "
        "* Be concise, professional, and conclude with a call to action them to reach out directly or "
        "forward my resume_template to the proper channels.\n\n"
        "Output: \n"
        "Output: The email"
    ]

    # Call the email model
    print(global_vars.pacifier_message)
    email = call_generative_api_with_retries(model, email_prompt_parts)
    # Display the emails and ask the user to choose
    print(email.text)

    # Get today's date
    today = datetime.date.today()

    # Add 7 days to today's date
    date_in_7_days = today + datetime.timedelta(days=7)

    with open("temp/email/" + job_company + "-" + job_title + ".txt", "w") as file:
        file.write(email.text)

    # Update the database
    cursor.execute("UPDATE job_applications "
                   "SET email = ?, status = ?, date_emailed = ?, date_email_followup = ? "
                   "WHERE job_application_id = ?",
                   (email.text, 'Step 6 - Follow-Up', today, date_in_7_days, row['job_application_id']))

    conn.commit()

cursor.close()
conn.close()
