
"""
Pipeline entrypoint.
 
Run from the project root:
    python main.py
"""
 
from app.ingestion.load_bronze import load_bronze
from app.transform.load_silver import load_silver
from app.gold.load_gold import load_gold
 
 
def main():
    load_bronze()
    load_silver()
    load_gold()
  
if __name__ == "__main__":
    main()
 
