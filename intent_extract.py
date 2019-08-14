import sqlite3
import string
import re
import random
from rasa_nlu.training_data import load_data
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Trainer,Interpreter,Metadata
from rasa_nlu import config


responses1 = ["I'm sorry :( I couldn't find anything like that", 
                           '{} is a great stock!', 
                           '{} or {} would work!', 
                           'what about {}?']

keywords = {
            'greet': [' hello ', ' hi ', ' hey '], 
            'thankyou': ['thank', 'thx'], 
            'goodbye': ['bye', 'farewell','that is all','ok,thanks'],
            'year':['age','How old are you','how old are you'],
            'func':['function','what can you do', 'what can you do for me','What can you do for me',"can you do"],
            'number':['0','1','2','3','4','5','6','7','8','9'],
            'hprice':['history price'],
            'form':['sheet','text'],
            'logout':['logout'],    
            'volume':['volume'],
            'open':['open price'],
            'close':['close price'],
            'changepercent':['changepercent']
            
           }

patterns={}
# Iterate over the keywords dictionary
for intent, keys in keywords.items():
    # Create regular expressions and compile them into pzattern objects
    patterns[intent] = re.compile("|".join(keys))
    
# Print the patterns

responses = {'greet': 'Hello you! :)', 
             'thankyou': 'you are very welcome', 
             'default': 'default message', 
             'goodbye': 'have a nice day!',
             'year': 'I was born on 08/10/2019 :)',
             'logout':'thank you, have a nice day!',
             'func': 'I can help you to check stocks'
            }

"""
# Create a trainer that uses this config
trainer = Trainer(config.load("config_spacy.yml"))
training_data = load_data('demo-rasa.json')
interpreter = trainer.train(training_data)
model_directory = trainer.persist('D:\Chat_robot')
"""

def interpret(message,interpreter):
    data = interpreter.parse(message)
    if 'no' in message:
        data["intent"]["name"] = "deny"
    return data

def find_hotels(params, excluded):
    query = 'SELECT * FROM stocklist'
    if len(params) > 0:
        filters = ["{}=?".format(k) for k in params] + ["name!='?'".format(k) for k in excluded] 
        query += " WHERE " + " and ".join(filters)
    t = tuple(params.values())
    
    # open connection to DB
    conn = sqlite3.connect('stocklist.db')
    # create a cursor
    c = conn.cursor()
    c.execute(query, t)
    return c.fetchall()

# Define respond()
def respond(message, params, suggestions, excluded,interpreter):
    # Interpret the message
    parse_data = interpret(message,interpreter)
    # Extract the intent
    intent = parse_data["intent"]["name"]
    # Extract the entities
    entities = parse_data["entities"]
    # Add the suggestion to the excluded list if intent is "deny"
    if intent == "deny":
        excluded.extend(suggestions)
        #print(excluded)
    # Fill the dictionary with entities
    for ent in entities:
        params[ent["entity"]] = str(ent["value"])
    # Find matching hotels
    results = [
        r 
        for r in find_hotels(params, excluded) 
        if r[0] not in excluded
    ]
    # Extract the suggestions
    names = [r[0] for r in results]
    n = min(len(results), 3)
    suggestions = names[:2]
    return responses1[n].format(*names), params, suggestions, excluded

# Initialize the empty dictionary and lists


def ent_ex(message,interpreter):
    ent=interpreter.parse(message)["entities"][0]["value"]
    return ent

def intent_ex(message,interpreter):
    intent=interpreter.parse(message)["intent"]["name"]
    return intent

def match_intent(message,interpreter):
    matched_intent = None
    for intent, pattern in patterns.items():
        # Check if the pattern occurs in the message 
        if re.search(pattern,message):
            matched_intent = intent
    if(matched_intent==None):
        matched_intent=intent_ex(message,interpreter)
    return matched_intent

for intent, keys in keywords.items():
    # Create regular expressions and compile them into pattern objects
    patterns[intent] = re.compile("|".join(keys))
    
def find_name(message):
    name = None
    # Create a pattern for checking if the keywords occur
    name_keyword = re.compile(r"(name|call)")
    # Create a pattern for finding capitalized words
    name_pattern = re.compile('[A-Z]{1}[a-z]*')
    if name_keyword.search(message):
        # Get the matching words in the string
        name_words = name_pattern.findall(message)
        if len(name_words) > 0:
            # Return the name if the keywords are present
            name = ' '.join(name_words)
    return name

def intent_response(message, params, suggestions, excluded,interpreter):
    intent = match_intent(message,interpreter)
    
    key = "default"
    if intent in responses:
        key = intent
        return responses[key],{}, [], []
    else:
        return respond(message,params,suggestions, excluded,interpreter)
    
def keyrespond(message,interpreter):
    intent = match_intent(message,interpreter)
    key = "default"
    if intent in responses:
        key = intent
        return responses[key]
    else:
        return None
    

"""
params, suggestions, excluded = {}, [], []
# Send the messages
for message in ["howdy","stocks which located in us", "it doesn't work for me"]:
    print("USER: {}".format(message))
    response, params, suggestions, excluded = intent_response(message, params, suggestions, excluded)
    print("BOT: {}".format(response))
"""
