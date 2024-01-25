import datetime
import pandas as pd
import json
import sqlite3
import shutil

from docx import Document

# import global variables
import variables.global_variables as global_vars

# import functions
from utilities.gemini_functions import setup_model, generate_fit_score, call_generative_api_with_retries
from utilities.gobal_functions import create_list_from_lines, replace_text_in_docx, \
    user_selects_option, user_selects_options, get_config_value_from_key

# Set Today
today = datetime.date.today()

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
work_experience = loaded_resume['data']['work_experience']

# Set the number of bullets per role
num_bullets_per_role = [
    5,  # 1 Firstup
    2,  # 2 Nike
    4,  # 3 WC PM
    4,  # 4 WC Dev
    2,  # 5 PCC
    2,  # 6 Verisae
]
# Setup the Gemini model
model = setup_model(google_ai_key)  # Use default settings

# Convert data to a pandas dataframe
df = pd.read_sql_query("SELECT * FROM job_applications WHERE status = 'Step 2 - Resume'", conn)

# Loop through the filtered records
for index, row in df.iterrows():
    # Get required data from the record
    target_company = row['company_name']
    target_job_title = row['job_title']
    target_job_description = str(row['job_description'])
    target_guidance = str(row['guidance'])
    target_keywords = str(row['keywords'])
    target_company_mission = str(row['company_mission'])
    target_company_values = str(row['company_values'])

    # Check for null target_company_mission and target_company_values
    if not target_company_mission or not target_company_values:
        no_mission_or_values_prompt = input(f"No company_mission or company_values for "
                                            f"{target_company} - {target_job_title}. "
                                            f"Do you want to continue (y/n)?")

        if not no_mission_or_values_prompt.lower().startswith('y'):
            print(f"Skipping: {target_company} - {target_job_title}")
            continue

    # copy ResumeTemplate.docx to a new file
    resume_file_name = f"{target_company}-{target_job_title}-Resume"
    docx_resume_file_name = f'temp/resumes/docx/{resume_file_name}.docx'
    template_resume_file_name = f'data/src/resume_template/ResumeTemplate.docx'

    # copy ResumeTemplate.docx to a new file
    shutil.copy(template_resume_file_name, docx_resume_file_name)

    # Open the New Company Specific Resume
    resume_docx_file = Document(docx_resume_file_name)

    # Set the Job Title in the resume_template docx and save
    replace_text_in_docx(resume_docx_file, 'jobTitle', target_job_title)
    resume_docx_file.save(docx_resume_file_name)

    # Update User with progress
    print(f"Processing: {target_company} - {target_job_title}")

    generated_resume = 'Summary \n\n summaryPlaceHolder \n\n summaryBullets'

    full_resume_bullets_list = []

    # Loop through each job in the resume_template
    for resume_job_index in range(len(work_experience)):
        resume_company = work_experience[resume_job_index]['organization']
        resume_job_title = work_experience[resume_job_index]['job_title']
        resume_job_months = work_experience[resume_job_index]['dates']['months_in_position']
        resume_job_start = work_experience[resume_job_index]['dates']['start_date']
        resume_job_end = work_experience[resume_job_index]['dates']['end_date']
        resume_job_achievements = work_experience[resume_job_index]['job_description']

        num_of_bullets = num_bullets_per_role[resume_job_index]

        # Filter Achievements to keep the most important

        bullets_filter_prompt_parts = [
            "Input: "
            "Achievements: " + resume_job_achievements + "\n"
            "Job Description: " + target_job_description + "\n"
            "Job Guidance: " + target_guidance + "\n"
            "Task: "
            "Analyze the achievements and select the top " + str(num_of_bullets) +
            " that most closely align with the job description and guidance. "
            "Prioritize achievements that:\n"
            "- Demonstrate skills, experience, and accomplishments directly matching those "
            "specified in the job description and guidance.\n"
            "- Highlight measurable results and quantifiable impacts.\n"
            "- Align with the company's values or mission (if mentioned in the guidance).\n"
            "- Demonstrate leadership or initiative (if relevant to the role).\n"
            "Output: The top " + str(num_of_bullets) + " most relevant achievements, presented "
            "verbatim as they appear in the input list. \n"
            "Example Output:\n"
            "- Achievement Sentence 1\n"
            "- Achievement Sentence 2\n"

        ]

        ai_filtered_bullets = call_generative_api_with_retries(model, bullets_filter_prompt_parts)
        # create a list of filtered achievements removing empty lines
        ai_filtered_bullet_list = create_list_from_lines(ai_filtered_bullets.text)

        resume_job_bullets_list = []

        # Add the filtered achievements to the final job achievements list
        # Loop through each job filtered achievements
        for bullet_index in range(len(ai_filtered_bullet_list)):
            original_bullet = ai_filtered_bullet_list[bullet_index]

            bullet_update_prompt_parts = [
                "Input:\n"
                "Original Achievement: " + original_bullet + "\n"
                "Target Guidance Item: " + target_guidance + "\n"
                "Job Guidance: " + target_guidance + "\n"
                "Keywords: " + target_keywords + "\n"
                "Task: \n"
                "Craft 5 enhanced versions of the original achievement bullet, keeping it under 250 characters each. "
                "Focus on:\n"
                "- Integrating relevant keywords naturally, avoiding keyword stuffing.\n"
                "- Clarifying details by mentioning tools, technologies, or processes used.\n"
                "- Quantifying impact with data or metrics whenever possible, or offering alternative ways to "
                "demonstrate results.\n"
                "- Aligning the revised bullet with the most relevant Resume Bullets Guidance items. \n"
                "- Do not change the meaning of the original bullet for all suggestions.\n"
                "- Using professional language, avoiding buzzwords, clichés, and personal pronouns.\n"
                "- Keep the action verb the same as the original achievement or use a verb with the same meaning.\n"
                "Output: \n"
                "Just the enhanced bullet text with no formatting and each bullet on a separate line.\n"
            ]

            print(global_vars.pacifier_message)
            ai_bullet_response = call_generative_api_with_retries(model, bullet_update_prompt_parts)
            # Create a list of all original_achievement options starting with the original original_achievement
            bullet_options_list = [original_bullet] + create_list_from_lines(ai_bullet_response.text)

            print(f"-------{resume_company} - {resume_job_title} - Bullet {bullet_index + 1} of {num_of_bullets}------")
            selected_bullet = user_selects_option(bullet_options_list)

            # Update Resume Job
            resume_job_bullets_list.append(selected_bullet)
            full_resume_bullets_list.append(f"At {resume_company}, {selected_bullet}")

        # Exiting the Job Achievement Loop Going to Next Job
        resume_job_bullets_string = "- " + "\n- ".join(resume_job_bullets_list)

        # Display to the User the full list of bullets for the resume_template job
        print(f"{resume_company} - {resume_job_title}")
        print(resume_job_bullets_string)

        # set the placeholder string based on the job index number
        docx_jobNumberPlaceholder = 'job' + str(resume_job_index + 1) + 'Achievement'

        # Iterate over each achievement and add it to the docx
        for final_ach_index in range(len(resume_job_bullets_list)):
            achievement_counter = docx_jobNumberPlaceholder + str(final_ach_index + 1)
            replace_text_in_docx(resume_docx_file, achievement_counter, resume_job_bullets_list[final_ach_index])

        # Save the docx file
        resume_docx_file.save(docx_resume_file_name)

        continue
    # Finished building the work_experience for the job in loop.

    # Create a summary for the job description
    full_resume_bullets_string = "\n".join(full_resume_bullets_list)
    # Use the AI job description to generate a resume summary
    resume_summary_prompt_parts = [
        "Persona: Executive career coach that works with highly skilled job seekers. \n"
        "Guidance: " + target_guidance + "\n\n"
        "Company: " + target_company + "\n"
        "Job Description: " + target_job_description + "\n\n"
        "Resume Bullets: " + full_resume_bullets_string + "\n\n"
        "Keywords: " + target_keywords + "\n\n"
        "Company Values:" + target_company_values + "\n"
        "Company Mission:" + target_company_mission + "\n\n"
        "Task: Craft 3 captivating and ATS-friendly summaries, each no longer than 3-4 sentences. Ensure they:\n"
        "1. ** Hook attention: ** Start with a strong first sentence that highlights a relevant achievement or skill.\n"
        "2. ** Showcase expertise:** Briefly demonstrate your qualifications and value proposition using keywords "
        "and a quantifiable accomplishment from your resume bullets.\n"
        "3. **Align with guidance:** Address key points from the Resume Summary Guidance.\n"
        "4. **Express passion:** Conclude with a genuine reference to a specific company value or mission statement, "
        "demonstrating your alignment with their vision.\n"
        "Format: Avoid generic statements, buzzwords, clichés, and personal pronouns. "
        "Use active voice and strong verbs. \n\n"
        "Output: 3 separate lines, each containing a complete resume summary."

    ]
    print(f"{global_vars.pacifier_message} Now working on Resume summary")
    summaries_response = call_generative_api_with_retries(model, resume_summary_prompt_parts)
    summaries = summaries_response.text.strip()

    # Create a list of all summaries options returned from the AI
    summaries_options_list = create_list_from_lines(summaries)

    # Have the user choose an option
    print(f"-----------{target_company} - {target_job_title}-----------------")
    summary = user_selects_option(summaries_options_list)

    # Write the summary to the database
    cursor.execute("UPDATE job_applications SET resume_summary = ? WHERE job_application_id = ?",
                   (summary, row['job_application_id']))
    conn.commit()

    # Update Generated Text Resume with SelectedSummary
    generated_resume = generated_resume.replace("summaryPlaceHolder", summary)

    # Updated the Resume docx with the summary
    replace_text_in_docx(resume_docx_file, 'summaryParagraph', summary)
    # Save the docx file
    resume_docx_file.save(docx_resume_file_name)

    # Summary Achievements
    summary_achievements_prompt_parts = [
        "Input: \n"
        "Persona: Executive career coach that works with highly skilled job seekers. \n"
        "Guidance: " + target_guidance + "\n"
        "Job Description: " + target_job_description + "\n"
        "Achievements: " + full_resume_bullets_string + "\n"
        "Keywords: " + target_keywords + "\n"
        "Summary Paragraph: " + summary + "\n\n"
        "Company Values:" + target_company_values + "\n"
        "Company Mission:" + target_company_mission + "\n\n"
        "Task: "
        "Identify 6 achievements that best showcase your skills and experiences relevant to the 3 Keys "
        "and Resume Bullet Guidance. Rewrite each original achievement to be:\n"
        "1. **Concise and engaging:** Aim for 2-3 lines, employing strong action verbs and vivid language.\n"
        "2. **Keyword-rich:** Integrate hard and soft keywords naturally, but avoid keyword stuffing.\n"
        "3. **Company-specific:** Mention the company where the achievement occurred, adding context and impact.\n"
        "4. **Relevant:** Align each achievement with at least one Key and support the claims in your summary "
        "paragraph.\n\n"
        "Please prioritize achievements that are:\n"
        "* **Quantifiable:** Include measurable results and data if possible.\n"
        "* **Demonstrate initiative and leadership (where applicable).**\n"
        "* **Unique and impactful:** Highlight achievements that stand out from others.\n\n"
        "Avoid formatting or styling in the output. \n\n"
        "Output: List 6 individual achievements, each on a separate line."
    ]
    # Use the AI to generate a list of achievements
    print(global_vars.pacifier_message)
    summary_achievements_response = call_generative_api_with_retries(model, summary_achievements_prompt_parts)
    # Create a clean list of summary original_achievement options
    summary_achievements_list = create_list_from_lines(summary_achievements_response.text)

    # Process User Input
    summary_achievements = user_selects_options(summary_achievements_list, number_of_choices=3)

    # Iterate over each summary achievement and add it to the resume_template docx
    for final_ach_index in range(len(summary_achievements)):
        achievement_counter = 'summaryBullet' + str(final_ach_index + 1)
        replace_text_in_docx(resume_docx_file, achievement_counter, summary_achievements[final_ach_index])

    # Save the docx file
    resume_docx_file.save(docx_resume_file_name)

    # Convert the list to a string
    resume_summary_bullets = '\n'.join(summary_achievements)

    # Add the work experience to the generated resume_template
    generated_resume = generated_resume.replace("summaryBullets", resume_summary_bullets)

    # Write the summary bullet to the database
    cursor.execute("UPDATE job_applications SET resume_summary_bullets = ? WHERE job_application_id = ?",
                   (resume_summary_bullets, row['job_application_id']))
    conn.commit()

    # Update Generated Text Resume with SelectedSummary
    generated_resume = (generated_resume + '\n' +
                        'Education: \n' +
                        'Bachelor of Science - Computer Information Systems \n'
                        'Bentley University, Waltham, MA\n\n'
                        'Certification: \n'
                        'Machine Learning Foundations for Product Managers - December 2023\n'
                        'Duke University\n'
                        'AWS Cloud Quest: Cloud Practitioner - January 2024 \n'
                        'Amazon Web Services Training and Certification\n\n'
                        'Skills: \n'
                        )

    # After Summary Achievements is selected, create a list of skills
    resume_skills_prompt_parts = [
        "Input: \n"
        "Persona: Executive career coach that works with highly skilled job seekers. \n"
        "Job Description: " + target_job_description + "\n\n"
        "Keywords: " + target_keywords + "\n\n"
        "Resume: " + generated_resume + "\n"
        "Guidance: " + target_guidance + "\n\n"
        "Task: "
        "Please analyze the resume and extract the following, presented as comma-separated lists within their "
        "respective groups:\n"
        "1. All hard keywords matching those found in the guidance. \n"
        "2. Specific technologies mentioned in the resume (e.g., NiFi, AWS). \n"
        "Categorize these skills into 3 logical groups based on the concise versions of the Guidance 3 Keys.\n"
        "Output: A structured list of skills, categorized into 3 comma-separated groups. "
        "Each category should be labeled based on teh guidance in a 2-3 word heading. \n\n"
        "Avoid: Including soft skills in the output. \n\n "
        "Output Format: \n"
        "Heading 1: Skill 1, Skill 2, Skill 3, etc. \n"
        "Heading 2: Skill 1, Skill 2, Skill 3, etc. \n"
        "Heading 3: Skill 1, Skill 2, Skill 3, etc. \n"

    ]
    print(global_vars.pacifier_message)
    skills_response = call_generative_api_with_retries(model, resume_skills_prompt_parts)
    skills_string = skills_response.text.strip()

    print("Skills: " + skills_string)

    # add the skills to the txt file
    generated_resume = generated_resume + skills_response.text.strip()

    # add the skills to the docx file
    replace_text_in_docx(resume_docx_file, 'skillsPlaceHolder', skills_string)
    # Save the docx file
    resume_docx_file.save(docx_resume_file_name)

    # Use the AI job skills to generate a Fit Score
    fit_score = generate_fit_score(model, target_job_description, generated_resume)
    print(f'Fit Score: {fit_score}')  # Print the fit score

    # Update the database
    cursor.execute("UPDATE job_applications "
                   "SET resume = ?, final_fit_score = ?, status = ?, date_resume_created = ? "
                   " WHERE job_application_id = ?",
                   (generated_resume, fit_score, 'Step 3 - Apply', today, row['job_application_id']))
    conn.commit()
    pass

cursor.close()
conn.close()
