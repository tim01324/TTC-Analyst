import sys

def read_section():
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        with open(r'c:\Users\tim01\Desktop\TTC\answers.txt', 'r', encoding='utf-8') as f:
            print(f.read())

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    read_section()
