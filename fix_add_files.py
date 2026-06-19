import xml.etree.ElementTree as ET
import sys

def fix_positions(net_file, add_files):
    # Parse network to get lane lengths
    print(f"Parsing {net_file} for lane lengths...")
    net_tree = ET.parse(net_file)
    lane_lengths = {}
    for edge in net_tree.getroot().findall('edge'):
        for lane in edge.findall('lane'):
            lane_id = lane.attrib['id']
            length = float(lane.attrib['length'])
            lane_lengths[lane_id] = length

    for add_file in add_files:
        try:
            print(f"Fixing positions in {add_file}...")
            tree = ET.parse(add_file)
            root = tree.getroot()
            modified = False
            
            # Check bus stops
            for elem in root.findall('.//busStop'):
                lane_id = elem.attrib.get('lane')
                if lane_id in lane_lengths:
                    max_len = lane_lengths[lane_id]
                    start_pos = float(elem.attrib.get('startPos', 0))
                    end_pos = float(elem.attrib.get('endPos', 0))
                    
                    if end_pos > max_len:
                        diff = end_pos - start_pos
                        new_end = max_len - 0.1
                        new_start = max(0.0, new_end - diff)
                        elem.attrib['startPos'] = f"{new_start:.2f}"
                        elem.attrib['endPos'] = f"{new_end:.2f}"
                        modified = True
                        print(f"  Fixed {elem.tag} {elem.attrib.get('id')} on {lane_id}: endPos to {new_end:.2f}")

            # Check detectors (e1Detector)
            for elem in root.findall('.//e1Detector'):
                lane_id = elem.attrib.get('lane')
                if lane_id in lane_lengths:
                    max_len = lane_lengths[lane_id]
                    pos = float(elem.attrib.get('pos', 0))
                    if pos > max_len:
                        new_pos = max_len - 0.1
                        elem.attrib['pos'] = f"{new_pos:.2f}"
                        modified = True
                        print(f"  Fixed {elem.tag} {elem.attrib.get('id')} on {lane_id}: pos to {new_pos:.2f}")

            if modified:
                tree.write(add_file, encoding='UTF-8', xml_declaration=True)
                print(f"Saved {add_file}")
            else:
                print(f"No changes needed for {add_file}")
        except Exception as e:
            print(f"Error processing {add_file}: {e}")

if __name__ == "__main__":
    fix_positions("lust_edge_level.net.xml", ["busstops.add.xml", "e1detectors.add.xml"])
