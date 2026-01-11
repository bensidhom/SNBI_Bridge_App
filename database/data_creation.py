import json
import pandas as pd
from collections import defaultdict
import xml.etree.ElementTree as ET
import math
import csv

# Field names in order from the example
field_names = [
    'STATE_CODE_001', 'STRUCTURE_NUMBER_008', 'RECORD_TYPE_005A', 'ROUTE_PREFIX_005B', 'SERVICE_LEVEL_005C', 
    'ROUTE_NUMBER_005D', 'DIRECTION_005E', 'HIGHWAY_DISTRICT_002', 'COUNTY_CODE_003', 'PLACE_CODE_004', 
    'FEATURES_DESC_006A', 'CRITICAL_FACILITY_006B', 'FACILITY_CARRIED_007', 'LOCATION_009', 'MIN_VERT_CLR_010', 
    'KILOPOINT_011', 'BASE_HWY_NETWORK_012', 'LRS_INV_ROUTE_013A', 'SUBROUTE_NO_013B', 'LAT_016', 
    'LONG_017', 'DETOUR_KILOS_019', 'TOLL_020', 'MAINTENANCE_021', 'OWNER_022', 
    'FUNCTIONAL_CLASS_026', 'YEAR_BUILT_027', 'TRAFFIC_LANES_ON_028A', 'TRAFFIC_LANES_UND_028B', 'ADT_029', 
    'YEAR_ADT_030', 'DESIGN_LOAD_031', 'APPR_WIDTH_MT_032', 'MEDIAN_CODE_033', 'DEGREES_SKEW_034', 
    'STRUCTURE_FLARED_035', 'RAILINGS_036A', 'TRANSITIONS_036B', 'APPR_RAIL_036C', 'APPR_RAIL_END_036D', 
    'HISTORY_037', 'NAVIGATION_038', 'NAV_VERT_CLR_MT_039', 'NAV_HORR_CLR_MT_040', 'OPEN_CLOSED_POSTED_041', 
    'SERVICE_ON_042A', 'SERVICE_UND_042B', 'STRUCTURE_KIND_043A', 'STRUCTURE_TYPE_043B', 'APPR_KIND_044A', 
    'APPR_TYPE_044B', 'MAIN_UNIT_SPANS_045', 'APPR_SPANS_046', 'HORR_CLR_MT_047', 'MAX_SPAN_LEN_MT_048', 
    'STRUCTURE_LEN_MT_049', 'LEFT_CURB_MT_050A', 'RIGHT_CURB_MT_050B', 'ROADWAY_WIDTH_MT_051', 'DECK_WIDTH_MT_052', 
    'VERT_CLR_OVER_MT_053', 'VERT_CLR_UND_REF_054A', 'VERT_CLR_UND_054B', 'LAT_UND_REF_055A', 'LAT_UND_MT_055B', 
    'LEFT_LAT_UND_MT_056', 'DECK_COND_058', 'SUPERSTRUCTURE_COND_059', 'SUBSTRUCTURE_COND_060', 'CHANNEL_COND_061', 
    'CULVERT_COND_062', 'OPR_RATING_METH_063', 'OPERATING_RATING_064', 'INV_RATING_METH_065', 'INVENTORY_RATING_066', 
    'STRUCTURAL_EVAL_067', 'DECK_GEOMETRY_EVAL_068', 'UNDCLRENCE_EVAL_069', 'POSTING_EVAL_070', 'WATERWAY_EVAL_071', 
    'APPR_ROAD_EVAL_072', 'WORK_PROPOSED_075A', 'WORK_DONE_BY_075B', 'IMP_LEN_MT_076', 'DATE_OF_INSPECT_090', 
    'INSPECT_FREQ_MONTHS_091', 'FRACTURE_092A', 'UNDWATER_LOOK_SEE_092B', 'SPEC_INSPECT_092C', 'FRACTURE_LAST_DATE_093A', 
    'UNDWATER_LAST_DATE_093B', 'SPEC_LAST_DATE_093C', 'BRIDGE_IMP_COST_094', 'ROADWAY_IMP_COST_095', 'TOTAL_IMP_COST_096', 
    'YEAR_OF_IMP_097', 'OTHER_STATE_CODE_098A', 'OTHER_STATE_PCNT_098B', 'OTHR_STATE_STRUC_NO_099', 'STRAHNET_HIGHWAY_100', 
    'PARALLEL_STRUCTURE_101', 'TRAFFIC_DIRECTION_102', 'TEMP_STRUCTURE_103', 'HIGHWAY_SYSTEM_104', 'FEDERAL_LANDS_105', 
    'YEAR_RECONSTRUCTED_106', 'DECK_STRUCTURE_TYPE_107', 'SURFACE_TYPE_108A', 'MEMBRANE_TYPE_108B', 'DECK_PROTECTION_108C', 
    'PERCENT_ADT_TRUCK_109', 'NATIONAL_NETWORK_110', 'PIER_PROTECTION_111', 'BRIDGE_LEN_IND_112', 'SCOUR_CRITICAL_113', 
    'FUTURE_ADT_114', 'YEAR_OF_FUTURE_ADT_115', 'MIN_NAV_CLR_MT_116', 'FED_AGENCY', 'SUBMITTED_BY', 
    'BRIDGE_CONDITION', 'LOWEST_RATING', 'DECK_AREA'
]

