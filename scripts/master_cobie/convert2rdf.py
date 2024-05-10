import pandas as pd
from rdflib import Graph, Namespace, Literal
import re

from brontes.utils import create_uri

cobie = Namespace("http://checksem.u-bourgogne.fr/ontology/cobie24#")
rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
syyclops = Namespace('https://syyclops.com/')

master_cobie = pd.read_csv("./master_cobie.csv")
master_cobie = master_cobie[master_cobie['Category-Product'].notna()] # drop rows where 'Category-Product' is empty or NaN

# get all the rows in the column 'Category-Product'
category_products = master_cobie['Category-Product']

# drop rows where 'Category-Space' is empty or NaN
master_cobie_spaces = master_cobie[master_cobie['Category-Space'].notna()]
category_spaces = master_cobie_spaces['Category-Space'] # get all the rows in the column 'Category-Space'

# split omniclass into number and text
def split_on_first_letter(s):
  match = re.search(r'^([^A-Za-z]*)(.*)$', s)
  if match:
    return match.group(1).strip(), match.group(2).strip()
  else:
    return None, None

# helper function to create category elements
def create_category_elements(graph, master_df, category_column, type_namespace, prefix):
  for element in master_df[category_column].unique():
    # If element is empty, skip
    if pd.isna(element):
      continue
    uri = syyclops[f'{prefix}/' + create_uri(element)]
    graph.add((uri, rdf.type, type_namespace))
    graph.add((uri, rdf.hasStringValue, Literal(element)))
    graph.add((uri, rdf.isVerified, Literal(True)))

# create tree structure for category products
tree = {}

# create rdf graph
g = Graph()
g.bind('syyclops', syyclops)
g.bind('cobie', cobie)
g.bind('rdf', rdf)

# Add elements to graph
create_category_elements(g, master_cobie, 'Category-Product', cobie.CategoryProduct, 'categoryProduct')
create_category_elements(g, master_cobie, 'Category-Job', cobie.CategoryJob, 'categoryJob')
create_category_elements(g, master_cobie, 'Category-Document', cobie.DocumentType, 'docType')
create_category_elements(g, master_cobie, 'Category-Floor', cobie.CategoryFloor, 'categoryFloor')
create_category_elements(g, master_cobie, 'Category-Facility', cobie.CategoryFacility, 'categoryFacility')
create_category_elements(g, master_cobie, 'Category-Space', cobie.CategorySpace, 'categorySpace')

# dataframe to store the omniclass codes in a tree structure
df = pd.DataFrame(columns=['col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7'])

# Category Products tree
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


# Category Spaces

tree = {}

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


# Export the graph
g.serialize('./master_cobie.ttl', format='turtle')