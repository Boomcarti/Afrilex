import mysql.connector
from flask import Flask, request, render_template
import os
import requests
import json
import re
from datetime import datetime
from flask import jsonify
from flask import session, redirect, url_for
from flask import Response
# import Flask libraries
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename

# import SPARQL query function

import requests
import urllib.parse
import json


# Create a connection to the database
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="aizen",
    database="lexdb",
    port=3306
)
singulargram="Q110786"
# Create a cursor object to interact with the MySQL server
cursor = connection.cursor()

# Execute the SPARQL query
cursor.execute("SELECT * from user")
userdata=cursor.fetchall()
print("")
print("User Data!")
print(userdata)
print("")
class WingUCTBOT:
    def __init__(self):
        self.url= "https://test.wikidata.org/w/api.php"
        self.session = requests.Session()
        cursor.execute("SELECT * FROM batchupload")
        self.batchdata = cursor.fetchall()
        self.batchusername = ""
        self.batchGrammaticalCategory=""

    def record_batch_upload(self, batch_size, success_count, language):
        # Get the current time
        now = datetime.now()
        formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
        # Insert the record using self.batchusername
        query = "INSERT INTO batchupload (batch_upload_size, upload_success_rate, UploadDate, username,languages) VALUES (%s, %s, %s, %s,%s)"
        cursor.execute(query, (batch_size, success_count, formatted_date, self.batchusername,language))
        connection.commit()
        get_batch_data()

    def uploadlexemes(self, batchsize, gramcode, language):
        # Execute a SQL query to select a specific number (batchsize) of LexicalEntry IDs from the database
        cursor.execute(f"SELECT LexicalEntry_id FROM lexicalentry LIMIT {batchsize}")

        # Fetch the results from the SQL query
        results = cursor.fetchall()

        # Extract the LexicalEntry IDs from the query results
        lexicalids = [row[0] for row in results]
        success_count = 0  # Counter to keep track of successful operations

        # Iterate over each LexicalEntry ID
        for i in lexicalids:
            lexical_entry_id = i  # Current LexicalEntry ID

            # SQL query to get the language code associated with the current LexicalEntry ID by joining word and language tables
            query = (
                "SELECT l.Language_code "
                "FROM word AS w "
                "JOIN language AS l ON w.Language_id = l.Language_id "
                "WHERE w.LexicalEntry_id = %s;"
            )
            cursor.execute(query, (lexical_entry_id,))
            result = cursor.fetchone()
            language_code = result[0]  # Extracting language code
            gram = gramcode  # Assign provided gramcode

            # SQL query to retrieve a word and its grammatical features based on LexicalEntry ID and the category code (gram)
            query = (
                "SELECT word, grammaticalfeatures FROM word WHERE LexicalEntry_id = %s AND category_code = %s"
            )
            cursor.execute(query, (lexical_entry_id, gram))
            result = cursor.fetchone()
            word = result[0]  # Extracting the word
            wordfeatures = result[1]  # Extracting the grammatical features

            # Updating the grammatical features with a fixed value, likely a Wikidata item ID
            wordfeatures = "Q163014"
            print(wordfeatures)

            # SQL query to fetch the category code associated with the current LexicalEntry ID
            query = (
                "SELECT category_code FROM grammaticalcategory WHERE LexicalEntry_id = %s"
            )
            cursor.execute(query, (lexical_entry_id,))
            result = cursor.fetchone()
            cat = result[0]  # Extracting the grammatical category

            # SQL query to get the language ID for the current word
            query = (
                "SELECT Language_id FROM word WHERE LexicalEntry_id = %s"
            )
            cursor.execute(query, (lexical_entry_id,))
            result = cursor.fetchone()
            lang = result[0]  # Extracting the language ID

            # SQL query to get inflections and their associated grammatical feature IDs by joining inflection and lexicalentry tables
            query = (
                "SELECT gramfeaturesid, inflection "
                "FROM inflection AS i "
                "JOIN lexicalentry AS l ON i.base = l.Word "
                "WHERE l.LexicalEntry_id = %s"
            )
            cursor.execute(query, (lexical_entry_id,))
            results = cursor.fetchall()
            forms = results  # All the forms (inflections) retrieved

            # Creating a list of unique forms by filtering out duplicates
            unique_forms = []
            seen = set()  # Set to keep track of already seen forms
            for form in forms:
                if form not in seen:
                    unique_forms.append(form)
                    seen.add(form)
            forms = unique_forms  # Updating forms list to only contain unique forms

            # Modifying the forms based on certain conditions ( related to test Wikidata item IDs, which are always changing)
            forms = [('Q232161', value) if feature == 'Q146786' else (feature, value) for feature, value in forms]

            #the word table must also have grammaitcal category

            # Execute a SQL query to fetch the 'BantuContext' of meanings related to the given lexical entry
            query = (
                "SELECT m.BantuContext "
                "FROM meanings AS m "
                "JOIN lexicalentry AS l ON m.word = l.Word "
                "WHERE l.LexicalEntry_id = %s;"
            )
            cursor.execute(query, (lexical_entry_id,))

            # Fetch all the results from the query
            results = cursor.fetchall()

            # Extract the senses (meanings) from the results
            senses = results

            # Get a login token from the specified URL
            LOGIN_TOKEN = self.session.get(url=self.url, params={
                "action": "query",
                "meta": "tokens",
                "type": "login",
                "format": "json"
            }).json()['query']['tokens']['logintoken']

            # Data for logging in using the login token
            LOGIN_DATA = {
                "action": "login",
                "lgname": "WingUCTBOT",
                "lgpassword": "$Tinkmeaner7",
                "format": "json",
                "lgtoken": LOGIN_TOKEN
            }

            # Send a POST request to log in
            self.session.post(self.url, data=LOGIN_DATA)

            # Fetch the CSRF token for subsequent requests
            CSRF_TOKEN = self.session.get(url=self.url, params={
                "action": "query",
                "meta": "tokens",
                "format": "json"
            }).json()['query']['tokens']['csrftoken']

            print(senses)  # Print the extracted senses for logging/debugging

            # Check if the first form is empty
            if forms[0][1] == '':
                # Set up the data for creating a new lexeme with minimal info if the form is empty
                LEXEME_DATA = {
                    "action": "wbeditentity",
                    "new": "lexeme",
                    "data": json.dumps({
                        "lemmas": {
                            language_code: {
                                "language": language_code,
                                "value": word
                            }
                        },
                        "lexicalCategory": cat,
                        "language": lang,
                        "forms": [
                            {
                                "add": "",
                                "representations": {
                                    language_code: {
                                        "language": language_code,
                                        "value": word
                                    }
                                },
                                "grammaticalFeatures": [wordfeatures]
                            }
                        ],
                        "senses": [
                            {
                                "add": "",
                                "glosses": {
                                    language_code: {
                                        "language": language_code,
                                        "value": sense[0]
                                    }
                                }
                            } for sense in senses
                        ]
                    }),
                    "format": "json",
                    "token": CSRF_TOKEN
                }
            else:
                # If there's a form, set up a list of form items
                form_items = [
                    {
                        "add": "",
                        "representations": {
                            language_code: {
                                "language": language_code,
                                "value": word
                            }
                        },
                        "grammaticalFeatures": [wordfeatures]
                    }
                ]

                # Iterate over the forms and add each to the list of form items
                for feature, value in forms:
                    form_items.append({
                        "add": "",
                        "representations": {
                            language_code: {
                                "language": language_code,
                                "value": value
                            }
                        },
                        "grammaticalFeatures": [feature]
                    })

                # Set up the data for creating a new lexeme with forms
                LEXEME_DATA = {
                    "action": "wbeditentity",
                    "new": "lexeme",
                    "data": json.dumps({
                        "lemmas": {
                            language_code: {
                                "language": language_code,
                                "value": word
                            }
                        },
                        "lexicalCategory": cat,
                        "language": lang,
                        "forms": form_items,
                        "senses": [
                            {
                                "add": "",
                                "glosses": {
                                    language_code: {
                                        "language": language_code,
                                        "value": sense[0]
                                    }
                                }
                            } for sense in senses
                        ]
                    }),
                    "format": "json",
                    "token": CSRF_TOKEN
                }

            # Send a POST request with the lexeme data
            response = self.session.post(self.url, data=LEXEME_DATA)
            data = response.json()

            # Check if the request was successful
            if ('success' in data) and (data['success'] == 1):
                success_count += 1

            # Print the response for logging/debugging
            print(json.dumps(data, indent=4))

            return success_count  # Return the count of successful operations

            




    def get_batch_data(self):
        return self.batchdata


