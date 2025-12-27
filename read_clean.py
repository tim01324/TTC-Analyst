import sys

def read_clean():
    sys.stdout.reconfigure(encoding='utf-8')
    path = r'c:\Users\tim01\Desktop\TTC\advanced_metrics_results.txt'
    with open(path, 'r', encoding='utf-8') as f:
        print(f.read())

if __name__ == "__main__":
    read_clean()
