import google.generativeai as genai
import time
import keyring

from google.api_core.exceptions import GoogleAPIError

# Import Global Variables
import variables.gemini_variables as gemini_cfg
from utilities.gobal_functions import strip_non_numeric

def setup_model(google_ai_key,
                model_name="gemini-pro",  # Default model name
                generation_config=gemini_cfg.generation_config,  # Generation config settings
                safety_settings=gemini_cfg.safety_settings):  # Safety settings
    """Configures and creates a GenerativeModel instance.

    Args:
        google_ai_key (str): The Google AI key.
        model_name (str, optional): Name of the model to use. Defaults to "gemini-pro".
        generation_config: Generation configuration settings.
        safety_settings: Safety settings for the model.

    Returns:
        genai.GenerativeModel: The configured model instance.
    """
    key = google_ai_key
    genai.configure(api_key=key)
    model = genai.GenerativeModel(model_name=model_name,
                                  generation_config=generation_config,
                                  safety_settings=safety_settings)
    return model


def generate_fit_score(model, job_requirements, resume_text):
    """
    Generates a job fit score percentage using an AI model.

    Args:
        model (AIModel): The AI model to use for content generation.
        job_requirements (str): A string containing the job requirements.
        resume_text (str): A string containing the resume_template text.

    Returns:
        str: The AI-generated fit score as a percentage.
    """
    # Create the prompt parts for generating the fit score
    fit_prompt_parts = [
        "Requirement: " + job_requirements + "\n\n"
        "Resume: " + resume_text + "\n\n"
        "Persona: Experienced recruiter or hiring manager, adept at identifying strong candidates using both "
        "ATS and manual review. \n"
        "Task: \n"
        "1. **Keyword Matching:**\n"
        "   - Extract keywords and phrases from the job requirements.\n"
        "   - Calculate a percentage match based on the frequency of these keywords appearing in the resume.\n"
        "   - Weight keywords based on their importance in the job description (e.g., using bold formatting or "
        "(repetition).\n"
        "2. **Skill Alignment:**\n"
        "   - Identify specific skills mentioned in the job requirements.\n"
        "   - Assess the degree to which the resume demonstrates those skills through experiences, achievements, "
        "or certifications.\n"
        "   - Assign a percentage score for each skill, considering factors like relevance, depth of experience, "
        "and quantifiable results.\n"
        "3. **Experience and Education:**\n"
        "   - Evaluate the alignment of the candidate's professional experience "
        "(e.g., job titles, companies, industries) with the job requirements.\n"
        "   - Assess the relevance of their educational background to the role.\n"
        "   - Assign a percentage score for each category, considering factors like duration of experience, "
        "industry reputation, and educational credentials.\n"
        "4. **Additional Factors (Optional):**\n"
        "   - Consider incorporating other relevant aspects based on the job description, such as:\n"
        "     - Alignment with company culture or values\n"
        "     - Specific certifications or licenses\n"
        "     - Geographic proximity to the job location\n"
        "     - Industry awards or recognition\n\n"
        "Output: A single job fit score between 0 and 100 (XX.XX), calculated as an average of "
        "the 4 scores above. Refer to the Output Example there is only 1 number.\n"
        "Output Example: 93.50"

    ]
    # TODO remove non numeric characters
    # Generate the fit score using the AI model
    fit_response = call_generative_api_with_retries(model, fit_prompt_parts)
    ai_fit = strip_non_numeric(fit_response.text)

    return ai_fit


def call_generative_api_with_retries(model, prompt_parts, max_retries=3, retry_delay=5):
    """Calls a Google generative AI model with retry logic for potential issues.

    Args:
        model: The Google generative AI model object.
        prompt_parts: The prompt parts for the API call.
        max_retries (int, optional): Maximum number of retries. Defaults to 3.
        retry_delay (int, optional): Delay in seconds between retries. Defaults to 5.

    Returns:
        The response from the model's generate_content() method.

    Raises:
        GoogleAPIError: If the API request fails after maximum retries.
    """

    for attempt in range(max_retries):
        response = ""
        try:
            response = model.generate_content(prompt_parts)
            return response  # Successful response, return it
        except GoogleAPIError as e:
            print(f"Attempt {attempt+1}: API request failed with error: {e}")
            if attempt < max_retries - 1:
                print("Retrying in", retry_delay, "seconds...")
                time.sleep(retry_delay)
            else:
                print("Maximum retries exceeded. Raising the error.")
                raise  # Re-raise the exception for further handling
