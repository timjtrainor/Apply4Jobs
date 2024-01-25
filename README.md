
# Streamline the application process with AI

Drawing on my experience as a developer and transition to product manager, I've built Apply4Job, a Python project born from a deep understanding of the job search process. This MVP tackles common challenges like crafting tailored resumes and cover letters by leveraging AI assistance. While this version prioritizes developer-friendly local execution and avoids UI complexities, it seamlessly integrates Git for easy sharing and lays the foundation for future enhancements. Whether you're a developer, job seeker, or anyone looking to streamline your applications, Apply4Job offers a powerful tool to navigate the process with confidence.

[Product Requirements Doc (WIP)](https://docs.google.com/document/u/1/d/e/2PACX-1vQ9OBJ3Kd4XyRO8eXMf46ZW1eyMJ7iREFULlI1PAsholNIWNQr-gYhMnViqYZryTbmd4whJuOskb-jm/pub)

## Key Features:

AI-powered resume tailoring: Craft compelling resumes and cover letters that align with specific job descriptions and company values.
Job description analysis: Gain insights into job requirements and identify potential fit.
Direct message and email generation: Create personalized outreach messages for LinkedIn and email.
## Setup:

It is suggested to use a virtual environment.  https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/

* Install requirements: pip install -r requirements.txt
* Create an Affinda Account: https://docs.affinda.com/docs/getting-started
* Get Google AI API Key: https://ai.google.dev/tutorials/setup
* Create Full Resume: src/resume_full/template-FullResume.docx
* Run init.py: `python init.py`
  * Configure Affinda
    * Provide Affinda API Key
    * Set Affinda Workspace ID
    * Set Affinda Collection ID
  * Configure Google AI
  * Specify full resume filename (docx format).
* Parse full resume: `python AffindaParseFullResume.py`

## Usage:

Add job details to Apply4Job.db: 

Populate the following columns:
* company_name
* job_title
* link
* job_description
* company_mission (optional)
* company_values (optional)
* recent_news (optional)


### Review job description: `python step1_reviewJobDescription.py`

Summarizes job description and prompts for continuation.
Sets job status to "Bad Fit" if not continued.


### Create tailored resume: `python step2_createResume.py` 

Generates AI tailored resume bullets, summaries, accomplishments, and skills.
Allowing for manual selection or input.

### Apply and move resume file: 

1. Review and refine: Carefully examine the generated Docx resume file located in the temp/resumes folder. Pay close attention to formatting consistency and address any inconsistencies or errors that may have occurred during the AI-powered tailoring process.

2. Update application status: Within the job_applications table, set the date_applied field to the current date to accurately track your application progress.

3. Execute the code: Once you've completed the review and date update, proceed to run `python step3_apply.py`. This will automatically organize your application materials by moving the Docx resume from the temp/resumes/docx folder and your manually created PDF version from the temp/resumes/pdf folder to data/applied/{today's_date}, ensuring a well-structured and easily accessible history.

### Generate direct messages: `python step4_DM.py`

Creates potential LinkedIn messages or direct communications. Note this will also ask for the link if available. 

### Generate cover letter: `python step4_Email.py`

Creates a cover letter based on resume, company information, and recent news.  This also sets a followup date for a week from today in the database. 

## Additional Notes:

* Database: Utilizes SQLite database (Apply4Job.db). Connect using DBeaver or similar tool.
* Resume template: Located in src/resume_template.docx.
* Seamless.ai integration: Suggested for LinkedIn email extraction.

TODO:
* Script for follow-up email
* Move bullet count configuration to settings
* UI 

## Contributing:

Fork the repository
Create a branch for your changes
Make your changes
Submit a pull request

## License:

MIT License: link_to_license