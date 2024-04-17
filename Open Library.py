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
        isbn_dict = isbn_response.json()
        print(type(isbn_dict))
        works_key = isbn_dict["works"][0]["key"]
        print(works_key)
        works_id_list = works_key.split("/")
        works_id = works_id_list[-1]
        print(works_id)

        works_url = f'https://openlibrary.org/works/{works_id}/ratings.json'
        works_response = requests.get(works_url)
        if works_response.status_code == 200:
            works_dict = works_response.json()
            print(works_dict)
            print(float(works_dict["summary"]["average"]))
            return(float(works_dict["summary"]["average"]))
    else:
        return None