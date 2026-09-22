def test_stack():
    stack = Stack()
    stack.push(18)
    stack.push(20)
    stack.push(30)
    assert stack.pop() == 30
    assert stack.peek() == 20
    assert stack.is_empty() is False
    assert stack.pop() == 20
    assert stack.pop() == 18
    assert stack.is_empty() is True
    print("Stack tests passed.")
    
def test_queue():
    queue = Queue()
    queue.enqueue(18)
    queue.enqueue(20)
    queue.enqueue(30)
    assert queue.dequeue() == 18
    assert queue.peek() == 20
    assert queue.is_empty() is False
    assert queue.dequeue() == 20
    assert queue.dequeue() == 30
    assert queue.is_empty() is True
    print("Queue tests passed.")
    
if __name__ == "__main__":
    test_stack()
    test_queue()