def parse_nbi_txt(txt_path):
    bridges = defaultdict(lambda: {'over': None, 'unders': []})
    with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        # Skip the header row (first line)
        try:
            next(reader)  # ← This consumes the header
        except StopIteration:
            print("No data found in TXT file.")
            return bridges
        for line_num, row in enumerate(reader, 1):
            if len(row) != len(field_names):
                print(f"Skipping invalid line {line_num}: length {len(row)}")
                continue
            bridge = {}
            for col, value in zip(field_names, row):
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
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        print(f"Root tag: {root.tag}")  # Confirms FHWAELEMENT

        elements_by_struc = defaultdict(list)
        count = 0

        for fhwaed in root.findall('.//FHWAED'):
            struc_text = fhwaed.findtext('STRUCNUM', '').strip()
            if not struc_text:
                continue
            struc = struc_text
            count += 1

            el = {
                'BE01': fhwaed.findtext('EN', ''),
                'BE02': fhwaed.findtext('EPN', '0'),
                'BE03': fhwaed.findtext('TOTALQTY', '0'),
                'BCS01': fhwaed.findtext('CS1', '0'),
                'BCS02': fhwaed.findtext('CS2', '0'),
                'BCS03': fhwaed.findtext('CS3', '0'),
                'BCS04': fhwaed.findtext('CS4', '0')
            }

            elements_by_struc[struc].append(el)

        print(f"Parsed elements for {len(elements_by_struc)} bridges "
              f"({count} element records total) from XML.")
        return elements_by_struc

    except ET.ParseError as e:
        print(f"XML parse error: {e}")
        return defaultdict(list)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return defaultdict(list)

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

def safe_str(value, default=''):
    """Safely convert to stripped string"""
    return str(value or default).strip()


def safe_int(value, default=0):
    """Safely convert to integer"""
    try:
        return int(float(value or default))
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """Safely convert to float"""
    try:
        return float(value or default)
    except (ValueError, TypeError):
        return default


