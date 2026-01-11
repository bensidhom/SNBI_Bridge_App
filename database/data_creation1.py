import json
import pandas as pd
from collections import defaultdict
import xml.etree.ElementTree as ET
import math
import csv

# Field names in order for CSV
ordered_fields = [col for col, pos in sorted(field_positions.items(), key=lambda x: x[1][0])]

def parse_nbi_txt(txt_path):
    bridges = defaultdict(lambda: {'over': None, 'unders': []})
    with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        for line_num, row in enumerate(reader, 1):
            if len(row) != len(ordered_fields):
                print(f"Skipping invalid line {line_num}: length {len(row)}")
                continue
            bridge = {}
            for col, value in zip(ordered_fields, row):
                value = value.strip()
                bridge[col] = value if value else None
            struc = bridge['STRUCTURE_NUMBER_008'].strip()
            rec_type = bridge['RECORD_TYPE_005A']
            if rec_type == '1':
                bridges[struc]['over'] = bridge
            else:
                bridges[struc]['unders'].append(bridge)
    print(f"Parsed {len(bridges)} bridges from TXT.")
    return bridges

def parse_elements_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    elements_by_struc = defaultdict(list)
    for elem in root.findall('.//row'):
        struc = elem.get('STRUCNUM', '').strip()
        if not struc:
            continue
        el = {
            'BE01': elem.get('EN', ''),
            'BE02': elem.get('EPN', '0'),
            'BE03': elem.get('TOTALQTY', '0'),
            'BCS01': elem.get('CS1', '0'),
            'BCS02': elem.get('CS2', '0'),
            'BCS03': elem.get('CS3', '0'),
            'BCS04': elem.get('CS4', '0')
        }
        elements_by_struc[struc].append(el)
    print(f"Parsed elements for {len(elements_by_struc)} bridges from XML.")
    return elements_by_struc

