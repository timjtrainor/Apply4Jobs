import re
import sqlite3


def remove_non_letters_from_start(text_list):
    """
    Removes non-letter characters from the beginning of each string in a list.

    Args:
        text_list: A list of strings.

    Returns:
        A new list with the non-letter characters removed from the beginning of each string.
    """
    modified_list = []
    for text in text_list:
        for i in range(len(text)):
            if text[i].isalpha():  # Check if the current character is a letter
                modified_list.append(text[i:])  # Append the string from the first letter onwards
                break  # Exit the inner loop as soon as an alphabetic character is found
        else:  # If no letters found, append an empty string
            modified_list.append("")
    return modified_list


def create_list_from_lines(text):
    """
    Creates a list of items from the provided text, removing blank lines.

    Args:
        text (str): The text to be processed.

    Returns:
        list: A list of items extracted from the text, excluding blank lines.
    """

    return [line.strip() for line in text.splitlines() if line.strip()]


def replace_text_in_docx(doc, target_text, replacement_text):
    """
    Replaces target_text with replacement_text in a docx document.

    Args:
        doc (docx.Document): The document to modify.
        target_text (str): The text to replace.
        replacement_text (str): The text to replace target_text with.
    """

    # Iterate over each paragraph in the document
    for paragraph in doc.paragraphs:

        # Iterate over each run in the paragraph
        for run in paragraph.runs:

            # Check if target_text is present in the run's text
            if target_text in run.text:
                # Replace target_text with replacement_text in the run's text
                run.text = run.text.replace(target_text, replacement_text)


def user_selects_option(choices_list):
    """
    Prompts the user to choose an option from a list or enter their own.

    Args:
        choices_list (list): A list of available achievements to choose from.

    Returns:
        choice_string (str): The selected option from the list or the user's entered text.
    """

    # Get the number of options
    option_count = len(choices_list)

    # Remove non letter characters from the beginning of each string
    choices_list = remove_non_letters_from_start(choices_list)

    # Turn the list into a string
    choices_string = "\n".join(
        f"{i - 1:>2}. {item}" for i, item in enumerate(choices_list, 1)
    )

    # Display the list of options to the user
    print(choices_string)

    # Have the user choose an option
    selection = input(f"Choose an option (0 - {option_count - 1}) or write your own input: ")

    # Process the input
    try:
        # Attempt conversion to integer
        number = int(selection)
        # Append the selected original_achievement from the list if number
        choice_string = choices_list[number]
    except ValueError:
        # Assume user entered their own original_achievement as string
        choice_string = selection.strip()
        # TODO : Add a AI process to review the inputted value
    print("Result:", choice_string)

    return choice_string


def user_selects_options(choices_list, number_of_choices=3):
    """
    Prompts the user to choose an option from a list or enter their own.

    Args:
        choices_list (list): A list of available achievements to choose from.
        number_of_choices (int, optional): The number of choices the user can make. Defaults to 3.

    Returns:
        list: A list of the selected options from the list or the user's entered texts.
    """

    # Get the number of options
    option_count = len(choices_list)

    # Remove non letter characters from the beginning of each string
    choices_list = remove_non_letters_from_start(choices_list)

    # Turn the list into a string
    choices_string = "\n".join(
        f"{i - 1:>2}. {item}" for i, item in enumerate(choices_list, 1)
    )

    # Display the list of options to the user
    print(choices_string)

    # Ask the user to choose an option for each choice
    selection_list = []
    for x in range(number_of_choices):
        selection = input(f"Choose an option (0 - {option_count - 1}) or write your own achievement: ")

        # Process the input
        try:
            # Attempt conversion to integer
            number = int(selection)
            # Append the selected original_achievement from the list if number
            selection_list.append(choices_list[number])
        except ValueError:
            # Assume user entered their own original_achievement as string
            selection_list.append(selection.strip())
            # TODO : Add an AI process to review the inputted value

    return selection_list


def strip_non_numeric(text):
    """
    Strips all non-numeric characters from a string.

    Args:
    text: The string to be stripped.

    Returns:
    A new string containing only the numeric characters from the original string.
    """
    pattern = re.compile(r"[^\d\-+\.]")
    return pattern.sub("", text)


def get_config_value_from_key(cursor, key):
    """Retrieves the value associated with the given key from the config table in the database.

    Args:
        cursor: A cursor object connected to the SQLite database.
        key: The key to search for in the config table.

    Returns:
        The value associated with the key if found, otherwise None.
    """

    try:
        # Execute the SQL query to retrieve the value for the given key
        cursor.execute(f"SELECT value FROM config WHERE key = '{key}'")
        result = cursor.fetchone()

        if result:
            # Return the value associated with the key directly
            return result[0]
        else:
            # Print a message if the key is not found in the config table
            print(f"{key} not found in the config table.")
            return None
    except sqlite3.Error as e:
        # Print an error message if there is an error retrieving the value from the database
        print(f"Error retrieving {key} from database:", e)
        return None