def map_bridge_to_snbi(old, unders):
    """
    Map NBI legacy record to SNBI structure.
    Fully defensive against None/old being invalid.
    """
    if old is None or not isinstance(old, dict):
        print("Warning: map_bridge_to_snbi received invalid 'old' (None or not dict)")
        return {}

    snbi = {}

    # ── Basic Location and Identification ──────────────────────────────────────
    snbi['BL01'] = safe_int(old.get('STATE_CODE_001'), 0)
    snbi['BID01'] = safe_str(old.get('STRUCTURE_NUMBER_008'))
    snbi['BL02'] = safe_int(old.get('COUNTY_CODE_003'), 0)
    snbi['BL03'] = safe_int(old.get('PLACE_CODE_004'), 0)
    snbi['BL04'] = safe_str(old.get('HIGHWAY_DISTRICT_002')).lstrip('0')
    snbi['BL11'] = safe_str(old.get('LOCATION_009'))

    snbi['BW01'] = safe_int(old.get('YEAR_BUILT_027'), 0)

    snbi['BCL01'] = safe_str(old.get('OWNER_022'))
    snbi['BCL02'] = safe_str(old.get('MAINTENANCE_021'))
    snbi['BCL05'] = safe_str(old.get('TOLL_020'))

    snbi['BC01'] = safe_str(old.get('DECK_COND_058'))
    snbi['BC02'] = safe_str(old.get('SUPERSTRUCTURE_COND_059'))
    snbi['BC03'] = safe_str(old.get('SUBSTRUCTURE_COND_060'))
    snbi['BC04'] = safe_str(old.get('CULVERT_COND_062'))

    snbi['BRH01'] = safe_str(old.get('RAILINGS_036A'))
    snbi['BRH02'] = safe_str(old.get('TRANSITIONS_036B'))
    snbi['BG11'] = safe_int(old.get('DEGREES_SKEW_034'), 0)

    # ── Latitude / Longitude ───────────────────────────────────────────────────
    lat_raw = safe_str(old.get('LAT_016'))
    if lat_raw:
        lat_dec = convert_dms_to_decimal(lat_raw)
        if lat_dec is not None:
            snbi['BL05'] = lat_dec

    lon_raw = safe_str(old.get('LONG_017'))
    if lon_raw:
        lon_dec = convert_dms_to_decimal(lon_raw)
        if lon_dec is not None:
            snbi['BL06'] = -lon_dec   # East longitude → negative in US

    # ── Border Bridge Info ─────────────────────────────────────────────────────
    snbi['BL07'] = safe_str(old.get('OTHR_STATE_STRUC_NO_099'))
    border_state_raw = safe_str(old.get('OTHER_STATE_CODE_098A')).lstrip('0')
    border_state = border_state_raw.upper()
    if border_state == 'CAN':
        border_state = 'CA'
    elif border_state == 'MEX':
        border_state = 'MX'
    snbi['BL08'] = border_state
    snbi['BL09'] = safe_str(old.get('OTHER_STATE_PCNT_098B'))

    if border_state:
        snbi['BL10'] = snbi['BL01']   # Designated lead state = own state

    # ── Geometry & Dimensions ──────────────────────────────────────────────────
    struct_len = safe_float(old.get('STRUCTURE_LEN_MT_049'))
    max_span   = safe_float(old.get('MAX_SPAN_LEN_MT_048'))
    deck_width = safe_float(old.get('DECK_WIDTH_MT_052'))
    rway_width = safe_float(old.get('ROADWAY_WIDTH_MT_051'))
    appr_width = safe_float(old.get('APPR_WIDTH_MT_032'))

    snbi['BG02'] = meters_to_feet(struct_len)
    snbi['BG03'] = meters_to_feet(max_span)

    if struct_len and struct_len > 9.1:
        snbi['BG01'] = snbi['BG02']

    main_spans = safe_int(old.get('MAIN_UNIT_SPANS_045'))
    appr_spans = safe_int(old.get('APPR_SPANS_046'))

    if main_spans == 1 and appr_spans == 0:
        snbi['BG04'] = snbi['BG03']

    snbi['BG05'] = meters_to_feet(deck_width) if deck_width > 0 else None
    snbi['BG06'] = meters_to_feet(rway_width)
    snbi['BG07'] = meters_to_feet(old.get('LEFT_CURB_MT_050A'))
    snbi['BG08'] = meters_to_feet(old.get('RIGHT_CURB_MT_050B'))
    snbi['BG09'] = meters_to_feet(appr_width)
    snbi['BG10'] = safe_str(old.get('MEDIAN_CODE_033'))

    deck_ft = snbi.get('BG05') or meters_to_feet(appr_width) or 0.0
    if snbi.get('BG02'):
        snbi['BG16'] = round(snbi['BG02'] * deck_ft, 1)

    # ── Span Sets ──────────────────────────────────────────────────────────────
    snbi['SpanSets'] = []
    structure_type_b = safe_str(old.get('STRUCTURE_TYPE_043B'))

    if main_spans > 0 and structure_type_b != '00':
        main_config = 'M01' if structure_type_b != '19' else 'C01'
        snbi['SpanSets'].append({
            'BSP01': main_config,
            'BSP02': main_spans,
            'BSP04': safe_str(old.get('STRUCTURE_KIND_043A')),
            'BSP06': structure_type_b,
            'BSP09': safe_str(old.get('DECK_STRUCTURE_TYPE_107')),
            'BSP10': safe_str(old.get('SURFACE_TYPE_108A')),
            'BSP11': safe_str(old.get('MEMBRANE_TYPE_108B')),
            'BSP12': safe_str(old.get('DECK_PROTECTION_108C')),
        })

    if appr_spans > 0:
        appr_config = 'A01' if structure_type_b != '19' else 'C02'
        snbi['SpanSets'].append({
            'BSP01': appr_config,
            'BSP02': appr_spans,
            'BSP04': safe_str(old.get('APPR_KIND_044A')),
            'BSP06': safe_str(old.get('APPR_TYPE_044B')),
            'BSP09': safe_str(old.get('DECK_STRUCTURE_TYPE_107')),
            'BSP10': safe_str(old.get('SURFACE_TYPE_108A')),
            'BSP11': safe_str(old.get('MEMBRANE_TYPE_108B')),
            'BSP12': safe_str(old.get('DECK_PROTECTION_108C')),
        })

    # ── Load Rating ────────────────────────────────────────────────────────────
    snbi['BLR01'] = safe_str(old.get('DESIGN_LOAD_031'))
    snbi['BLR04'] = safe_str(old.get('OPR_RATING_METH_063'))
    snbi['BLR05'] = get_rating_factor(old, 'INVENTORY_RATING_066', 'INV_RATING_METH_065')
    snbi['BLR06'] = get_rating_factor(old, 'OPERATING_RATING_064', 'OPR_RATING_METH_063')

    # ── Posting & Condition Flags ──────────────────────────────────────────────
    snbi['BPS01'] = safe_str(old.get('OPEN_CLOSED_POSTED_041'))

    snbi['BIR01'] = (safe_str(old.get('FRACTURE_092A'))[:1] or None)
    snbi['BIR03'] = (safe_str(old.get('UNDWATER_LOOK_SEE_092B'))[:1] or None)

    snbi['BC09'] = safe_str(old.get('CHANNEL_COND_061'))
    snbi['BC11'] = safe_str(old.get('SCOUR_CRITICAL_113'))

    # ── Approach & Waterway Eval ───────────────────────────────────────────────
    snbi['BAP01'] = safe_str(old.get('APPR_ROAD_EVAL_072'))
    snbi['BAP02'] = safe_str(old.get('WATERWAY_EVAL_071'))
    snbi['BAP03'] = safe_str(old.get('SCOUR_CRITICAL_113'))
    snbi['BAP04'] = safe_str(old.get('SCOUR_CRITICAL_113'))  # same as BAP03

    # ── Work History ───────────────────────────────────────────────────────────
    snbi['Works'] = []
    year_recon = safe_int(old.get('YEAR_RECONSTRUCTED_106'))
    if year_recon > 0:
        snbi['Works'].append({
            'BW02': year_recon,
            'BW03': 'RECONSTRUCTED'
        })

    # ── Features (Over) ────────────────────────────────────────────────────────
    snbi['Features'] = []
    service_on = safe_str(old.get('SERVICE_ON_042A'))

    if service_on in {'1', '4', '5', '6', '7', '8'}:
        feat = {
            'BF01': 'H01',
            'BF02': 'C',
            'BF03': safe_str(old.get('FACILITY_CARRIED_007')),
            'BH01': safe_str(old.get('FUNCTIONAL_CLASS_026')),
            'BH02': safe_str(old.get('FUNCTIONAL_CLASS_026')),  # TODO: real mapping needed
            'BH03': safe_str(old.get('HIGHWAY_SYSTEM_104')),
            'BH04': safe_str(old.get('NATIONAL_NETWORK_110')),
            'BH05': safe_str(old.get('STRAHNET_HIGHWAY_100')),
            'BH06': (safe_str(old.get('LRS_INV_ROUTE_013A')) +
                     safe_str(old.get('SUBROUTE_NO_013B'))).strip().lstrip('0') or None,
            'BH07': km_to_mile(old.get('KILOPOINT_011')),
            'BH08': safe_int(old.get('TRAFFIC_LANES_ON_028A')),
            'BH09': safe_int(old.get('ADT_029')),
            'BH10': safe_int(old.get('ADT_029')) * safe_int(old.get('PERCENT_ADT_TRUCK_109')) // 100,
            'BH11': safe_int(old.get('YEAR_ADT_030')),
            'BH12': meters_to_feet(old.get('MIN_VERT_CLR_010'), round_down=True, cap99=True),
            'BH13': meters_to_feet(old.get('VERT_CLR_OVER_MT_053'), round_down=True, cap99=True),
            'BH16': meters_to_feet(old.get('HORR_CLR_MT_047'), round_down=True, cap99=True),
            'BH17': 999 if safe_str(old.get('DETOUR_KILOS_019')) == '199' else
                    round(safe_float(old.get('DETOUR_KILOS_019')) / 1.60934)
        }

        route_num = safe_str(old.get('ROUTE_NUMBER_005D')).lstrip('0') or '0'
        route_num += safe_str(old.get('DIRECTION_005E'))

        route = {
            'BRT01': 'R01',
            'BRT02': route_num,
            'BRT03': safe_str(old.get('TRAFFIC_DIRECTION_102')),
            'BRT04': safe_str(old.get('ROUTE_PREFIX_005B')),
            'BRT05': safe_str(old.get('SERVICE_LEVEL_005C'))
        }
        feat['Routes'] = [route]
        snbi['Features'].append(feat)

    # ── Under Features ─────────────────────────────────────────────────────────
    service_und = safe_str(old.get('SERVICE_UND_042B'))
    if service_und != '0' and unders:
        primary_under, secondary_unders = determine_primary_under(unders)
        highway_under = service_und in {'1', '3', '5', '6', '7', '8', '9'}
        railroad_under = service_und in {'2', '3', '7', '9'}
        water_under = service_und in {'3', '4', '8', '9'}

        if highway_under:
            under_records = ([primary_under] if primary_under else []) + secondary_unders
            h_num = 2
            for u in under_records:
                if not isinstance(u, dict):
                    continue
                feat = {
                    'BF01': f'H{h_num:02d}',
                    'BF02': 'B',
                    'BF03': safe_str(u.get('FEATURES_DESC_006A') or old.get('FEATURES_DESC_006A')),
                    'BH01': safe_str(u.get('FUNCTIONAL_CLASS_026')),
                    'BH02': safe_str(u.get('FUNCTIONAL_CLASS_026')),  # TODO: real mapping
                    # ... rest of highway fields using u.get() with safe_ helpers ...
                    # (you can copy pattern from over feature)
                }
                # Route for under (similar pattern)
                route_num = safe_str(u.get('ROUTE_NUMBER_005D')).lstrip('0') or '0'
                route_num += safe_str(u.get('DIRECTION_005E'))
                route = {
                    'BRT01': 'R01',
                    'BRT02': route_num,
                    'BRT03': safe_str(u.get('TRAFFIC_DIRECTION_102')),
                    'BRT04': safe_str(u.get('ROUTE_PREFIX_005B')),
                    'BRT05': safe_str(u.get('SERVICE_LEVEL_005C'))
                }
                feat['Routes'] = [route]
                snbi['Features'].append(feat)
                h_num += 1

        # Railroad & Water features (similar safe pattern can be applied)

    return snbi