def convert_dms_to_decimal(dms_str):
    if not dms_str or len(dms_str) < 6:
        return None
    try:
        dms = float(dms_str)
        degrees = int(dms // 1000000)
        minutes = int((dms % 1000000) // 10000)
        seconds = (dms % 10000) / 100
        decimal = degrees + minutes / 60 + seconds / 3600
        return round(decimal, 6)
    except:
        return None

def meters_to_feet(meters_str, round_down=False, cap99=False):
    if not meters_str:
        return None
    try:
        m = float(meters_str)
        if cap99 and m >= 30:
            return 99.9
        ft = m / 0.3048
        if round_down:
            ft = math.floor(ft * 10) / 10
        else:
            ft = round(ft, 1)
        return ft
    except:
        return None

def km_to_mile(km_str):
    if not km_str:
        return None
    try:
        km = float(km_str) / 1000
        mile = km / 1.60934
        return round(mile, 3)
    except:
        return None

def get_rating_factor(old, rating_key, meth_key, is_legacy=True):
    meth = old.get(meth_key, '')
    try:
        rating = float(old.get(rating_key, 0))
    except:
        return None
    if meth in ['6', '7', '8', 'D', 'E', 'F']:
        div = 32.4 if is_legacy else 1
    else:
        div = 32.67
    return round(rating / div, 2)

def determine_primary_under(unders):
    primary = None
    secondaries = []
    for u in unders:
        rec_type = u['RECORD_TYPE_005A']
        if rec_type == '2':
            primary = u
        elif rec_type == 'A':
            if primary is None:
                primary = u
            else:
                secondaries.append(u)
        else:
            secondaries.append(u)
    secondaries.sort(key=lambda x: x['RECORD_TYPE_005A'])
    return primary, secondaries

def map_bridge_to_snbi(old, unders):
    snbi = {}
    # Basic Location and ID
    snbi['BL01'] = int(old.get('STATE_CODE_001', '0').lstrip('0') or 0)
    snbi['BID01'] = old.get('STRUCTURE_NUMBER_008', '').strip()
    snbi['BL02'] = int(old.get('COUNTY_CODE_003', '0') or 0)
    snbi['BL03'] = int(old.get('PLACE_CODE_004', '0') or 0)
    snbi['BL04'] = old.get('HIGHWAY_DISTRICT_002', '').lstrip('0')
    snbi['BL11'] = old.get('LOCATION_009', '').strip()
    snbi['BW01'] = int(old.get('YEAR_BUILT_027', '0') or 0)
    snbi['BCL01'] = old.get('OWNER_022', '')
    snbi['BCL02'] = old.get('MAINTENANCE_021', '')
    snbi['BCL05'] = old.get('TOLL_020', '')
    snbi['BC01'] = old.get('DECK_COND_058', '')
    snbi['BC02'] = old.get('SUPERSTRUCTURE_COND_059', '')
    snbi['BC03'] = old.get('SUBSTRUCTURE_COND_060', '')
    snbi['BC04'] = old.get('CULVERT_COND_062', '')
    snbi['BRH01'] = old.get('RAILINGS_036A', '')
    snbi['BRH02'] = old.get('TRANSITIONS_036B', '')
    snbi['BG11'] = int(old.get('DEGREES_SKEW_034', '0') or 0)
    # Lat/Long
    lat_raw = old.get('LAT_016', '')
    if lat_raw:
        lat_dec = convert_dms_to_decimal(lat_raw)
        if lat_dec is not None:
            snbi['BL05'] = lat_dec
    lon_raw = old.get('LONG_017', '')
    if lon_raw:
        lon_dec = convert_dms_to_decimal(lon_raw)
        if lon_dec is not None:
            snbi['BL06'] = -lon_dec
    # Border
    snbi['BL07'] = old.get('BORDER_BRIDGE_STRUCTURE_099', '').strip()
    border_state = old.get('BORDER_BRIDGE_STATE_CODE_098A', '').strip().lstrip('0')
    if border_state.upper() == 'CAN':
        border_state = 'CA'
    elif border_state.upper() == 'MEX':
        border_state = 'MX'
    snbi['BL08'] = border_state
    snbi['BL09'] = old.get('BORDER_BRIDGE_PERCENT_098B', '')
    if border_state:
        snbi['BL10'] = snbi['BL01']
    # Geometry
    struct_len = old.get('STRUCTURE_LEN_MT_049', '')
    max_span = old.get('MAX_SPAN_LEN_MT_048', '')
    deck_width = old.get('DECK_WIDTH_MT_052', '')
    roadway_width = old.get('ROADWAY_WIDTH_MT_051', '')
    appr_width = old.get('APPR_WIDTH_MT_032', '')
    m_len = float(struct_len or 0)
    snbi['BG02'] = meters_to_feet(struct_len)
    snbi['BG03'] = meters_to_feet(max_span)
    if m_len > 9.1:
        snbi['BG01'] = snbi['BG02']
    main_spans = int(old.get('MAIN_UNIT_SPANS_045', '0') or 0)
    appr_spans = int(old.get('APPR_SPANS_046', '0') or 0)
    if main_spans == 1 and appr_spans == 0:
        snbi['BG04'] = snbi['BG03']
    snbi['BG05'] = meters_to_feet(deck_width) if float(deck_width or 0) > 0 else None
    snbi['BG06'] = meters_to_feet(roadway_width)
    snbi['BG07'] = meters_to_feet(old.get('LEFT_CURB_MT_050A', ''))
    snbi['BG08'] = meters_to_feet(old.get('RIGHT_CURB_MT_050B', ''))
    snbi['BG09'] = meters_to_feet(appr_width)
    snbi['BG10'] = old.get('MEDIAN_CODE_033', '')
    deck_ft = snbi['BG05'] or meters_to_feet(appr_width) or 0
    snbi['BG16'] = round(snbi['BG02'] * deck_ft, 1)
    # Span Sets
    snbi['SpanSets'] = []
    structure_type_b = old.get('STRUCTURE_TYPE_043B', '')
    if main_spans > 0 and structure_type_b != '00':
        main_config = 'M01' if structure_type_b != '19' else 'C01'
        main = {
            'BSP01': main_config,
            'BSP02': main_spans,
            'BSP04': old.get('STRUCTURE_KIND_043A', ''),
            'BSP06': structure_type_b,
            'BSP09': old.get('DECK_STRUCTURE_TYPE_107', ''),
            'BSP10': old.get('WEARING_SURFACE_108A', ''),
            'BSP11': old.get('MEMBRANE_108B', ''),
            'BSP12': old.get('DECK_PROTECTION_108C', ''),
        }
        snbi['SpanSets'].append(main)
    if appr_spans > 0:
        appr_config = 'A01' if structure_type_b != '19' else 'C02'
        appr = {
            'BSP01': appr_config,
            'BSP02': appr_spans,
            'BSP04': old.get('APPR_KIND_044A', ''),
            'BSP06': old.get('APPR_TYPE_044B', ''),
            'BSP09': old.get('DECK_STRUCTURE_TYPE_107', ''),
            'BSP10': old.get('WEARING_SURFACE_108A', ''),
            'BSP11': old.get('MEMBRANE_108B', ''),
            'BSP12': old.get('DECK_PROTECTION_108C', ''),
        }
        snbi['SpanSets'].append(appr)
    # Load Rating
    snbi['BLR01'] = old.get('DESIGN_LOAD_031', '')
    snbi['BLR04'] = old.get('OPR_RATING_METH_063', '')
    snbi['BLR05'] = get_rating_factor(old, 'INVENTORY_RATING_066', 'INV_RATING_METH_065')
    snbi['BLR06'] = get_rating_factor(old, 'OPERATING_RATING_064', 'OPR_RATING_METH_063')
    # Posting Status
    snbi['BPS01'] = old.get('OPEN_CLOSED_POSTED_041', '')
    # Inspection Requirements
    snbi['BIR01'] = old.get('FRACTURE_092A', '')[0] if old.get('FRACTURE_092A') else None
    snbi['BIR03'] = old.get('UNDERWATER_092B', '')[0] if old.get('UNDERWATER_092B') else None
    # Condition
    snbi['BC09'] = old.get('CHANNEL_COND_061', '')
    snbi['BC11'] = old.get('SCOUR_CRITICAL_113', '')
    # Approach
    snbi['BAP01'] = old.get('APPR_ROAD_ALIGN_072', '')
    snbi['BAP02'] = old.get('WATERWAY_EVAL_071', '')
    snbi['BAP03'] = old.get('SCOUR_CRITICAL_113', '')
    snbi['BAP04'] = old.get('SCOUR_CRITICAL_113', '')
    # Work
    snbi['Works'] = []
    year_recon = old.get('YEAR_RECONSTRUCTED_106', '')
    if year_recon and int(year_recon) > 0:
        snbi['Works'].append({'BW02': int(year_recon), 'BW03': 'RECONSTRUCTED'})
    # Features
    snbi['Features'] = []
    service_on = old.get('SERVICE_ON_042A', '')
    if service_on in ['1', '4', '5', '6', '7', '8']:
        feat = {
            'BF01': 'H01',
            'BF02': 'C',
            'BF03': old.get('FACILITY_CARRIED_007', '').strip(),
            'BH01': old.get('FUNCTIONAL_CLASS_026', ''),
            'BH02': old.get('FUNCTIONAL_CLASS_026', ''),  # Placeholder, adjust if mapping known
            'BH03': old.get('HIGHWAY_SYSTEM_104', ''),
            'BH04': old.get('NATIONAL_NETWORK_110', ''),
            'BH05': old.get('STRAHNET_100', ''),
            'BH06': (old.get('LRS_INVENTORY_ROUTE_013A', '') + old.get('SUBROUTE_013B', '')).strip().lstrip('0') or None,
            'BH07': km_to_mile(old.get('KILOPOINT_011', '')),
            'BH08': int(old.get('TRAFFIC_LANES_ON_028A', '0') or 0),
            'BH09': int(old.get('ADT_029', '0') or 0),
            'BH10': int(old.get('ADT_029', '0') or 0) * int(old.get('PERCENT_ADT_TRUCK_109', '0') or 0) / 100,
            'BH11': old.get('YEAR_ADT_030', ''),
            'BH12': meters_to_feet(old.get('MIN_VERT_CLR_010', ''), round_down=True, cap99=True),
            'BH13': meters_to_feet(old.get('VERT_CLR_OVER_MT_053', ''), round_down=True, cap99=True),
            'BH16': meters_to_feet(old.get('HORR_CLR_MT_047', ''), round_down=True, cap99=True),
            'BH17': 999 if old.get('DETOUR_KILOS_019', '') == '199' else round(float(old.get('DETOUR_KILOS_019', '0') or 0) / 1.60934)
        }
        route_num = old.get('ROUTE_NUMBER_005D', '').lstrip('0') or '0'
        route_num += old.get('DIRECTION_005E', '') or ''
        route = {
            'BRT01': 'R01',
            'BRT02': route_num,
            'BRT03': old.get('DIRECTION_OF_TRAFFIC_102', ''),
            'BRT04': old.get('ROUTE_PREFIX_005B', ''),
            'BRT05': old.get('SERVICE_LEVEL_005C', '')
        }
        feat['Routes'] = [route]
        snbi['Features'].append(feat)
    # Under features
    service_und = old.get('SERVICE_UND_042B', '')
    if service_und != '0':
        primary_under, secondary_unders = determine_primary_under(unders)
        highway_under = service_und in ['1', '3', '5', '6', '7', '8', '9']
        railroad_under = service_und in ['2', '3', '7', '9']
        water_under = service_und in ['3', '4', '8', '9']
        if highway_under:
            under_records = [primary_under or old] + secondary_unders
            h_num = 2
            for u in under_records:
                feat = {
                    'BF01': f'H{h_num:02d}',
                    'BF02': 'B',
                    'BF03': u.get('FEATURES_DESC_006A', old.get('FEATURES_DESC_006A', '')).strip() if u else '',
                    'BH01': u.get('FUNCTIONAL_CLASS_026', ''),
                    'BH02': u.get('FUNCTIONAL_CLASS_026', ''),  # Placeholder
                    'BH03': u.get('HIGHWAY_SYSTEM_104', ''),
                    'BH04': u.get('NATIONAL_NETWORK_110', ''),
                    'BH05': u.get('STRAHNET_100', ''),
                    'BH06': (u.get('LRS_INVENTORY_ROUTE_013A', '') + u.get('SUBROUTE_013B', '')).strip().lstrip('0') or None,
                    'BH07': km_to_mile(u.get('KILOPOINT_011', '')),
                    'BH08': int(u.get('TRAFFIC_LANES_UND_028B', '0') or 0),
                    'BH09': int(u.get('ADT_029', '0') or 0),
                    'BH10': int(u.get('ADT_029', '0') or 0) * int(u.get('PERCENT_ADT_TRUCK_109', '0') or 0) / 100,
                    'BH11': u.get('YEAR_ADT_030', ''),
                    'BH12': meters_to_feet(u.get('MIN_VERT_CLR_010', ''), round_down=True, cap99=True),
                    'BH13': meters_to_feet(old.get('VERT_CLR_UND_054B', ''), round_down=True, cap99=True) if old.get('VERT_CLR_UND_REF_054A', '') == 'H' else None,
                    'BH14': meters_to_feet(old.get('LEFT_LAT_UND_MT_056', ''), round_down=True, cap99=True) if old.get('LAT_UND_REF_055A', '') == 'H' else None,
                    'BH15': meters_to_feet(old.get('LAT_UND_MT_055B', ''), round_down=True, cap99=True) if old.get('LAT_UND_REF_055A', '') == 'H' else None,
                    'BH16': meters_to_feet(u.get('HORR_CLR_MT_047', ''), round_down=True, cap99=True),
                    'BH17': 999 if u.get('DETOUR_KILOS_019', '') == '199' else round(float(u.get('DETOUR_KILOS_019', '0') or 0) / 1.60934)
                }
                route_num = u.get('ROUTE_NUMBER_005D', '').lstrip('0') or '0'
                route_num += u.get('DIRECTION_005E', '') or ''
                route = {
                    'BRT01': 'R01',
                    'BRT02': route_num,
                    'BRT03': u.get('DIRECTION_OF_TRAFFIC_102', ''),
                    'BRT04': u.get('ROUTE_PREFIX_005B', ''),
                    'BRT05': u.get('SERVICE_LEVEL_005C', '')
                }
                feat['Routes'] = [route]
                snbi['Features'].append(feat)
                h_num += 1
        if railroad_under:
            r_feat = 'R01' if service_on != '4' else 'R02'
            feat = {
                'BF01': r_feat,
                'BF02': 'B',
                'BF03': old.get('FEATURES_DESC_006A', '').strip(),
                'BRR02': meters_to_feet(old.get('VERT_CLR_UND_054B', ''), round_down=True, cap99=True) if old.get('VERT_CLR_UND_REF_054A', '') == 'R' else None,
                'BRR03': meters_to_feet(old.get('LAT_UND_MT_055B', ''), round_down=True, cap99=True) if old.get('LAT_UND_REF_055A', '') == 'R' else None,
            }
            snbi['Features'].append(feat)
        if water_under:
            feat = {
                'BF01': 'W01',
                'BF02': 'B',
                'BF03': old.get('FEATURES_DESC_006A', '').strip(),
                'BN01': 'Y' if old.get('NAVIGATION_038', '') == '1' else 'N',
            }
            if feat['BN01'] == 'Y':
                nav_vert = old.get('NAV_VERT_CLR_MT_039', '')
                structure_type_b = old.get('STRUCTURE_TYPE_043B', '')
                if structure_type_b == '15':
                    feat['BN03'] = meters_to_feet(nav_vert, round_down=True)
                    nav_vert = old.get('MIN_NAV_CLR_MT_116', '') or nav_vert
                feat['BN02'] = meters_to_feet(nav_vert, round_down=True)
                feat['BN04'] = meters_to_feet(old.get('NAV_HORR_CLR_MT_040', ''), round_down=True)
                feat['BN06'] = old.get('PIER_PROTECTION_111', '')
            snbi['Features'].append(feat)
    return snbi

# Main execution
txt_path = r'D:\SNBI_Bridge_App\SNBI_Bridge_App\database\NJ25.txt'  # Replace
xml_path = r'D:\SNBI_Bridge_App\SNBI_Bridge_App\database\2025NJ_ElementData.xml'  # Replace
bridges_data = parse_nbi_txt(txt_path)
elements_by_struc = parse_elements_xml(xml_path)
json_bridges = []
for struc, bridge_data in bridges_data.items():
    old = bridge_data['over']
    if not old:
        continue
    unders = bridge_data['unders']
    snbi_bridge = map_bridge_to_snbi(old, unders)
    elems = elements_by_struc.get(struc, [])
    if elems:
        snbi_bridge['Elements'] = elems
    json_bridges.append(snbi_bridge)
with open('nj_bridges_converted.json', 'w', encoding='utf-8') as f:
    json.dump(json_bridges, f, indent=2, ensure_ascii=False)
print(f"Converted {len(json_bridges)} bridges to nj_bridges_converted.json")