# import psycopg2

# from configure import config


# def connect(): 
#     connection = None
#     try:
#         params = config()
#         print('Connection to the postresSQL database...')

#         #connect a database
#         connection = psycopg2.connect(**params)

#         # create a cursor
#         cursr = connection.cursor()



#         print('PostgreSQL database version: ')
#         cursr.execute('SELECT version()')
#         db_version = cursr.fetchone()
#         print(db_version)
#         cursr.close()

#         connection.commit()
#     except(Exception, psycopg2.DatabaseError) as error:
#         print(error)

#     finally:
#         if connection is not None:
#             connection.close()
#             print('Database connection terminated.')

# if __name__ == "__main__":
#     connect()


from flask import Flask, jsonify, request, abort
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from configure import config


app = Flask(__name__)

# extablish a connection to the PostgreSQL DB
def connect_db():
    params = config()
    conn = psycopg2.connect(**params)
    return conn


# Helper function to create the task table 
def create_table():
    conn = None
    try: 
        conn = connect_db()
        cursor = conn.cursor()
        create_table_query = ''' 
                CREATE TABLE IF NOT EXISTS dummy_table (
                    Id SERIAL PRIMARY KEY,
                    Name TEXT NOT NULL,

                    Title__c TEXT NOT NULL,
                    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
        '''
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
    except (Exception , psycopg2.DatabaseError ) as error:
        print(f"Error creating table: {error}")

    finally:
        if conn is not None:
            conn.close()
        

#Create the table on app startup
create_table()

# Initial route
@app.route('/')
def index():
    message = {
        "message": "Welcome to the TodoList API!",
        "routes": {
            "get_all_tasks": "/TodoLists [GET]",
            "get_task_by_id": "/TodoLists/<id> [GET]",
            "create_task": "/TodoLists [POST]",
            "update_task": "/TodoLists/<id> [PUT]",
            "delete_task": "/TodoLists/<id> [DELETE]"
        }
    }
    return jsonify(message)


# Get all tasks
@app.route('/TodoLists', methods=['GET'])
def get_todolists():
    conn = connect_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT "Id", "Name", "Title__c", "CreatedAt" FROM dummy_table ')
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(tasks)

# Get a task by ID
@app.route('/TodoLists/<int:task_id>', methods=['GET'])
def get_todolist_id(task_id):
    conn = connect_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT "Id", "Name", "Title__c", "CreatedAt" FROM dummy_table WHERE "Id" = %s', (task_id,))
    task = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if task:
        return jsonify(task)
    else:
        abort(404, description="Task not found")

# Create a new task
@app.route('/TodoLists', methods=['POST'])
def add_new_task():
    if not request.json or not 'Name' in request.json or not 'Title__c' in request.json:
        abort(400, description="Invalid input. Task and status are required.")
    
    Name = request.json['Name']
    Title__c = request.json['Title__c']

    conn = connect_db()
    cursor = conn.cursor()
    insert_query = '''
        INSERT INTO dummy_table ("Name", "Title__c", "CreatedAt")
        VALUES (%s, %s, %s) RETURNING "Id";
    '''
    now = datetime.now()
    cursor.execute(insert_query, (Name, Title__c, now))
    task_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Task created successfully", "Id": task_id}), 201

# Update an existing task
@app.route('/TodoLists/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    if not request.json:
        abort(400, description="Invalid input")

    task = request.json.get('Name')
    status = request.json.get('Title__c')

    conn = connect_db()
    cursor = conn.cursor()
    update_query = '''
        UPDATE dummy_table
        SET "Name" = COALESCE(%s, "Name"),
            "Title__c" = COALESCE(%s, "Title__c"),
            "CreatedAt" = %s
        WHERE "Id" = %s;
    '''
    now = datetime.now()
    cursor.execute(update_query, (task, status, now, task_id))
    
    if cursor.rowcount == 0:
        conn.close()
        abort(404, description="Task not found")

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Task updated successfully", "Id": task_id}), 200

# Delete a task
@app.route('/TodoLists/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM dummy_table WHERE "Id" = %s', (task_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        abort(404, description="Task not found")

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Task deleted successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)