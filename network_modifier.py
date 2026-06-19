import xml.etree.ElementTree as ET
import os

def modify_network(input_file, output_file):
    print(f"Parsing {input_file}...")
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    edge_lanes = {}
    for edge in root.findall('edge'):
        if 'function' not in edge.attrib or edge.attrib['function'] != 'internal':
            edge_id = edge.attrib['id']
            num_lanes = len(edge.findall('lane'))
            edge_lanes[edge_id] = num_lanes
            
    print(f"Found {len(edge_lanes)} edges.")
    
    edge_pairs = {}
    connections_to_remove = []
    
    for conn in root.findall('connection'):
        # Ignore internal connections (starts with :)
        if conn.attrib.get('from', '').startswith(':'):
            continue
            
        from_edge = conn.attrib['from']
        to_edge = conn.attrib['to']
        
        pair = (from_edge, to_edge)
        if pair not in edge_pairs:
            edge_pairs[pair] = conn.attrib.copy()
            
        connections_to_remove.append(conn)
        
    print(f"Found {len(connections_to_remove)} connections to replace.")
    
    for conn in connections_to_remove:
        root.remove(conn)
        
    new_conns_count = 0
    for (from_edge, to_edge), template in edge_pairs.items():
        if from_edge not in edge_lanes or to_edge not in edge_lanes:
            continue
            
        from_lanes = edge_lanes[from_edge]
        to_lanes = edge_lanes[to_edge]
        
        for fl in range(from_lanes):
            tl_lane = min(fl, to_lanes - 1)
            
            new_conn = ET.Element('connection')
            
            for k, v in template.items():
                # Do not copy 'via' as it refers to a specific internal lane geometry
                if k != 'via':
                    new_conn.attrib[k] = v
                
            new_conn.attrib['fromLane'] = str(fl)
            new_conn.attrib['toLane'] = str(tl_lane)
            
            root.append(new_conn)
            new_conns_count += 1
            
    print(f"Generated {new_conns_count} new permissive connections.")
    
    print(f"Writing output to {output_file}...")
    tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    print("Done!")

if __name__ == "__main__":
    modify_network("lust.net.xml", "lust_modified.net.xml")
