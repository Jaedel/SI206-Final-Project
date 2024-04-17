import unittest
import sqlite3
import json
import os
import requests


# Gets a singular rating by isbn number
def get_rating(isbn):
    '''
    creates API request
    ARGUMENTS: 
        title: ISBN of the book you're searching for 

    RETURNS: 
        float with the rating OR None if the 
        request was unsuccesful
    '''

    isbn_url = f'https://openlibrary.org/isbn/{isbn}.json'
    isbn_response = requests.get(isbn_url)
    if isbn_response.status_code == 200:
        works_key = isbn_response["works"]["key"]

        works_url = f'https://openlibrary.org/works/{works_key}/ratings.json'
        works_response = requests.get(works_url)
        if works_response.status_code == 200:
            return(float(works_response["average"]))
    else:
        return None