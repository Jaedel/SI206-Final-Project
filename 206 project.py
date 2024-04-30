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
    creates API request
    INPUTS: 
        title: ISBN of the book you're searching for 

    OUTPUTS: 
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


def set_up_database(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path + "/" + db_name)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS Books (isbn13 INTEGER PRIMARY KEY, title TEXT, nyt_rank INTEGER, rating REAL)')
    cur.execute('CREATE TABLE IF NOT EXISTS Publishers (isbn13 INTEGER PRIMARY KEY, pub_id INTEGER)')
    return cur, conn

def set_up_tables(data, cur, conn):
    # get most recent count of things in the database
    # make api call but only take next 25 items to add to database

    for i in data:
        isbn13 = i[0]
        title = i[1]
        nyt_rank = i[2]
        pub_id = i[3]
        rating = i[4]
        cur.execute('INSERT OR IGNORE INTO Books(isbn13, title, nyt_rank, rating) VALUES (?,?,?,?)', (isbn13, title, nyt_rank, rating))
        cur.execute('INSERT OR IGNORE INTO Publishers(isbn13, pub_id) VALUES (?,?)', (isbn13, pub_id))
        conn.commit()


def analyze_first_data(cur, conn):
    '''
    This function adds a new column called new_rating to
    the Books Table. Then it gets the isbn13, nyt_rank_ and rating
    from the Books Table. For each isbn number, calculate a new rating
    (called new_rating) which adds the nyt_rank and the rating from Open
    Library. Then, for each isbn number, add the new_rating calculation to
    the new_rating column in the Books Table. 
    INPUTS: 
        cur: cursor object for the database
        conn: connection object for the database

    OUTPUTS: 
        none
    '''
    cur.execute("ALTER TABLE Books ADD COLUMN new_rating REAL")
    rows = cur.execute("SELECT isbn13, nyt_rank, rating FROM Books").fetchall()
    for row in rows:
        nyt_rank = row[1]
        rating = row[2]
        new_rating = rating - nyt_rank
        isbn13 = row[0]
        cur.execute("UPDATE Books SET new_rating = ? WHERE isbn13 = ?", (new_rating, isbn13))
    conn.commit()

def analyze_data(cur, conn):
    '''
    This function gets the isbn13, nyt_rank_ and rating
    from the Books Table. For each isbn number, calculate a new rating
    (called new_rating) which adds the nyt_rank and the rating from Open
    Library. Then, for each isbn number, add the new_rating calculation to
    the new_rating column in the Books Table. 
    INPUTS: 
        cur: cursor object for the database
        conn: connection object for the database

    OUTPUTS: 
        none
    '''
    rows = cur.execute("SELECT isbn13, nyt_rank, rating FROM Books").fetchall()
    for row in rows:
        nyt_rank = row[1]
        rating = row[2]
        new_rating = rating - nyt_rank
        isbn13 = row[0]
        cur.execute("UPDATE Books SET new_rating = ? WHERE isbn13 = ?", (new_rating, isbn13))
    conn.commit()

def create_first_visualization(cur, conn):
    '''
    This function creates a bar chart that displays the
    title and the new_rating for the Top 5 Books based on the new_rating
    in our database. First, this function creates a title list and a rating list
    for the x and y axes, respectively. It also creates a list for the widths
    so that each width is 0.3. After, this function gets the title and new_rating
    from the Books Table and these should be in descending order because that corresponds
    the larger the r
    and 

    INPUTS: 
        cur: cursor object for the database
        conn: connection object for the database

    OUTPUTS: 
        none
    '''
    
    title_list = []
    rating_list = []
    widths = [0.3, 0.3, 0.3, 0.3, 0.3]
    items = cur.execute('SELECT title, new_rating FROM Books ORDER BY new_rating DESC').fetchall()
    count = 0
    for item in items:
        if count < 5:
            count += 1
            book_title = item[0]
            if len(book_title) > 10:
                first_ten_characters = book_title[:11] + '..'
                title_list.append(first_ten_characters)
            else:
                title_list.append(book_title)
            rating_list.append(item[1])
        else:
            break
    plt.bar(title_list, rating_list, color='red', width= widths) 
    plt.xlabel("Book Title (First 10 Letters)") 
    plt.ylabel("New Rating Calculation")  
    plt.title("New Rating Calculation for Top 5 Books") 
    plt.savefig("barchart_newrating_and_title.png")
    plt.show()
    conn.commit()

def create_second_visualization(cur, conn):
    pub_dict = {}
    new_dict = {}

    rows = cur.execute('SELECT Publishers.pub_id, Books.new_rating FROM Publishers JOIN Books ON Publishers.isbn13 = Books.isbn13').fetchall()
    for row in rows:
        pub_id = row[0]
        rating = row[1]
        if pub_id in pub_dict.keys():
            pub_dict[pub_id].append(rating)
        else:
            pub_dict[pub_id] = [rating]

    for pub in pub_dict.keys():
        if len(pub_dict.get(pub)) > 2:
            vals_of_pub = pub_dict[pub]
            new_dict[pub] = vals_of_pub
        else:
            continue

    count = 0

    x_axis_list = []
    y_axis_list = []
    x_tick_labels = []
    axis_count = 0

    for i in new_dict.keys():
        if count < 5:
            count += 1
            for val in new_dict.get(i):
                x_axis_list.append(i)
                individual_value = val
                y_axis_list.append(individual_value)
        else:
            break

    while axis_count < 51:
        axis_count += 3
        x_tick_labels.append(axis_count)

    ax = plt.axes()
    plt.scatter(x_axis_list, y_axis_list) 
    ax.set_xticks(x_tick_labels)
    plt.grid()
    plt.xlabel("Publisher ID") 
    plt.ylabel("New Ratings for Publisher's Books")  
    plt.title("New Rating Calculations for 5 Publishers") 
    plt.savefig("scatterplot_newrating_and_publisher.png")
    plt.show()
    conn.commit()


def main():
    cur, conn = set_up_database("Storage")
    data = new_rating_function()
    book_count = cur.execute('SELECT COUNT (*) FROM Books').fetchall()[0][0]
    

    if book_count < 1:
        first_25 = data[:25]
        set_up_tables(first_25, cur, conn)
        analyze_first_data(cur, conn)
    elif book_count < 26:
        next_25 = data[25:50]
        set_up_tables(next_25, cur, conn)
        analyze_data(cur, conn)
    elif book_count < 51:
        third_25 = data[50:75]
        set_up_tables(third_25, cur, conn)
        analyze_data(cur, conn)
    elif book_count < 76:
        last_25 = data[75:100]
        set_up_tables(last_25, cur, conn)
        analyze_data(cur, conn)

    elif book_count < 101:
        create_first_visualization(cur, conn)
        create_second_visualization(cur, conn)

    conn.close()

main()
#data = new_rating_function()
#print(data)

# def get_isbn_numbers():
    # loop thru get book data and get isbn numbers for each book

# def get_open_library_book_data():
    # get book data based on isbn numbers for nyt books

# def set_up_database():

# def create_table():