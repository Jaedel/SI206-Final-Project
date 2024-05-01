import requests
import sqlite3
import json
import os
import matplotlib
import matplotlib.pyplot as plt


NYT_API_KEY = 'Y4YC23d1jbw0W2Y9pu5NgxFWFm1Mrz8p'

def new_api_key():
    '''
    This function makes a request to The New York Times
    Bestsellers List for 4/1/22. The function then checks
    and ensures that the response.status_code == 200 and 
    loads the data as a json file. After, it loops through
    the specific genre lists and finds information about the
    isbn number, title, rank, and publisher for each book. 
    To avoid duplicate titles, it adds each title to a title
    dictionary and makes sure to only get information from a
    book if the title isn’t already in the dictionary. This function
    creates a publisher ID key by creating a publisher dictionary
    and checking if the publisher is already in the dictionary.
    The keys of this dictionary are the publisher name and the
    values are a publisher id created by the publisher variable.
    If the publisher name is already in the publisher dictionary,
    it assigns the publisher id number value to the new_dict publisher
    id value. If the publisher name is not already in the dictionary,
    it adds it to the dictionary and increments publisher so that
    there is a new publisher id that can be added as the value in new_dict. 
    INPUTS: 
        none

    OUTPUTS: 
        new_dict: dictionary with primary isbn13 number as the key, and title,
        rank on the NYT Bestsellers list, and publisher ID as the values
    '''
    new_dict = {}
    publisher_dict = {}
    title_dict = {}
    num_value = 0
    publisher = 0
    published_date = '2022-04-01'
    response = requests.get(url=f'https://api.nytimes.com/svc/books/v3/lists/full-overview.json?published_date={published_date}&api-key={NYT_API_KEY}')
    if response.status_code == 200:
        data = json.loads(response.text)
        for item in data["results"]["lists"]:
            for i in item["books"]:
                if i["title"] not in title_dict.keys():
                    title_dict[i["title"]] = 1
                    if i["publisher"] not in publisher_dict.keys():
                        num_value += 1
                        publisher_dict[i["publisher"]] = num_value
                    publisher = publisher_dict[i["publisher"]]
                    new_dict[i["primary_isbn13"]] = [i["title"], i["rank"], publisher]              
    return new_dict

def get_rating(isbn):
    '''
    This function makes a request to the Open Library API ISBN page for a specific book based on the ISBN number,
    which is taken as an argumnet for this function. After ensuring the request is successfully stored to a variable,
    it takes the works value from the json so that another request can be made to open up the works page for that same book.
    From there it then ensures the request is successfully stored to a variable, stores the rating for the book by searching
    through the JSON (first checking if it exists and returning None if it doesn't), and returns the rating as a float.

    ARGUMENTS: 
        title: ISBN of the book you're searching for 

    RETURNS: 
        float with the rating OR None if the 
        request was unsuccesful
    '''


    isbn_url = f'https://openlibrary.org/isbn/{isbn}.json'
    isbn_response = requests.get(isbn_url)
    if isbn_response.status_code == 200:
        isbn_dict = isbn_response.json()
        works_key = isbn_dict["works"][0]["key"]
        works_id_list = works_key.split("/")
        works_id = works_id_list[-1]

        works_url = f'https://openlibrary.org/works/{works_id}/ratings.json'
        works_response = requests.get(works_url)
        if works_response.status_code == 200:
            works_dict = works_response.json()
            rating = works_dict["summary"]["average"]
            if rating is None:
                return None
            else:
                return float(rating)
        else:
            return None
    else:
        return None       
    

def new_rating_function():
    '''
    This function first gets all the data from the new_api_key()
    function which returns a dictionary with isbn number as the 
    key and title, rank on NYT Bestsellers list, and publisher id
    as the values. It then loops through the keys of that dictionary
    (which are the isbn numbers) and for each isbn number, it finds 
    the Open Library rating using the get_rating() function. If the
    isbn number provided by the new_api_key() function is ‘None’, do
    not find the Open Library rating because it needs an isbn number
    to work properly. Check to see if the isbn number has a corresponding
    rating on Open Library, and if it does, create a list with isbn number,
    book title, rank on NYT Bestsellers list, publisher if, and Open Library rating.
    Add this list to the rating_list so that the output is a list of lists. 

    INPUTS: 
        none 

    OUTPUTS: 
        rating_list: list with isbn number, book title,
        rank on New York Times Bestsellers list,
        publisher id, and Open Library rating
    '''
    rating_list = []
    nyt_dict = new_api_key()
    for item in nyt_dict:
        
        if item == None:
            continue
        else:
            rating = get_rating(item)
            if rating == None:
                continue
            else:
                get_values = nyt_dict.get(item)
                rating_list.append([item, get_values[0], get_values[1], get_values[2], rating])
    return rating_list