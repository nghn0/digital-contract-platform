import grpc
from concurrent import futures
import time

# Create a simple proto for testing
# (Normally we would use the existing one, but let's keep it simple)

def test_print_io():
    try:
        for i in range(10):
            print(f"Test print {i}")
            time.sleep(0.1)
        return True
    except Exception as e:
        with open("io_error_test.log", "a") as f:
            f.write(f"Caught IO Error: {str(e)}\n")
        return False

if __name__ == "__main__":
    print("Starting IO test...")
    success = test_print_io()
    print(f"Test finished. Success: {success}")
