import requests
import sqlite3
import json
import os
import matplotlib
import matplotlib.pyplot as plt


NYT_API_KEY = 'Y4YC23d1jbw0W2Y9pu5NgxFWFm1Mrz8p'

def new_api_key():
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
    '''
    This function establishes a path and file for the database using the name that is input as the argument.
    This then creates the connection and cursor objects for the database. Afterwards, two tables are then created
    so that data on Books can then be inserted into these tables for future calculations.
    
    ARGUMENTS: 
        title: Name of the database 

    RETURNS: 
        The database's cursor and connection objects
    '''
    
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path + "/" + db_name)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS Books (isbn13 INTEGER PRIMARY KEY, title TEXT, nyt_rank INTEGER, rating REAL)')
    cur.execute('CREATE TABLE IF NOT EXISTS Publishers (isbn13 INTEGER PRIMARY KEY, pub_id INTEGER)')
    return cur, conn

def set_up_tables(data, cur, conn):
    '''
    This function takes the name of the database, cursor object for the database, and connection object for the database as arguments.
    The function then loops through each row of the database and inserts data into two tables. The first table takes the following
    values: isbn13, title, NYT rank, rating. The second table takes the following values: isbn13 and Publisher ID. The function also
    commits this inserted data for each row each time the loop is run.
    
    ARGUMENTS: 
        title: Name of the database, cursor object for the database, connection object for the database

    RETURNS: 
        No return
    '''

    for i in data:
        isbn13 = i[0]
        title = i[1]
        nyt_rank = i[2]
        pub_id = i[3]
        rating = i[4]
        cur.execute('INSERT OR IGNORE INTO Books(isbn13, title, nyt_rank, rating) VALUES (?,?,?,?)', (isbn13, title, nyt_rank, rating))
        cur.execute('INSERT OR IGNORE INTO Publishers(isbn13, pub_id) VALUES (?,?)', (isbn13, pub_id))
        conn.commit()

def database_join(cur, conn):
    rows = cur.execute('SELECT Publishers.pub_id, Books.rating FROM Publishers JOIN Books ON Publishers.isbn13 = Books.isbn13').fetchall()
    print(rows)
    for row in rows:
        pub_id = row[0]
        rating = row[1]
    conn.commit()
    

def analyze_first_data(cur, conn):
    cur.execute("ALTER TABLE Books ADD COLUMN new_rating REAL")
    rows = cur.execute("SELECT isbn13, nyt_rank, rating FROM Books").fetchall()
    for row in rows:
        nyt_rank = row[1]
        rating = row[2]
        new_rating = nyt_rank + rating
        isbn13 = row[0]
        cur.execute("UPDATE Books SET new_rating = ? WHERE isbn13 = ?", (new_rating, isbn13))
    conn.commit()

def analyze_data(cur, conn):
    rows = cur.execute("SELECT isbn13, nyt_rank, rating FROM Books").fetchall()
    for row in rows:
        nyt_rank = row[1]
        rating = row[2]
        new_rating = nyt_rank + rating
        isbn13 = row[0]
        cur.execute("UPDATE Books SET new_rating = ? WHERE isbn13 = ?", (new_rating, isbn13))
    conn.commit()

def create_first_visualization(cur, conn):
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

    rows = cur.execute('SELECT Publishers.pub_id, Books.rating FROM Publishers JOIN Books ON Publishers.isbn13 = Books.isbn13').fetchall()
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
        axis_count += 1
        x_tick_labels.append(axis_count)

    plt.scatter(x_axis_list, y_axis_list) 
    plt.xticks(x_tick_labels)
    plt.xlabel("Publisher ID") 
    plt.ylabel("New Ratings for Publisher's Books")  
    plt.title("New Rating Calculations for 5 Publishers") 
    plt.savefig("scatterplot_newrating_and_publisher.png")
    plt.show()
    conn.commit()


def main():
    '''
    This function is the main function of the progarm where most other functions are called. It takes no arguments.
    This function first creates the database, assigning it the name of "Storage" and assiging the cursor and connection
    objects to variables. Next it calls the new_rating_function() to add the new ratings to the database, after which
    it then stores this database to a variable called data. Following this, the current number of books within the Books
    table is stored into a variable. Following this, data is inserted into the Books and Publishers tables within the
    database, 25 books at a time. This is done by checking how many books are already added into the Books table, and
    inserting data for the next 25 books based on that value. If the code is run and the book count is above 76 and
    below 101 this means that the database has been populated with 100 items total, and so the visualizations are
    then made. This is done by calling each function for each visualization. Lastly, this function always closes the connection object.
    
    ARGUMENTS: 
        No arguments

    RETURNS: 
        No return
    '''
    
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