# Main execution
txt_path = r'D:\SNBI_Bridge_App\SNBI_Bridge_App\database\NJ25.txt'  # Replace
xml_path = r'D:\SNBI_Bridge_App\SNBI_Bridge_App\database\2025NJ_ElementData.xml'  # Replace
bridges_data = parse_nbi_txt(txt_path)
elements_by_struc = parse_elements_xml(xml_path)
json_bridges = []
skipped = 0

for struc, bridge_data in bridges_data.items():
    old = bridge_data.get('over')
    if old is None or not isinstance(old, dict) or not old:
        unders_count = len(bridge_data.get('unders', []))
        print(f"Skipped structure {struc!r}: "
              f"no valid 'over' record, but has {unders_count} under record(s)")
        skipped += 1
        continue

    unders = bridge_data.get('unders', [])
    try:
        snbi_bridge = map_bridge_to_snbi(old, unders)
        elems = elements_by_struc.get(struc, [])
        if elems:
            snbi_bridge['Elements'] = elems
        json_bridges.append(snbi_bridge)
    except Exception as e:
        print(f"Mapping failed for {struc}: {e}")
        skipped += 1

print(f"Converted {len(json_bridges)} bridges (skipped {skipped})")
with open('nj_bridges_converted.json', 'w', encoding='utf-8') as f:
    json.dump(json_bridges, f, indent=2, ensure_ascii=False)
print(f"Converted {len(json_bridges)} bridges to nj_bridges_converted.json")