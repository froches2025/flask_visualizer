import base64
import io
import os
import time
import numpy
import matplotlib
matplotlib.use('Agg') # interactive backend
import matplotlib.pyplot as plt
from flask import Flask, jsonify, request

app = Flask(__name__)

# Creating the directory where image snapshots will be saved locally
SNAPSHOT_DIR = 'static/snapshots'
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

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

ALGOS = {
    'linear_search': linear_search,
    'bubble_sort': bubble_sort,
    'binary_search': binary_search,
    'nested_loops': nested_loops
}

# Complexity mapping for extra fields shown in the image
COMPLEXITIES = {
    'linear_search': 'O(n)',
    'bubble_sort': 'O(n^2)',
    'binary_search': 'O(log n)',
    'nested_loops': 'O(n^2)'
}

PRETTY_NAMES = {
    'linear_search': 'Linear Search',
    'bubble_sort': 'Bubble Sort',
    'binary_search': 'Binary Search',
    'nested_loops': 'Nested Loops'
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
    
    filepath, base64_img = time_complexity_visualizer(ALGOS[algo_name], n_min, n_max, step)
    
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
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)