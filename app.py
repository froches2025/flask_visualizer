import base64
import io
import os
import time
import numpy
import matplotlib
import json
import pymysql

from data_structures import Stack, Queue
matplotlib.use('Agg') # interactive backend
import matplotlib.pyplot as plt
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# 1. Database credentials
DB_USER = 'froches'
DB_PASSWORD = 'froches_pass'
DB_HOST = 'localhost'
DB_NAME = 'visualizer_db'

# 2. Check and Create Database if it doesn't exist
try:
    # Connect to MySQL server (not the specific DB yet)
    connection = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
    cursor = connection.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.close()
    connection.close()
    print(f"Database '{DB_NAME}' verified/created.")
except Exception as e:
    print(f"Error creating database: {e}")

# 3. NOW initialize SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:3306/{DB_NAME}'
db = SQLAlchemy(app)

# use jwt on your save_analysis endpoint to authenticate the user and ensure that only authorized users can save analysis records. You can use Flask-JWT-Extended or any other JWT library for this purpose.
# if a request is sent without a valid JWT token, return a 401 Unauthorized response saying "I don't know you".
# the jwt token should be sent as a query parameter as a Bearer token like "?bearer_token=<your_token_here>".
# do a direct comparison of the token with a hardcoded value for simplicity, but in a real application, you would want to validate it properly.

class AnalysisRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    algo = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.Integer, nullable=False)
    end_time = db.Column(db.Integer, nullable=False)
    items = db.Column(db.Integer, nullable=False)
    steps = db.Column(db.Integer, nullable=False)
    time_complexity = db.Column(db.String(20), nullable=False)
    total_time_ms = db.Column(db.Integer, nullable=False)
    graph_base64 = db.Column(db.LargeBinary, nullable=False)
    
with app.app_context():
    db.create_all()

