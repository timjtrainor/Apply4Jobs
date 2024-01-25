import datetime
import pandas as pd
import json
import sqlite3
from pathlib import Path

# import global variables
import variables.global_variables as global_vars

# import functions
from utilities.gemini_functions import setup_model, generate_fit_score, call_generative_api_with_retries
from utilities.gobal_functions import get_config_value_from_key

# Connect to the database
conn = sqlite3.connect(global_vars.sqlite_db_file)

# Create a cursor
cursor = conn.cursor()

# Get Values from config table
resume_name = get_config_value_from_key(cursor, "full_resume_file_name")
google_ai_key = get_config_value_from_key(cursor, "google_token")

# get resume_template JSON file
with open('data/target/' + resume_name + '.json') as f:  # Open JSON file
    loaded_resume = json.load(f)

# get full resume_template text
resume_text = str(loaded_resume['data']['raw_text'])

# Set Today
today = datetime.date.today()

# Setup the Gemini model
model = setup_model(google_ai_key)  # Use default settings

# In Step 1 setup temp directory if it does not exist
temp_email = Path('temp/email')
temp_resume_docx = Path('temp/resumes/docx')
temp_resume_pdf = Path('temp/resumes/pdf')
target = Path('data/target')

temp_email.mkdir(parents=True, exist_ok=True)
temp_resume_docx.mkdir(parents=True, exist_ok=True)
temp_resume_pdf.mkdir(parents=True, exist_ok=True)

# Convert data to a pandas dataframe
df = pd.read_sql_query("SELECT * FROM job_applications WHERE status = 'Step 1 - JD Review'", conn)

