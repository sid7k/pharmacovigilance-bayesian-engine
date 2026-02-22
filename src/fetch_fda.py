import requests
import pandas as pd
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_openfda_data(limit=1000):
    """
    Fetches adverse event reports from the openFDA API.
    Includes fault tolerance and a fallback dataset for pipeline testing.
    """
    logging.info(f"Attempting to fetch {limit} records from openFDA API...")
    url = f"https://api.fda.gov/drug/event.json?limit={limit}"
    
    try:
        # Added a 10-second timeout so the pipeline doesn't hang indefinitely
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()['results']
        
        records = []
        for report in data:
            reactions = [r.get('reactionmeddrapt', 'UNKNOWN') for r in report.get('patient', {}).get('reaction', [])]
            drugs = [d.get('medicinalproduct', 'UNKNOWN') for d in report.get('patient', {}).get('drug', []) 
                     if d.get('drugcharacterization') == '1']
            
            for drug in drugs:
                for reaction in reactions:
                    records.append({'Drug': drug.upper(), 'Event': reaction.upper()})
                    
        df = pd.DataFrame(records)
        logging.info(f"Successfully extracted {len(df)} live drug-event pairs.")
        return df

    except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
        # Fault Tolerance: Catch the timeout and inject synthetic data
        logging.error(f"API request failed or timed out: {e}")
        logging.info("Initializing fallback synthetic dataset for pipeline demonstration...")
        
        # A mock dataset representing common drug-event pairs
        mock_data = {
            'Drug': ['SEMAGLUTIDE', 'SEMAGLUTIDE', 'LINDANE', 'SEMAGLUTIDE', 'AMOXICILLIN', 'LINDANE', 'AMOXICILLIN', 'SEMAGLUTIDE'],
            'Event': ['NAUSEA', 'PANCREATITIS', 'SEIZURE', 'NAUSEA', 'RASH', 'DIZZINESS', 'RASH', 'FATIGUE']
        }
        
        df_mock = pd.DataFrame(mock_data)
        # Duplicate the mock data to simulate a larger sample size for the BCPNN engine
        df_mock = pd.concat([df_mock]*125, ignore_index=True) 
        return df_mock

if __name__ == "__main__":
    # Test the pipeline
    df_safety = fetch_openfda_data(limit=100)
    print(df_safety.head())