@app.after_request
def allow_frontend_requests(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# Creating the directory where image snapshots will be saved locally
SNAPSHOT_DIR = 'static/snapshots'
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

ANALYSIS_FILE = os.path.join(app.root_path, 'analysis_results.json')

def time_complexity_visualizer(algorithm, n_min, n_max, n_step):
    times = []
    # Generates the list of input sizes based on min, max,and step params
    input_sizes = list(range(n_min, n_max + n_step, n_step))
    
    # Create a figure and axis for plotting the performance curve
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlabel('Input Size')
    ax.set_ylabel('Running time (seconds)')
    ax.set_title('Algorithm Time Complexity Visualization (Live)')


    # Measure execution time for each input size step
    for n in input_sizes:
        start_time = time.time()
        algorithm(n) # Execute the target algorith function with size n
        end_time = time.time()
        times.append(end_time - start_time)

    # Plot the collected performance data points onto the graoh 
    ax.plot(input_sizes, times, 'o-', label='Running time')
    ax.grid(True)
    ax.legend()

    # Save a local image snapshot of the generated graph to disk
    filename = f"snapshot_{int(time.time())}.png"
    filepath = os.path.join(SNAPSHOT_DIR, filename)
    plt.savefig(filepath)
    
    # Convert the plot image into an in-memory binary buffer, then encode it to base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    base64_img = base64.b64encode(buf.read()).decode('utf-8')

    # Close the matplotlib figure to free up system memory
    plt.close(fig)
    
    return filepath, base64_img



def linear_search(n):
    for i in range(n):
        if i == n - 1:
            return True
    return False

def bubble_sort(n):
    arr = list(range(min(n, 1000), 0, -1))
    length = len(arr)
    for i in range(length):
        for j in range(0, length - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                
def binary_search(n):
    arr = list(range(n))
    target = n - 1
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return True
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return False

def nested_loops(n):
    limit = min(n, 500)
    total = 0
    for i in range(limit):
        for j in range(limit):
            total += i * j
    return total

def list_algo(n):
    users = [{'id': i} for i in range(n)]
    seen_ids = set()

    for user in users:
        seen_ids.add(user['id'])

    return len(seen_ids)

def benchmark_stack_push(n):
    stack = Stack()
    for i in range(n):
        stack.push(i)
    return stack.size()

def benchmark_queue_enqueue(n):
    queue = Queue()
    for i in range (n):
        queue.enqueue(i)
    return queue.size()


ALGOS = {
    'linear_search': linear_search,
    'bubble_sort': bubble_sort,
    'binary_search': binary_search,
    'list_algo': list_algo,
    'nested_loops': nested_loops,
    'stack_push': benchmark_stack_push,
    'queue_enqueue': benchmark_queue_enqueue
}

# Complexity mapping for extra fields shown in the image
COMPLEXITIES = {
    'linear_search': 'O(n)',
    'bubble_sort': 'O(n^2)',
    'binary_search': 'O(log n)',
    'nested_loops': 'O(n^2)',
    'list_algo': 'O(n^2)',
    'stack_push': 'O(n)',
    'queue_enqueue': 'O(n)'
}

PRETTY_NAMES = {
    'linear_search': 'Linear Search',
    'bubble_sort': 'Bubble Sort',
    'binary_search': 'Binary Search',
    'nested_loops': 'Nested Loops',
    'list_algo': 'List Algorithm',
    'stack_push': 'Stack Push',
    'queue_enqueue': 'Queue Enqueue'
}

@app.route('/analyze', methods=['GET'])
def analyze():
    algo_name = request.args.get('algo')
    try:
        step = int(request.args.get('step', 100))
        n_max = int(request.args.get('n_max', 10000))
    except ValueError:
        return jsonify({'error': 'Invalid step or n_max value. Please provide valid integers.'}), 400
    
    if algo_name not in ALGOS:
        return jsonify({'error': f'Algorithm "{algo_name}" not supported. Available algorithms: {list(ALGOS.keys())}'}), 400
    
    n_min = 0
    
    start_time = int(time.time())
    t_start_perf = time.perf_counter()
    
    _, base64_img = time_complexity_visualizer(ALGOS[algo_name], n_min, n_max, step)
    
    t_end_perf = time.perf_counter()
    end_time = int(time.time())
    total_time_ms = int((t_end_perf - t_start_perf) * 1000)

    return jsonify({
        'algo': PRETTY_NAMES.get(algo_name, algo_name),
        'end_time': end_time,
        'graph_base64': f"data:image/png;base64,{base64_img}",
        'items': n_max,
        'start_time': start_time,
        'steps': step,
        'time_complexity': COMPLEXITIES.get(algo_name, 'O(n)'),
        'total_time_ms': total_time_ms
    })
    
@app.route('/save_analysis', methods=['POST'])
def save_analysis():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            'error': 'Request body must be a JSON object.'
        }), 400

    try:
        algo = data.get('algo', 'Unknown')
        start_time = data.get('start_time', int(time.time()))
        end_time = data.get('end_time', int(time.time()))
        items = data.get('items', 0)
        steps = data.get('steps', 0)
        time_complexity = data.get('time_complexity', 'O(n)')
        total_time_ms = data.get('total_time_ms', 0)
        graph_base64 = data.get('graph_base64', '')

        # Save record using SQLAlchemy ORM (instead of writing to a JSON file)
        new_record = AnalysisRecord(
            algo=algo,
            start_time=start_time,
            end_time=end_time,
            items=items,
            steps=steps,
            time_complexity=time_complexity,
            total_time_ms=total_time_ms,
            graph_base64=graph_base64
        )
        db.session.add(new_record)
        db.session.commit()

    except Exception as error:
        db.session.rollback()
        return jsonify({
            'error': f'Could not save analysis to database: {error}'
        }), 500

    return jsonify({
        'message': 'Analysis saved successfully to database via SQLAlchemy',
        'id': new_record.id,
        'analysis': data
    }), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)