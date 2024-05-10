import pandas as pd
from rdflib import Graph, Namespace
import re

cobie = Namespace("http://checksem.u-bourgogne.fr/ontology/cobie24#")
rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
syyclops = Namespace('https://syyclops.com/')

def create_uri(name: str) -> str:
  # function to transform the name string into a URI
  return re.sub(r'[^a-zA-Z0-9]', '', str(name).lower())

master_cobie = pd.read_csv("./master_cobie.csv")

# drop rows where 'Category-Product' is empty or NaN
master_cobie = master_cobie[master_cobie['Category-Product'].notna()]

# get all the rows in the column 'Category-Product'
category_products = master_cobie['Category-Product']

# drop rows where 'Category-Space' is empty or NaN
master_cobie_spaces = master_cobie[master_cobie['Category-Space'].notna()]

# get all the rows in the column 'Category-Space'
category_spaces = master_cobie_spaces['Category-Space']

# split omniclass into number and text
def split_on_first_letter(s):
  match = re.search(r'^([^A-Za-z]*)(.*)$', s)
  if match:
    return match.group(1).strip(), match.group(2).strip()
  else:
    return None, None
    

# Category Products

tree = {}

# create rdf graph
g = Graph()
g.bind('syyclops', syyclops)
g.bind('cobie', cobie)
g.bind('rdf', rdf)

# dataframe to store the omniclass codes in a tree structure
df = pd.DataFrame(columns=['col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7'])

for s in category_products:
  number, text = split_on_first_letter(s)
  category_uri = syyclops['categoryProduct/'+create_uri(number+text)]
  number = number.replace(' 00', '')  # remove all 0's


  # If len of number is 5, then put in the first column
  if len(number) == 5:
    df.loc[number] = [s, None, None, None, None, None, None]
  # If len of number is 8, then put in the second column
  elif len(number) == 8:
    df.loc[number] = [None, s, None, None, None, None, None]
  # If len of number is 11, then put in the third column
  elif len(number) == 11:
    df.loc[number] = [None, None, s, None, None, None, None]
  # If len of number is 13 or 14, then put in the fourth column
  elif len(number) == 14 or len(number) == 13:
    df.loc[number] = [None, None, None, s, None, None, None]
  # If len of number is 16 or 17 or 18, then put in the fifth column
  elif len(number) == 17 or len(number) == 16 or len(number) == 18:
    df.loc[number] = [None, None, None, None, s, None, None]
  # If len of number is 19 or 20, then put in the sixth column
  elif len(number) == 20 or len(number) == 19:
    df.loc[number] = [None, None, None, None, None, s, None]
  # If len of number is 22 or 23, then put in the seventh column
  elif len(number) == 22 or len(number) == 23:
    df.loc[number] = [None, None, None, None, None, None, s]
  else:
    print(number)
    print(len(number))

  # find the parent omniclass code
  parent = None
  if number[:-3] in tree.keys():
    parent = tree[number[:-3]]['uri']
  
  if parent is None and number[:-2] in tree.keys():
    parent = tree[number[:-2]]['uri'] 

  if parent is None and number[:-6] in tree.keys():
    parent = tree[number[:-6]]['uri'] 
  
  if parent is None and number[:-5] in tree.keys():
    parent = tree[number[:-5]]['uri'] 
  
  if parent is None and number[:-4] in tree.keys():
    parent = tree[number[:-4]]['uri']

  tree[number] = {"uri": category_uri, "parent": parent}

  if parent != None:
    g.add((category_uri, cobie['hasParent'], parent))


# export to turtle file
g.serialize('./omniclass_tree_products.ttl', format='turtle')

# export to csv file
df.to_csv('./omniclass_tree_products.csv', index=False)


# Category Spaces

tree = {}

# create rdf graph
g = Graph()
g.bind('syyclops', syyclops)
g.bind('cobie', cobie)
g.bind('rdf', rdf)

# dataframe to store the omniclass codes in a tree structure
df = pd.DataFrame(columns=['col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7'])

for s in category_spaces:
  number, text = split_on_first_letter(s)
  category_uri = syyclops['categorySpace/'+create_uri(number+text)]
  number = number.replace(' 00', '')  # remove all 0's


  # If len of number is 5, then put in the first column
  if len(number) == 5:
    df.loc[number] = [s, None, None, None, None, None, None]
  # If len of number is 8, then put in the second column
  elif len(number) == 8:
    df.loc[number] = [None, s, None, None, None, None, None]
  # If len of number is 11, then put in the third column
  elif len(number) == 11:
    df.loc[number] = [None, None, s, None, None, None, None]
  # If len of number is 13 or 14, then put in the fourth column
  elif len(number) == 14 or len(number) == 13:
    df.loc[number] = [None, None, None, s, None, None, None]
  # If len of number is 16 or 17 or 18, then put in the fifth column
  elif len(number) == 17 or len(number) == 16 or len(number) == 18:
    df.loc[number] = [None, None, None, None, s, None, None]
  # If len of number is 19 or 20, then put in the sixth column
  elif len(number) == 20 or len(number) == 19:
    df.loc[number] = [None, None, None, None, None, s, None]
  # If len of number is 22 or 23, then put in the seventh column
  elif len(number) == 22 or len(number) == 23:
    df.loc[number] = [None, None, None, None, None, None, s]
  else:
    print(number)
    print(len(number))

  # find the parent omniclass code
  parent = None
  if number[:-3] in tree.keys():
    parent = tree[number[:-3]]['uri']
  
  if parent is None and number[:-2] in tree.keys():
    parent = tree[number[:-2]]['uri'] 

  if parent is None and number[:-6] in tree.keys():
    parent = tree[number[:-6]]['uri'] 
  
  if parent is None and number[:-5] in tree.keys():
    parent = tree[number[:-5]]['uri'] 
  
  if parent is None and number[:-4] in tree.keys():
    parent = tree[number[:-4]]['uri']

  tree[number] = {"uri": category_uri, "parent": parent}

  if parent != None:
    g.add((category_uri, cobie['hasParent'], parent))


# export to turtle file
g.serialize('./omniclass_tree_spaces.ttl', format='turtle')

# export to csv file
df.to_csv('./omniclass_tree_spaces.csv', index=False)