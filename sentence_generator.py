import requests  # Requests is essentially the same thing as fetch() in Js for the HTML url that is the API
# Requests is like the call that you make to the API 
import re
import os

def generate_sentence(word_input): # Gererate 1 or more questions for user input word(s)

    # Split the string into individual words based on commas or spaces
    words = [w.strip() for w in re.split(r'[,\s]+', word_input) if w.strip()]   # if w.strip() is checking whether the word is empty, if the piece divided in empty or not, it strips the word of its spaces

    # Remove the duplicate words from the splited user input 
    # NOTE: Dictionaries can't have duplicate keys, so if we first assign the splitted words as keys in a dictionary, the duplicate words will disappear
    # THEN if we convert it back into a list, then we will have a non-repetitive list 
    words = list(dict.fromkeys(words))

    # Debugging line to make sure there are actual words in the list 'words'
    if not words:
        return {"error": "No valid words entered"}
    
    # Creation of quiz of ALL of the words
    # Sub functions used: generate_single_quiz
    all_quizzes = []
    for word in words:
        quiz = generate_single_quiz(word)
        if "error" not in quiz: # If the function generate_single_quiz did not return an error
            all_quizzes.append(quiz) # Add the generated quiz to the list of all the quizzes
            # all_quizzes is a list of dictionaries, each dictionary is a sentence and a set of choices 
        else:
            return quiz # Return the error message if there was an error in generating a quiz
        
    return {"quizzes": all_quizzes, "total" : len(all_quizzes)} # Return the list of all of the generated quizzes (each of the quizzes a dictionary)

def generate_single_quiz(word):

    #Config your variables for the API call
    api_key = os.getenv('GROQ_API_KEY') # The key must be kept SECRET, its the password to let you use the API
      # Its like a member, it proves that you allowed to use it
    url = "https://api.groq.com/openai/v1/chat/completions" # This url is the API address you will be sending your call to
        # Its like the street address you will be sending your letter to
    
    # Set up a dictionary (like a js object, OOP) with identification info
    # DUDE this is literally the header of the packet
    # The metadata of the request
    headers = {
        "Content-Type": "application/json", # This header tell the API that you are sending the data in JSON format
        "Authorization": f"Bearer {api_key}" # Authorizes you to use the API
         # f before a quote represents a formatted string, that means "insert variables inside {}" in this case your API key
    }

    # This is the actual payload (like the ones you know in a packet) of the request you are making, the data
    # This is the body of the request
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
            "role": "user",
            "content": f"""You are helping English-speaking students learn vocabulary through translanguaging.

Create Spanish sentences for the following word(s): '{word}'

If one word is provided, create ONE question.
If multiple words are provided (separated by commas or spaces), create a SEPARATE question for EACH word.

Requirements for EACH question:
1. Write a sentence entirely in SPANISH that naturally includes the English word
2. The Spanish context should provide OBVIOUS clues about what the word means
3. Provide exactly 4 answer choices (A, B, C, D):
   - One CORRECT answer (obvious from context)
   - One plausible but incorrect answer (related concept)
   - Two clearly wrong answers (completely unrelated)
4. Randomize which letter has the correct answer
5. Add quotations to the English word in the sentence to highlight it

Format your response EXACTLY like this:

Word: "siblings"
Sentence: Tengo dos siblings, un hermano y una hermana.
A. hermanos
B. primos
C. zapatos
D. libros
Correct: A

Format for multiple words:

Word: "siblings"
Sentence: Tengo dos siblings, un hermano y una hermana.
A. hermanos
B. primos
C. zapatos
D. libros
Correct: A

Word: "breakfast"
Sentence: Por la mañana, como breakfast antes de ir a la escuela.
A. tarea
B. desayuno
C. bicicleta
D. camiseta
Correct: B

Now create questions for: '{word}' and format it exactly as the examples shown above, and the sentence cannot include the spanish translation of the target word, but the multiple choice section can."""
            }
        ],
        "max_tokens": 300 # For computers, tokens is basically pieces of the words, so this a the word limit
    }

    # Make the error block for this API call in case there is an error that might cause the program to crash
    try: # This is your risky operation, the one that might crash
        response = requests.post(url, headers=headers, json=data) # This is your request to the API, its like a packet, url for destination, headers of packet, and payload or content of request
        # .post means you are sending your call to the API
        # JSON is the format in which your data is sent, the dictionary "data" is converted in JSON String

        """
        After response is run, it is an object that contains:
        - status code: did it work?
        - The response headers (metadata about the response)
        - The response body (what was the data ouputted from our call to the API)
        - etc. 
        """

        if response.status_code == 200: # 200 means that request was successful, so if the code is 200 that means the request worked
            result = response.json() # Convert the response body from JSON string into a Python dictionary for use
            sentence = result["choices"][0]["message"]["content"].strip() # Go through the result dictionary to get the actual question ouput

            parsed_sentence = parse_ai_response(sentence, word)
            # The structure of the result dictionary is defined in the API documentation of groq
            return parsed_sentence # Return the generated sentence
        
        else: # If the status code is not 200, in other words if the request was NOT successful
            return {"error": f"Status {response.status_code}"}

    except Exception as e: # This will catch any errors that happen in the try block
        # the exception, or error, will be stored in the variable e
        return {"error": str(e)} # Returns the error message 

# Below is the function to parse the generated AI sentence in UI friendly format
# This function lowk makes no sense LMAO => Learn how to use Regex because majority of this function is just Regex usage
def parse_ai_response(content, word_input):
    # Receives the content in one long string format, NOT seperated into Python friendly usage
    try:
        
        sentence_match = re.search(r'Sentence:\s*(.+)', content) # Regex to find the sentence line -> WTF is REGEX!!
        sentence = sentence_match.group(1).strip() if sentence_match else "" 
        # If the regex sentence is found, (if sentence_match is true) then the sentence variable will return the actual sentence
        # If NOT found, then instead of crashing, the sentence variable will just be an empty string (aka if the sentence match did not find any sentence in the content)

        #Extract choices using Regex
        # Search for the multiple choice options using regex pattern (see the same pattern tool being used for the sentence_match)
        choice_a = re.search(r'A\.\s*(.+)', content)
        choice_b = re.search(r'B\.\s*(.+)', content)
        choice_c = re.search(r'C\.\s*(.+)', content)
        choice_d = re.search(r'D\.\s*(.+)', content)
        # each key in the dictionary will have its own value of the mutliple choice option
        # double checking our extraction using the same type of if else statement as the sentence extraction
        choices = {
            "A": choice_a.group(1).strip() if choice_a else "",
            "B": choice_b.group(1).strip() if choice_b else "",
            "C": choice_c.group(1).strip() if choice_c else "",
            "D": choice_d.group(1).strip() if choice_d else "",
        }

        # extract the correct answer using regex pattern
        correct_match = re.search(r'Correct:\s*([A-D])', content)
        correct_answer = correct_match.group(1).strip() if correct_match else "NOT FOUND"

        # Validate that we got everything 
        # New concept you should learn: truthy and falsy values in Python
        if not sentence or not all(choices.values()):
            return {"error": "Failed to parse AI response", "raw": content}
        
        return {
            "word": word_input,
            "sentence" : sentence,
            "choices": choices,
            "correct": correct_answer
        }

    except Exception as e:
        return {"error" : f"Parsing error: {str(e)}", "raw": content}
    




    