# Initialize Flask application
app = Flask(__name__)

# Define the upload directory and allowable file extensions
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Base URL of the SPARQL endpoint
base_url = "http://localhost:2020/sparql"

# Check if the uploaded file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Execute a SPARQL query using the provided select clause
def run_sparql_query(select_clause):
    # SPARQL query prefixes
    prefixes = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX vocab: <http://localhost:2020/resource/vocab/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX map: <http://localhost:2020/resource/#>
    PREFIX db: <http://localhost:2020/resource/>
    """

    # Full SPARQL query
    query = prefixes + select_clause

    # URL encode the query
    encoded_query = urllib.parse.quote_plus(query)

    # Construct the full URL
    full_url = base_url + "?query=" + encoded_query + "&output=json"

    # Send the GET request
    response = requests.get(full_url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the response as JSON
        data = response.json()

        # Return the JSON data
        return data
    else:
        return {"error": f"Failed to retrieve data, status code: {response.status_code}"}

app.secret_key = '42'

# Instantiate a new WingUCTBOT object
bot = WingUCTBOT() # Instance of your existing bot class
print(bot.batchdata)
@app.route('/')
def index():
    return render_template('index.html')

# Retrieve batch upload data from the database
def get_BatchUpload_data():
    print("Getting batch data")
    cursor.execute("SELECT * FROM batchupload")
    bot.batchdata = cursor.fetchall()
    for i in range(len(bot.batchdata)):
        batch = list(bot.batchdata[i])
        batch[2] = batch[2].strftime("%Y-%m-%d %H:%M:%S")  # convert datetime to string
        bot.batchdata[i] = tuple(batch)
    return json.dumps(bot.batchdata), 200

# Route for obtaining batch data from the database
@app.route('/get_batch_data', methods=['GET'])
def get_batch_data():
    print("Getting batch data")
    cursor.execute("SELECT * FROM batchupload")
    bot.batchdata = cursor.fetchall()
    for i in range(len(bot.batchdata)):
        batch = list(bot.batchdata[i])
        batch[2] = batch[2].strftime("%Y-%m-%d %H:%M:%S")  # convert datetime to string
        bot.batchdata[i] = tuple(batch)
    print(bot.batchdata)
    return json.dumps(bot.batchdata), 200


# Define login functionality and route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the username and password from the form
        username = request.form['username']
        password = request.form['password']

        # Check credentials
        if authenticate(username, password):
            bot.loggedin="Y"
            bot.batchusername = username 
            return "Logged in successfully!", 200
        else:
            return "Incorrect username or password.", 401

    return render_template('login.html')


# Define the user registration route
@app.route('/register', methods=['POST'])
def register():
    # Get the registration details from the form data
    email = request.form['email']
    username = request.form['username']
    password = request.form['password']

    # Call the register_user function to handle registration
    status, message = register_user(email, username, password)
    return message, status

# This function aids in registering a new user
def register_user(email, username, password):
    try:
        # Check if email or username already exists
        cursor.execute("SELECT * FROM user WHERE UserEmail=%s OR username=%s", (email, username))
        existing_user = cursor.fetchone()

        if existing_user:
            return 400, "Email or username already exists."

        # Insert the new user details into the database
        cursor.execute("INSERT INTO user (UserEmail, username, UserPassword) VALUES (%s, %s, %s)", (email, username, password))
        connection.commit()

        return 200, "Registration successful!"
    except Exception as e:
        print(f"Error during registration: {e}")
        return 500, "Registration failed due to server error."

# This function checks a user's credentials during the login process
def authenticate(username, password):
    try:
        cursor.execute("SELECT * FROM user WHERE username=%s AND UserPassword=%s", (username, password))
        if cursor.fetchone():
            return True
        return False
    except Exception as e:
        print(f"Error during authentication: {e}")
        return False

# Define route for executing SPARQL operations
@app.route('/sparql', methods=['GET', 'POST'])
def sparql():
    if request.method == 'POST':
        query = request.form['query']

        # Try to run the query
        try:
            data = run_sparql_query(query)
            # Convert data to a string format
            data_str = json.dumps(data)
            return jsonify(data_str), 200
        except Exception as e:
            return jsonify(str(e)), 500

    return render_template('index.html') 


# Define a route to download a complete dump of the database
@app.route('/download_db_dump', methods=['GET'])
def download_db_dump():
    try:
        # Execute command to fetch entire database
        
        query = "SELECT * FROM information_schema.tables WHERE table_schema = 'lexdb'"
        
        cursor.execute(query)
        print("Here")
        tables = cursor.fetchall()
        data = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT * FROM {table_name}")
            data[table_name] = cursor.fetchall()
        
        # Convert data to JSON string for download
        data_str = json.dumps(data, default=str)
        print(data_str)  # Convert datetime to str
        
        # Return data as a downloadable file
        return Response(data_str, mimetype="application/json",
                        headers={"Content-Disposition": "attachment;filename=db_dump.json"})
    except Exception as e:
        return f"Error while fetching database dump: {e}", 500


# Define the batch upload route and functionality
@app.route('/batch_upload', methods=['POST'])
def batch_upload():
    # Retrieve the batch size from the form data. This indicates the number of items to be uploaded in this batch.
    batch_size = int(request.form['batch_size'])

    # Retrieve the grammatical category from the form (e.g., "Noun", "Verb").
    gramcode = request.form['grammatical_category']

    # Create a dictionary to map the full name of the grammatical category to its abbreviation.
    gram_mapping = {
        "Noun": "N",
        "Verb": "V",
        "Adjective": "Adj",
        "Adverb": "Adv",
        "Pronoun": "Pro"
    }

    # Using the mapping, convert the full name grammatical category to its abbreviation. 
    # If the category is not in the mapping, the original value is retained.
    gramcode = gram_mapping.get(gramcode, gramcode)

    # Retrieve the language from the form data. This specifies the language of the items being uploaded.
    language = request.form['language']

    # Log the values for debugging and monitoring.
    print("language:", language)
    print("gram code:", gramcode)
    print("batch size:", str(batch_size))

    # Call the `uploadlexemes` method of the `bot` object to handle the actual uploading process.
    # We assume this method returns the count of successfully uploaded items.
    success_count = bot.uploadlexemes(batch_size, gramcode, language)
    
    # Calculate the success rate of the batch upload. It's the ratio of the number of successful uploads to the batch size, multiplied by 100 to get a percentage.
    rate = (int(batch_size) / int(success_count)) * 100

    # Log the success rate for monitoring.
    print("rate:", str(rate))

    # Record the details of the batch upload, including the batch size, success rate, and language.
    bot.record_batch_upload(batch_size, rate, language)
    
    # Return a success message to the client indicating the completion of the batch upload.
    return 'Batch upload successful', 200



@app.route('/generate_verb_forms', methods=['POST'])
def generate_verb_forms():
    verblist = ['seka','rara','mhanya','gara','chema','dzora','pisa','ridza','pfeka','tora']
    
    try:
        for each in verblist:
            construct_verb_form(each)
        
        return "Verb forms generated successfully!", 200
    
    except Exception as e:
        return f"An error occurred: {str(e)}", 500


    

def construct_verb_form(verb):
    print(verb)
    query = "SELECT nounClass, subjectPastTense, subjectPresentTense, subjectFutureTense, objectMarker FROM shona_morphology"
    cursor.execute(query)
    results = cursor.fetchall()

    # Extract all object markers for cycling through each
    object_markers = [row[4] for row in results]

    # Dictionary to map tense names to their Wikidata IDs
    tense_to_wikidata = {
        "Past": "Q1994301",
        "Present": "Q192613",
        "Future": "Q501405"
    }

    # Sort results and iterate over each row in the table
    sorted_results = sorted(results, key=lambda x: (int(x[0][:-1] or 0), x[0][-1]))

    for row in sorted_results:
        noun_class, past, present, future, _ = row
        
        # Convert noun_class to its corresponding Wikidata ID
        class_to_wikidata = {
            "1": "Q113331807",
            "1a": "Q113195674",
            "2": "Q113380991",
            "2a": "Q113195677",
            "2b": "Q113380991",
            "3": "Q113194639",
            "4": "Q113195001",
            "5": "Q113383619",
            "6": "Q113383630",
            "7": "Q113383641",
            "8": "Q113383650",
            "9": "Q113383660",
            "10": "Q113383679",
            "11": "Q113383687",
            "12": "Q113383692",
            "13": "Q113383694",
            "14": "Q113383695",
            "15": "Q113383696",
            "16": "Q113383699",
            "17": "Q113383703",
            "18": "Q113383703",
            "19": "",
            "21": "Q113383703"
        }

        noun_class = class_to_wikidata.get(noun_class, noun_class)

        # Skip classes '19', '1a', '18', and '21'
        if noun_class in ['', "Q113195674", "Q113383703"]:
            continue
        
        for obj_marker in object_markers:
            for tense_name, tense_prefix in [("Past", past), ("Present", present), ("Future", future)]:
                constructed_verb = tense_prefix + " " + obj_marker + verb
                print(f"Verb Form: {constructed_verb}, tense: {tense_to_wikidata[tense_name]}, subject class: {noun_class}, Object concord: {obj_marker}")

                insert_query = """
                INSERT INTO inflection (gramfeaturesid, inflection, person, number, tense, LexicalEntry_id, gender, aspect, mood, grammarcase, voice, base, auto)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (tense_to_wikidata[tense_name], constructed_verb, None, None, tense_name, None, None, None, None, None, None, verb, "1"))


                #fix  the fellwoing
                match = re.match(r'[^aeiou]*', tense_prefix)
                filtered_tense_prefix = match.group(0) if match else ''

                insert_query = """
                    INSERT INTO verb_forms (verb, subject_noun_class, object_noun_class, stem, subject_concord, object_concord)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (constructed_verb, noun_class, obj_marker, verb, tense_prefix, obj_marker))

    connection.commit()
    



# Start the Flask app if this script is executed directly
if __name__ == "__main__":
    app.run(debug=True, port=8602)

