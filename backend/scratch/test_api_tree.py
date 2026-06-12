import os
import sys
import json

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

client = app.test_client()
response = client.get('/api/master-categories/tree')
data = response.get_json()

print(f"Status Code: {response.status_code}")
if 'data' in data:
    roots = data['data']
    print(f"Number of root categories (Level 1): {len(roots)}")
    
    # Let's find any Level 3 or 4 categories in the tree structure
    found_l3 = []
    found_l4 = []
    
    def traverse(node, depth=1):
        if node.get('level') == 3:
            found_l3.append(node)
        elif node.get('level') == 4:
            found_l4.append(node)
            
        for child in node.get('children', []):
            traverse(child, depth + 1)
            
    for root in roots:
        traverse(root)
        
    print(f"Found L3 in tree: {len(found_l3)}")
    print(f"Found L4 in tree: {len(found_l4)}")
    
    if found_l3:
        print("\nSample L3 nodes in tree:")
        for node in found_l3[:5]:
            print(f"ID: {node['id']} | Name: {node['name']} | Parent ID: {node['parent_id']} | Children Count: {len(node['children'])}")
    if found_l4:
        print("\nSample L4 nodes in tree:")
        for node in found_l4[:5]:
            print(f"ID: {node['id']} | Name: {node['name']} | Parent ID: {node['parent_id']} | Children Count: {len(node['children'])}")
else:
    print("Error or unexpected structure:", data)
