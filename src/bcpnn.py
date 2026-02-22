import numpy as np
import pandas as pd
import scipy.stats as stats

def calculate_bcpnn_ic(df, drug_col, event_col):
    """
    Calculates the Information Component (IC) and 95% Confidence Intervals
    using the BCPNN method for a dataset of drug-event pairs.
    """
    # Total reports in the database
    N = len(df)
    
    # Calculate marginal counts
    drug_counts = df[drug_col].value_counts().to_dict()
    event_counts = df[event_col].value_counts().to_dict()
    
    # Calculate observed combinations
    pair_counts = df.groupby([drug_col, event_col]).size().reset_index(name='observed_count')
    
    # Map marginal counts back to the pairs
    pair_counts['drug_total'] = pair_counts[drug_col].map(drug_counts)
    pair_counts['event_total'] = pair_counts[event_col].map(event_counts)
    
    # Calculate Expected Count (E_ij = (drug_total * event_total) / N)
    pair_counts['expected_count'] = (pair_counts['drug_total'] * pair_counts['event_total']) / N
    
    # Smoothing parameters to prevent zero-division (Jeffrey's Prior)
    alpha = 0.5
    beta = 0.5
    
    # Calculate IC
    # IC = log2((Observed + alpha) / (Expected + beta))
    pair_counts['IC'] = np.log2((pair_counts['observed_count'] + alpha) / 
                                (pair_counts['expected_count'] + beta))
    
    # Calculate Variance of IC (Delta method approximation)
    # Var(IC) ≈ (1 / ln(2)^2) * (1/(O + alpha) + 1/(drug_total + alpha) + 1/(event_total + alpha))
    variance_ic = (1 / (np.log(2)**2)) * (
        (1 / (pair_counts['observed_count'] + alpha)) + 
        (1 / (pair_counts['drug_total'] + alpha)) + 
        (1 / (pair_counts['event_total'] + alpha))
    )
    
    # 95% Confidence Interval (Z-score for 95% is 1.96)
    z_score = stats.norm.ppf(0.975)
    margin_of_error = z_score * np.sqrt(variance_ic)
    
    pair_counts['IC_025'] = pair_counts['IC'] - margin_of_error
    pair_counts['IC_975'] = pair_counts['IC'] + margin_of_error
    
    # Flag positive signals (Lower bound > 0)
    pair_counts['Signal_Detected'] = pair_counts['IC_025'] > 0
    
    # Sort by strongest signal (highest lower bound)
    return pair_counts.sort_values(by='IC_025', ascending=False).reset_index(drop=True)

# Example Usage (You can remove or comment this out for production):
# if __name__ == "__main__":
#     df_safety = pd.DataFrame({'Drug': ['DRUG_A', 'DRUG_A', 'DRUG_B', 'DRUG_A', 'DRUG_C'], 
#                               'Event': ['NAUSEA', 'HEADACHE', 'NAUSEA', 'NAUSEA', 'DIZZINESS']})
#     signals = calculate_bcpnn_ic(df_safety, 'Drug', 'Event')
#     print(signals)