import json
from pathlib import Path
import sqlite3

from affinda import AffindaAPI, TokenCredential

import variables.global_variables as global_vars
from utilities.gobal_functions import get_config_value_from_key

# Connect to the database
conn = sqlite3.connect(global_vars.sqlite_db_file)
# Create a cursor
cursor = conn.cursor()

# Get Values from config table
token = get_config_value_from_key(cursor, "affinda_token")
resume_name = get_config_value_from_key(cursor, "full_resume_file_name")
affinda_workspace_id = get_config_value_from_key(cursor, "affinda_workspace_id")
affinda_collection_id = get_config_value_from_key(cursor, "affinda_collection_id")

file_pth = Path("data/src/resume_full/" + resume_name + ".docx")

credential = TokenCredential(token=token)
client = AffindaAPI(credential=credential)

# First get the organisation, by default your first one will have free credits
my_organisation = client.get_all_organizations()[0]

credential = TokenCredential(token=token)
client = AffindaAPI(credential=credential)

recruitment_workspace = client.get_workspace(affinda_workspace_id)

# Finally, create a collection that will contain our uploaded documents, for example resumes, by selecting the
resume_collection = client.get_collection(affinda_collection_id)

# Now we can upload a resume_template for parsing
with open(file_pth, "rb") as f:
    resume = client.create_document(file=f, file_name=file_pth.name, collection=resume_collection.identifier)

# Save resume_template data as JSON
resume_data = resume.as_dict()
with open("data/target/" + resume_name + ".json", "w") as f:
    json.dump(resume_data, f, indent=4)  # Indent for readability

print("Done!")
