
"""
Pipeline entrypoint.
 
Run from the project root:
    python main.py
"""
 
from app.ingestion.load_bronze import load_bronze
 
 
def main():
    load_bronze()
    # Later: load_silver(), load_gold()
 
 
if __name__ == "__main__":
    main()
 