# Loop through the filtered records
for index, row in df.iterrows():
    # Get required data from the record
    job_company = str(row['company_name'])
    job_title = str(row['job_title'])
    job_description = str(row['job_description'])

    # Update User with progress
    print(f"------- {job_company}-{job_title} -------")
    print("Generating AI Job Requirements...")

    # Gemini Prompt to Get Job Skills
    job_requirements_prompt_parts = [
        "Input: " + job_description + "\n\n"
        "Output:" + "\n"
        "Special Requirements (Explicitly Mentioned): "
        "List any specific certifications, licenses, security clearances, travel expectations, "
        "or other unusual requirements explicitly stated in the job description. "
        "Quote any instructions or guidelines provided for applying, including deadlines, application methods, "
        "or specific formatting requirements. \n"
        "Must-Have Skills (Explicitly Mentioned): "
        "List only the skills or qualifications explicitly identified as 'must-have', 'required', "
        "or 'essential' in the job description. "
        "Avoid assumptions or inferences; stick to the exact language used in the document. \n\n"
        "Omit: \n"
        "Inferences about company culture or work environment. "
        "Hints of tools, technologies, or methodologies not explicitly stated. "
        "Analysis of implied skills or qualifications. "
        "Suggestions for additional skills or experiences. "
        "Summaries of company tone or culture. "
        "Qualifications that don't explicitly indicate that they are required. \n\n"
        "Additional Tips: \n"
        "If a requirement is unclear, include it as a potential need for clarification during the "
        "application process. "
        "Pay close attention to formatting, capitalization, or special emphasis used in the "
        "job description to highlight key requirements. "
        "Consider using a text-analysis tool or software to help identify patterns and keywords "
        "if dealing with large volumes of job descriptions. "
    ]

    # Use the prompt to get a list of job requirements
    print(global_vars.pacifier_message)
    job_requirements_response = call_generative_api_with_retries(model, job_requirements_prompt_parts)

    # Update User with progress
    # Prompt the user to  review the job requirements to ensure alignment with their skills and interests.
    print(job_requirements_response.text)
    user_input = input("Do you want to process this item? (Y/N): ")

    # Handle the indication that they don't want to proceed with the job
    if user_input.lower() == "n":  # Check for "N" or "n" (case-insensitive)
        print("Skipping to next item...")

        # Update the status in the database
        # Update the field in the database
        cursor.execute('UPDATE job_applications SET status = ?, date_jd_review = ? WHERE job_application_id = ?',
                       ('Bad Fit', today, row['job_application_id']))
        conn.commit()
        continue  # Skip to the next iteration of the loop

    # Any key other than N or n will proceed with processing the job.
    job_requirements = job_requirements_response.text.strip()

    # Write the job requirements to the database
    cursor.execute('UPDATE job_applications SET ai_requirements = ? WHERE job_application_id = ?',
                   (job_requirements, row['job_application_id']))

    # Use the AI job skills to generate a Fit Score
    print(global_vars.pacifier_message + ' Job Fit')
    fit_score = generate_fit_score(model, job_requirements, resume_text)
    print(f'Fit Score: {fit_score}')  # Print the fit score

    # Write the job fit to the Database
    cursor.execute('UPDATE job_applications SET original_fit_score = ? WHERE job_application_id = ?',
                   (fit_score, row['job_application_id']))

    # Use the job description to generate keywords
    # START KEYWORDS
    keywords_prompt_parts = [
        "Persona: Executive career coach that works with highly skilled job seekers. "
        "Job Description: " + job_description + "\n\n"
        "Output: " + "\n"
        "Hard keywords: A list of specific skills, tools, technologies, and qualifications explicitly"
        " mentioned in the job description. "
        "Soft keywords: A list of personality traits, work styles, cultural values, and desired behaviors "
        "implied in the job description's tone, language, and context."
        "Instructions: " + "\n"
        "Do not analyze text from the legal, compensation, or pay sections of the job description. "
        "Prioritize action verbs (e.g., manage, analyze, lead) and direct mentions of required skills "
        "and qualifications for the 'hard keywords' list. "
        "Identify descriptive adjectives and phrases conveying desired soft skills, company culture, "
        "and work environment for the 'soft keywords' list. "
        "Consider keywords mentioned multiple times or emphasized through formatting/bolding as more significant. "
        "Avoid repetition and redundancy in both lists."
        "Output: Hard keywords, soft keywords that will be included in a future prompt to improve a resume_template. "
    ]
    print(global_vars.pacifier_message + ' Now Working on Keywords!!')
    response = call_generative_api_with_retries(model, keywords_prompt_parts)

    ai_keywords = response.text.strip()

    # Write the job requirements to the Database
    cursor.execute('UPDATE job_applications SET keywords = ? WHERE job_application_id = ?',
                   (ai_keywords, row['job_application_id']))

    # END KEYWORDS

    # START GUIDANCE CODE
    # Use the job description to generate guidance
    resume_guidance_prompt_parts = [
        "Persona: Review the Job Description below as a Career Coach that is working with a senior level candidate. "
        "Job Description: " + job_description + "\n\n"
        "Task; Read through the Job Description as the Persona and provide guidance on what the candidate should "
        "include in their resume_template summary to impress the recruiter and hiring manager. "
        "Output: \n"
        "Resume Summary: Guidance instructions to be included in future prompts to create a resume summary."
        "Resume Bullets: Guidance instructions to be included in future prompts to improve each resume bullets to be "
        "specific to the job."
        "Resume 3 Keys: Instruction on the 3 key items the resume should communicate."
        "Output Example: \n"
        "Resume Summary Guidance: "
        "- Emphasize your 10+ years of progressive product management experience in an agile environment, "
        "highlighting your technical understanding and knowledge of data storage management software, "
        "machine learning, and artificial intelligence.\n "
        "- Showcase your demonstrated experience in driving and leading complex, "
        "multifaceted, early market stage products.\n"
        "Resume Bullets Guidance: \n"
        "- Include specific examples of how you have successfully shaped product vision, defined and "
        "iterated product roadmaps, and gathered and synthesized internal and external feedback to improve "
        "products.\n"
        "- Provide quantifiable results and achievements, such as increased customer satisfaction, "
        "improved product adoption, or enhanced revenue generation.\n"
        "- Demonstrate your ability to work effectively in a cross-functional and collaborative role, "
        "spanning engineering, marketing, sales, and customer support teams.\n"
        "3 Keys: \n"
        "- Experience building data solutions in the cloud. \n"
        "- Have built an AI-powered sales forecasting model using linear regression in R and Python. \n"
        "- Lead a project from 0 to 1."
    ]
    print(global_vars.pacifier_message + " Now working on Guidance!!")
    guidance_response = call_generative_api_with_retries(model, resume_guidance_prompt_parts)

    guidance = guidance_response.text.strip()

    # Write the job requirements to the Database
    cursor.execute('UPDATE job_applications SET guidance = ? WHERE job_application_id = ?',
                   (guidance, row['job_application_id']))

    # END GUIDANCE CODE

    # Update Status in the Database
    cursor.execute('UPDATE job_applications SET status = ?, date_jd_review = ? WHERE job_application_id = ?',
                   ('Step 2 - Resume', today, row['job_application_id']))

    # Commit the changes for the current row
    conn.commit()
    pass

# Close the cursor and connection
cursor.close()
conn.close()
