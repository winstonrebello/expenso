from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules
import pandas as pd

# Sample dataset (transaction data)
data = {'TID': [1, 2, 3, 4, 5],
        'Items': [['A', 'B', 'D'],
                  ['B', 'C', 'E'],
                  ['A', 'B', 'D'],
                  ['A', 'C', 'E'],
                  ['A', 'B', 'D', 'E']]}

df = pd.DataFrame(data)

# Convert the transaction data into a one-hot encoded format
oht = pd.get_dummies(df['Items'].apply(pd.Series).stack()).sum(level=0)
oht = oht.astype(bool)

# Use the Apriori algorithm to find frequent itemsets
frequent_itemsets = apriori(oht, min_support=0.6, use_colnames=True)

# Find association rules
association_rules = association_rules(frequent_itemsets, metric='lift', min_threshold=1.0)

print("Frequent Itemsets:")
print(frequent_itemsets)

print("\nAssociation Rules:")
print(association_rules)

