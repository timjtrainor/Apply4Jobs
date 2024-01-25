import pandas as pd
import sqlite3

# import global variables
import variables.global_variables as global_vars

# import functions
from utilities.gobal_functions import create_list_from_lines, user_selects_option, get_config_value_from_key
from utilities.gemini_functions import setup_model, call_generative_api_with_retries

# Connect to the database
conn = sqlite3.connect(global_vars.sqlite_db_file)

# Create a cursor
cursor = conn.cursor()

# Get Values from config table
google_ai_key = get_config_value_from_key(cursor, "google_token")

# Setup the Gemini model
model = setup_model(google_ai_key)  # Use default settings

# Convert data to a pandas dataframe
df = pd.read_sql_query("SELECT * FROM job_applications WHERE status = 'Step 4 - DM' AND company_name = 'Uber'", conn)

# Loop through the filtered records
for index, row in df.iterrows():
    # Get required data from the record
    job_company = row['company_name']
    job_title = row['job_title']
    job_company_mission = str(row['company_mission'])
    job_company_values = str(row['company_values'])
    job_company_recent_news = str(row['recent_news'])
    job_description = str(row['job_description'])
    resume_summary = str(row['resume_summary'])
    resume_summary_bullets = str(row['resume_summary_bullets'])

    if not job_company_recent_news:
        no_news_prompt = input(
            f"No Recent Company News for {job_company} - {job_title}. Do you want to continue (y/n)?")

        if not no_news_prompt.lower().startswith('y'):
            print(f"Skipping: {job_company} - {job_title}")
            continue

    post_link = input(f'Enter LinkedIn post url for {job_company} - {job_title}: ')

    dm_prompt_parts = [
        "Input: \n"
        "Company: " + job_company + "\n"
        "Job Title: " + job_title + "\n"
        "Company Mission: " + job_company_mission + "\n"
        "Company Values: " + job_company_values + "\n"
        "Company Recent News: " + job_company_recent_news + "\n\n"
        "Resume Summary: " + resume_summary + "\n"
        "Resume Summary Bullets: " + resume_summary_bullets + "\n\n"
        "Task: \n"
        "Craft a personalized LinkedIn comment (under 300 characters) expressing my enthusiasm for "
        "the @job_title role at @company.\n"
        "It should: \n"
        "* Highlight my passion for company's mission and my skills relevant to the job "
        "(e.g., 'protecting data integrity' for @company_mission) "
        "* Align my values with company values "
        "* Optionally, incorporate recent news from @company_recent_news in the fashion of someone following them "
        "* Be concise, professional, and conclude with a call to action for anyone at @company "
        "to reach out via LinkedIn.\n\n"
        "Output: \n"
        "3 Potential LinkedIn comments"
    ]

    # Call the DM model
    print(global_vars.pacifier_message)
    dm = call_generative_api_with_retries(model, dm_prompt_parts)

    # Have the user select the DM option
    dm_options_list = create_list_from_lines(dm.text)

    # Call user_selects_option to Check if the user entered a number or string
    print(f"--------{job_company} - {job_title} --------")
    chosen_dm = user_selects_option(dm_options_list)

    # Update the database
    cursor.execute("UPDATE job_applications "
                   "SET linkedin_post_url = ?, linkedin_comment = ?, status = ?"
                   " WHERE job_application_id = ?",
                   (post_link, chosen_dm, 'Step 5 - Email', row['job_application_id']))
    conn.commit()

cursor.close()
conn.close()
