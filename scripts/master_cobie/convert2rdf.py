import pandas as pd
from rdflib import Graph, Namespace, Literal
import re

from brontes.utils import create_uri

cobie = Namespace("http://checksem.u-bourgogne.fr/ontology/cobie24#")
rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
syyclops = Namespace('https://syyclops.com/')


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

# create Category Products
def create_category_products(g, master_cobie):
  # get all the rows in the colum Category-Product
  category_product = master_cobie['Category-Product']
  
  # add the Category-Product to the graph
  for cp in category_product:
    uri = syyclops['categoryProduct/' + create_uri(cp)]
    g.add((uri, rdf['type'], cobie['CategoryProduct']))
    g.add((uri, rdf['hasStringValue'], Literal(cp)))
    g.add((uri, rdf['isVerified'], Literal(True)))


# create Job Types
def create_job_types(g, master_cobie):
  # get all the rows in the colum Category-Job
  category_job = master_cobie['Category-Job']

  # add the Category-Job to the graph
  for cj in category_job:
    uri = syyclops['categoryJob/' + create_uri(cj)]
    g.add((uri, rdf['type'], cobie['CategoryJob']))
    g.add((uri, rdf['hasStringValue'], Literal(cj)))
    g.add((uri, rdf['isVerified'], Literal(True)))

# create Category Documents
def create_category_documents(g, master_cobie):
  # get all the rows in the colum Category-Document
  category_document = master_cobie['Category-Document']

  # add the Category-Document to the graph
  for cd in category_document:
    uri = syyclops['docType/' + create_uri(cd)]
    g.add((uri, rdf['type'], cobie['DocumentType']))
    g.add((uri, rdf['hasStringValue'], Literal(cd)))
    g.add((uri, rdf['isVerified'], Literal(True)))

# create category floors
def create_category_floors(g, master_cobie):
  # get all the rows in the colum Category-Floor
  category_floor = master_cobie['Category-Floor']
  
  # add the Category-Floor to the graph
  for cf in category_floor:
    uri = syyclops['categoryFloor/' + create_uri(cf)]
    g.add((uri, rdf['type'], cobie['CategoryFloor']))
    g.add((uri, rdf['hasStringValue'], Literal(cf)))
    g.add((uri, rdf['isVerified'], Literal(True)))
            
# create category facilities
def create_category_facilities(g, master_cobie):
  # get all the rows in the colum Category-Facility
  category_facility = master_cobie['Category-Facility']
  
  # add the Category-Facility to the graph
  for cf in category_facility:
    uri = syyclops['categoryFacility/' + create_uri(cf)]
    g.add((uri, rdf['type'], cobie['CategoryFacility']))
    g.add((uri, rdf['hasStringValue'], Literal(cf)))
    g.add((uri, rdf['isVerified'], Literal(True)))

# create category spaces
def create_category_spaces(g, master_cobie):
  # get all the rows in the colum Category-Space
  category_space = master_cobie['Category-Space']
  
  # add the Category-Space to the graph
  for cs in category_space:
    uri = syyclops['categorySpace/' + create_uri(cs)]
    g.add((uri, rdf['type'], cobie['CategorySpace']))
    g.add((uri, rdf['hasStringValue'], Literal(cs)))
    g.add((uri, rdf['isVerified'], Literal(True)))

# Category Products
tree = {}

# create rdf graph
g = Graph()
g.bind('syyclops', syyclops)
g.bind('cobie', cobie)
g.bind('rdf', rdf)

create_category_products(g, master_cobie)
create_job_types(g, master_cobie)
create_category_documents(g, master_cobie)
create_category_floors(g, master_cobie)
create_category_facilities(g, master_cobie)
create_category_spaces(g, master_cobie)


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
# g.serialize('./omniclass_tree_products.ttl', format='turtle')

# export to csv file
# df.to_csv('./omniclass_tree_products.csv', index=False)


# Category Spaces

tree = {}

# create rdf graph
# g = Graph()
# g.bind('syyclops', syyclops)
# g.bind('cobie', cobie)
# g.bind('rdf', rdf)

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



g.serialize('./master_cobie.ttl', format='turtle')
# export to turtle file
# g.serialize('./omniclass_tree_spaces.ttl', format='turtle')

# export to csv file
# df.to_csv('./omniclass_tree_spaces.csv', index=False)