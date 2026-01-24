import streamlit as st
import sqlite3
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium import plugins
import plotly.express as px
from datetime import datetime
import re
import json
import pandas as pd
from collections import defaultdict
import xml.etree.ElementTree as ET
import math
import csv
import json
import sqlite3
from typing import Dict, Any, List
import streamlit as st
import io
import tempfile
import json
from pathlib import Path
from PIL import Image
import os
import sys

import shutil

def resource_path(relative_path):
    try:
        # If running as EXE, PyInstaller sets _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # If running as script
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

USER_DB = os.path.join(os.path.expanduser("~"), "snbi_bridges.db")

if not os.path.exists(USER_DB):
    bundled_db = resource_path("bridges.db")  # Your existing resource_path function
    shutil.copy(bundled_db, USER_DB)
    print("Copied initial database to user folder.")

save_dir = os.path.join(os.path.expanduser("~"), "SNBI_Exports")
os.makedirs(save_dir, exist_ok=True)

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #FAFAD2 0%, #F0F8FF 100%);
    }
    </style>
    """,
    unsafe_allow_html=True
)

img_path = resource_path("image_bridge.png")



# Load image
img = Image.open(img_path)  # replace with your file path

# Display image
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image(img, use_container_width=True)

# 👉 import ALL your existing functions here
# from converter import (
#     parse_nbi_txt, parse_elements_xml, map_bridge_to_snbi
# )
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

#st.set_page_config(page_title="NBI → SNBI Converter", layout="wide")
# Option 1 – Clean & Modern Blue Gradient (my favorite)


# Option 2 – Professional Dark Theme + Gold Accent
st.markdown("""
    <h1 style='
        text-align: center;
        color: #1f2937;   /* dark gray text */
        padding: 20px;
        font-weight: bold;
    '>
        SNBI Converter
    </h1>
""", unsafe_allow_html=True)

st.write(
    "Upload an **NBI TXT file** and the corresponding **Element XML file** "
    "to generate an SNBI-compliant JSON output."
)

# ─────────────────────────────────────────────
# File uploads
# ─────────────────────────────────────────────
txt_file = st.file_uploader(
    "Upload NBI TXT file",
    type=["txt", "csv"]
)

xml_file = st.file_uploader(
    "Upload Element XML file",
    type=["xml"]
)

# ─────────────────────────────────────────────
# Convert button
# ─────────────────────────────────────────────
if st.button("Convert to SNBI JSON", disabled=not (txt_file and xml_file)):

    with st.spinner("Processing files..."):

        # Save uploads to temp files
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = Path(tmpdir) / txt_file.name
            xml_path = Path(tmpdir) / xml_file.name

            txt_path.write_bytes(txt_file.getbuffer())
            xml_path.write_bytes(xml_file.getbuffer())

            # ── Run your existing pipeline ─────────────────────
            bridges_data = parse_nbi_txt(txt_path)
            elements_by_struc = parse_elements_xml(xml_path)

            json_bridges = []
            skipped = 0

            for struc, bridge_data in bridges_data.items():
                old = bridge_data.get("over")

                if not old or not isinstance(old, dict):
                    skipped += 1
                    continue

                unders = bridge_data.get("unders", [])

                try:
                    snbi_bridge = map_bridge_to_snbi(old, unders)

                    elems = elements_by_struc.get(struc, [])
                    if elems:
                        snbi_bridge["Elements"] = elems

                    json_bridges.append(snbi_bridge)

                except Exception as e:
                    skipped += 1
                    st.warning(f"Mapping failed for {struc}: {e}")

    # ─────────────────────────────────────────
    # Results
    # ─────────────────────────────────────────
    st.success(f"Converted {len(json_bridges)} bridges (skipped {skipped})")

    # Preview
    with st.expander("Preview JSON"):
        st.json(json_bridges[:1])

    # Download
    json_bytes = json.dumps(
        json_bridges,
        indent=2,
        ensure_ascii=False
    ).encode("utf-8")


    save_path = os.path.join(
        save_dir,
        f"snbi_bridges.json"
    )

    with open(save_path, "wb") as f:
        f.write(json_bytes)

    st.success(f"Saved locally to: {save_path}")






# Column mapping from JSON keys to SQL column names
mapping = {
    'BL01': 'state_code',
    'BID01': 'bridge_number',
    'BID02': 'bridge_name',
    'BID03': 'previous_bridge_number',
    'BL02': 'county_code',
    'BL03': 'place_code',
    'BL04': 'highway_agency_district',
    'BL05': 'latitude',
    'BL06': 'longitude',
    'BL07': 'border_bridge_number',
    'BL08': 'border_bridge_state_or_country_code',
    'BL09': 'border_bridge_inspection_responsibility',
    'BL10': 'border_bridge_designated_lead_state',
    'BL11': 'bridge_location',
    'BL12': 'metropolitan_planning_organization',
    'BCL01': 'owner',
    'BCL02': 'maintenance_responsibility',
    'BCL03': 'federal_or_tribal_land_access',
    'BCL04': 'historical_significance',
    'BCL05': 'toll',
    'BCL06': 'emergency_evacuation_designation',
    'BRH01': 'bridge_railings',
    'BRH02': 'transitions',
    'BG01': 'nbis_bridge_length',
    'BG02': 'total_bridge_length',
    'BG03': 'maximum_span_length',
    'BG04': 'minimum_span_length',
    'BG05': 'bridge_width_out_to_out',
    'BG06': 'bridge_width_curb_to_curb',
    'BG07': 'left_curb_or_sidewalk_width',
    'BG08': 'right_curb_or_sidewalk_width',
    'BG09': 'approach_roadway_width',
    'BG10': 'bridge_median',
    'BG11': 'skew',
    'BG12': 'curved_bridge',
    'BG13': 'maximum_bridge_height',
    'BG14': 'sidehill_bridge',
    'BG15': 'irregular_deck_area',
    'BG16': 'calculated_deck_area',
    'BLR01': 'designed_load',
    'BLR02': 'designed_method',
    'BLR03': 'load_rating_date',
    'BLR04': 'load_rating_method',
    'BLR05': 'inventory_load_rating_factor',
    'BLR06': 'operating_load_rating_factor',
    'BLR07': 'controlling_legal_load_rating_factor',
    'BLR08': 'routine_permit_loads',
    'BIR01': 'nstm_inspection_required',
    'BIR02': 'fatigue_details',
    'BIR03': 'underwater_inspection_required',
    'BIR04': 'complex_feature',
    'BC01': 'deck_condition_rating',
    'BC02': 'superstructure_condition_rating',
    'BC03': 'substructure_condition_rating',
    'BC04': 'culvert_condition_rating',
    'BC05': 'bridge_railings_condition_rating',
    'BC06': 'bridge_railings_transitions_condition_rating',
    'BC07': 'bridge_bearings_condition_rating',
    'BC08': 'bridge_joints_condition_rating',
    'BC09': 'channel_condition_rating',
    'BC10': 'channel_protection_condition_rating',
    'BC11': 'scour_condition_rating',
    'BC12': 'bridge_condition_classification',
    'BC13': 'lowest_condition_rating_code',
    'BC14': 'nstm_inspection_condition',
    'BC15': 'underwater_inspection_condition',
    'BAP01': 'approach_roadway_alignment',
    'BAP02': 'overtopping_likelihood',
    'BAP03': 'scour_vulnerability',
    'BAP04': 'scour_plan_of_action',
    'BAP05': 'seismic_vulnerability',
    'BW01': 'year_built',
    'BE01': 'element_number',
    'BE02': 'element_parent_number',
    'BE03': 'element_total_quantity',
    'BCS01': 'element_quantity_condition_state_one',
    'BCS02': 'element_quantity_condition_state_two',
    'BCS03': 'element_quantity_condition_state_three',
    'BCS04': 'element_quantity_condition_state_four',
    'BF01': 'feature_type',
    'BF02': 'feature_location',
    'BF03': 'feature_name',
    'BH01': 'functional_classification',
    'BH02': 'urban_code',
    'BH03': 'nhs_designation',
    'BH04': 'national_highway_freight_network',
    'BH05': 'strahnet_designation',
    'BH06': 'lrs_route_id',
    'BH07': 'lrs_mile_point',
    'BH08': 'lanes_on_highway',
    'BH09': 'annual_average_daily_traffic',
    'BH10': 'annual_average_daily_truck_traffic',
    'BH11': 'year_of_annual_average_daily_traffic',
    'BH12': 'highway_max_usable_vertical_clearance',
    'BH13': 'highway_min_vertical_clearance',
    'BH14': 'highway_min_horizontal_clearance_left',
    'BH15': 'highway_min_horizontal_clearance_right',
    'BH16': 'highway_max_usable_surface_width',
    'BH17': 'bypass_detour_length',
    'BH18': 'crossing_bridge_number',
    'BRR01': 'railroad_service_type',
    'BRR02': 'railroad_min_vertical_clearance',
    'BRR03': 'railroad_min_horizontal_offset',
    'BN01': 'navigable_waterway',
    'BN02': 'navigable_min_vertical_clearance',
    'BN03': 'movable_bridge_max_navigation_vertical_clearance',
    'BN04': 'navigation_channel_width',
    'BN05': 'navigation_channel_min_horizontal_clearance',
    'BN06': 'substructure_navigation_protection',
    'BRT01': 'route_designation',
    'BRT02': 'route_number',
    'BRT03': 'route_direction',
    'BRT04': 'route_type',
    'BRT05': 'service_type',
    'BIE01': 'inspection_type',
    'BIE02': 'inspection_begin_date',
    'BIE03': 'inspection_completion_date',
    'BIE04': 'nationally_certified_bridge_inspector',
    'BIE05': 'inspection_interval',
    'BIE06': 'inspection_due_date',
    'BIE07': 'risk_based_inspection_interval_method',
    'BIE08': 'inspection_quality_control_date',
    'BIE09': 'inspection_quality_assurance_date',
    'BIE10': 'inspection_data_update_date',
    'BIE11': 'inspection_note',
    'BIE12': 'inspection_equipment',
    'BEP01': 'legal_load_configuration',
    'BEP02': 'legal_load_rating_factor',
    'BEP03': 'posting_type',
    'BEP04': 'posting_value',
    'BPS02': 'posting_status_change_date',
    'BPS01': 'load_posting_status',
    'BSP01': 'span_configuration_designation',
    'BSP02': 'number_of_spans',
    'BSP03': 'number_of_beam_lines',
    'BSP04': 'span_material',
    'BSP05': 'span_continuity',
    'BSP06': 'span_type',
    'BSP07': 'span_protective_system',
    'BSP08': 'deck_interaction',
    'BSP09': 'deck_material_and_type',
    'BSP10': 'wearing_surface',
    'BSP11': 'deck_protective_system',
    'BSP12': 'deck_reinforcing_protective_system',
    'BSP13': 'deck_stay_in_place_forms',
    'BSB01': 'substructure_configuration_designation',
    'BSB02': 'number_of_substructure_units',
    'BSB03': 'substructure_material',
    'BSB04': 'substructure_type',
    'BSB05': 'substructure_protective_system',
    'BSB06': 'foundation_type',
    'BSB07': 'foundation_protective_system',
    'BW02': 'year_work_performed',
    'BW03': 'work_performed'
}

# Main excluded keys for bridges table (very important!)
BRIDGE_EXCLUDE_KEYS = [
    'Features', 'SpanSets', 'SubstructureSets',
    'PostingEvaluations', 'PostingStatuses',
    'Inspections', 'Elements', 'Works'
]

def safe_insert(cursor, table: str, data: Dict[str, Any]):
    """Helper to insert safely with error reporting"""
    if not data:
        return
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?'] * len(data))
    values = list(data.values())
    try:
        cursor.execute(f"INSERT OR IGNORE INTO {table} ({columns}) VALUES ({placeholders})", values)
    except sqlite3.Error as e:
        print(f"Error inserting into {table}: {e}")
        print(f" → Data keys: {list(data.keys())}")

# ── Main execution ──────────────────────────────────────────────────────────────
# ── UI FIRST ────────────────────────────────────────────────────────────────────
st.markdown("""
    <h1 style='
        text-align: center;
        color: #1f2937;   /* dark gray text */
        padding: 20px;
        font-weight: bold;
    '>
        SNBI Loader
    </h1>
""", unsafe_allow_html=True)


uploaded_file = st.file_uploader("Upload bridge JSON", type=["json"])

if st.button(" Load into SNBI Database ", disabled=not uploaded_file):
    conn = sqlite3.connect(USER_DB)

    def get_table_columns(cursor, table_name):
        cursor.execute(f"PRAGMA table_info({table_name})")
        return {row[1] for row in cursor.fetchall()}

    cursor = conn.cursor()
    BRIDGES_COLUMNS = get_table_columns(cursor, "bridges")





    try:
        data: List[Dict] = json.load(uploaded_file)
        st.success(f"Loaded {len(data)} bridges")
    except Exception as e:
        st.error(f"Failed to load JSON: {e}")
        st.stop()


    processed = 0
    skipped = 0
    progress = st.progress(0)
    status = st.empty()
    total = len(data)

    for bridge_data in data:
        state_code = bridge_data.get('BL01')
        bridge_number = bridge_data.get('BID01')

        if not state_code or not bridge_number:
            st.warning("Skipping invalid bridge record (missing state_code or bridge_number)")

            skipped += 1
            continue

        progress.progress((processed + 1) / total)

        status.text(f"Processing {state_code}-{bridge_number}")


        # ── 1. Main bridge table ────────────────────────────────────────────────
        bridge_insert = {}

        for key, value in bridge_data.items():
            if key in mapping:
                col = mapping[key]
                if col in BRIDGES_COLUMNS:
                    bridge_insert[col] = value

        # VERY IMPORTANT: ensure PK fields are present
        bridge_insert['state_code'] = state_code
        bridge_insert['bridge_number'] = bridge_number

        if bridge_insert:
            safe_insert(cursor, 'bridges', bridge_insert)
        else:
            st.warning(f"\n⚠️  No bridge columns matched for {state_code}-{bridge_number}")

        # ── 2. Features + Routes ────────────────────────────────────────────────
        for feat in bridge_data.get('Features', []):
            feat_insert = {'state_code': state_code, 'bridge_number': bridge_number}
            for k, v in feat.items():
                if k in mapping and k != 'Routes':
                    feat_insert[mapping[k]] = v
            safe_insert(cursor, 'features', feat_insert)

            # Routes
            for route in feat.get('Routes', []):
                route_insert = {
                    'state_code': state_code,
                    'bridge_number': bridge_number,
                    'feature_type': feat.get('BF01')
                }
                for rk, rv in route.items():
                    if rk in mapping:
                        route_insert[mapping[rk]] = rv
                safe_insert(cursor, 'routes', route_insert)

        # ── 3. Span Sets ────────────────────────────────────────────────────────
        for span in bridge_data.get('SpanSets', []):
            span_insert = {'state_code': state_code, 'bridge_number': bridge_number}
            for k, v in span.items():
                if k in mapping:
                    span_insert[mapping[k]] = v
            safe_insert(cursor, 'span_sets', span_insert)

        # ── 4. Substructure Sets ────────────────────────────────────────────────
        for sub in bridge_data.get('SubstructureSets', []):
            sub_insert = {'state_code': state_code, 'bridge_number': bridge_number}
            for k, v in sub.items():
                if k in mapping:
                    sub_insert[mapping[k]] = v
            safe_insert(cursor, 'substructure_sets', sub_insert)

        # ── 5. Posting Evaluations ──────────────────────────────────────────────
        for pe in bridge_data.get('PostingEvaluations', []):
            pe_insert = {'state_code': state_code, 'bridge_number': bridge_number}
            for k, v in pe.items():
                if k in mapping:
                    pe_insert[mapping[k]] = v
            safe_insert(cursor, 'posting_evaluations', pe_insert)

        # ── 6. Posting Statuses ─────────────────────────────────────────────────
        for ps in bridge_data.get('PostingStatuses', []):
            ps_insert = {'state_code': state_code, 'bridge_number': bridge_number}
            for k, v in ps.items():
                if k in mapping:
                    ps_insert[mapping[k]] = v
            safe_insert(cursor, 'posting_statuses', ps_insert)

        # ── 7. Inspections ──────────────────────────────────────────────────────
        for insp in bridge_data.get('Inspections', []):
            insp_insert = {'state_code': state_code, 'bridge_number': bridge_number}
            for k, v in insp.items():
                if k in mapping:
                    insp_insert[mapping[k]] = v
            safe_insert(cursor, 'inspections', insp_insert)

        # ── 8. Elements ─────────────────────────────────────────────────────────
        for elem in bridge_data.get('Elements', []):
            elem_insert = {'state_code': state_code, 'bridge_number': bridge_number}
            for k, v in elem.items():
                if k in mapping:
                    elem_insert[mapping[k]] = v
            # Default for missing parent
            if 'element_parent_number' not in elem_insert:
                elem_insert['element_parent_number'] = '0'
            safe_insert(cursor, 'elements', elem_insert)

        # ── 9. Works ────────────────────────────────────────────────────────────
        for work in bridge_data.get('Works', []):
            work_insert = {'state_code': state_code, 'bridge_number': bridge_number}
            for k, v in work.items():
                if k in mapping:
                    work_insert[mapping[k]] = v
            safe_insert(cursor, 'works', work_insert)

        processed += 1
        status.text(f"Inserted {state_code}-{bridge_number}")


    conn.commit()
    conn.close()

    st.write(f"\nFinished!")
    st.write(f"Successfully processed: {processed} bridges")
    st.write(f"Skipped: {skipped} invalid records")














# Complete US state/territory FIPS code mapping (used in National Bridge Inventory - NBI)
# Codes are 2-digit (stored as int 1-78). Includes all 50 states + DC + territories
STATE_MAP = {
    1: 'Alabama (AL)',
    2: 'Alaska (AK)',
    4: 'Arizona (AZ)',
    5: 'Arkansas (AR)',
    6: 'California (CA)',
    8: 'Colorado (CO)',
    9: 'Connecticut (CT)',
    10: 'Delaware (DE)',
    11: 'District of Columbia (DC)',
    12: 'Florida (FL)',
    13: 'Georgia (GA)',
    15: 'Hawaii (HI)',
    16: 'Idaho (ID)',
    17: 'Illinois (IL)',
    18: 'Indiana (IN)',
    19: 'Iowa (IA)',
    20: 'Kansas (KS)',
    21: 'Kentucky (KY)',
    22: 'Louisiana (LA)',
    23: 'Maine (ME)',
    24: 'Maryland (MD)',
    25: 'Massachusetts (MA)',
    26: 'Michigan (MI)',
    27: 'Minnesota (MN)',
    28: 'Mississippi (MS)',
    29: 'Missouri (MO)',
    30: 'Montana (MT)',
    31: 'Nebraska (NE)',
    32: 'Nevada (NV)',
    33: 'New Hampshire (NH)',
    34: 'New Jersey (NJ)',
    35: 'New Mexico (NM)',
    36: 'New York (NY)',
    37: 'North Carolina (NC)',
    38: 'North Dakota (ND)',
    39: 'Ohio (OH)',
    40: 'Oklahoma (OK)',
    41: 'Oregon (OR)',
    42: 'Pennsylvania (PA)',
    44: 'Rhode Island (RI)',
    45: 'South Carolina (SC)',
    46: 'South Dakota (SD)',
    47: 'Tennessee (TN)',
    48: 'Texas (TX)',
    49: 'Utah (UT)',
    50: 'Vermont (VT)',
    51: 'Virginia (VA)',
    53: 'Washington (WA)',
    54: 'West Virginia (WV)',
    55: 'Wisconsin (WI)',
    56: 'Wyoming (WY)',
    # Territories (included for completeness - NBI uses these)
    60: 'American Samoa (AS)',
    66: 'Guam (GU)',
    69: 'Northern Mariana Islands (MP)',
    72: 'Puerto Rico (PR)',
    78: 'Virgin Islands (VI)',
}
# Connect to the SQLite database
conn = sqlite3.connect(USER_DB)

# Get list of tables dynamically
tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
tables = tables_df['name'].tolist()

st.markdown("""
    <h1 style='
        text-align: center;
        color: #1f2937;   /* dark gray text */
        padding: 20px;
        font-weight: bold;
    '>
        SNBI Explorer
    </h1>
""", unsafe_allow_html=True)


# Reverse map for display → code
STATE_OPTIONS = {v: k for k, v in STATE_MAP.items()}

selected_state_name = st.selectbox(
    "Filter by State",
    options=["All States"] + list(STATE_OPTIONS.keys())
)

selected_state_code = (
    None if selected_state_name == "All States"
    else STATE_OPTIONS[selected_state_name]
)


tabs = st.tabs(tables)

for tab, table_name in zip(tabs, tables):
    with tab:
        

        # Check table schema for state_code
        cols = pd.read_sql_query(f"PRAGMA table_info({table_name})", conn)
        col_names = cols["name"].tolist()

        if selected_state_code is not None and "state_code" in col_names:
            query = f"""
                SELECT *
                FROM {table_name}
                WHERE state_code = ?
            """
            df = pd.read_sql_query(query, conn, params=(selected_state_code,))
        else:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        
        st.subheader(table_name)

        st.dataframe(
            df,
            use_container_width=True,
            height=500
        )

# Map section at the bottom
st.markdown("""
    <h1 style='
        text-align: center;
        color: #1f2937;   /* dark gray text */
        padding: 20px;
        font-weight: bold;
    '>
        GIS map
    </h1>
""", unsafe_allow_html=True)


# Query bridges table for locations
bridges_df = pd.read_sql_query('''
    SELECT bridge_name, bridge_number, latitude, longitude, state_code
    FROM bridges 
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
''', conn)

if not bridges_df.empty:
    # ... your existing code ...

    # Create Folium map centered on average location
    avg_lat = bridges_df['latitude'].mean()
    avg_lon = bridges_df['longitude'].mean()
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=10,
                tiles="cartodbpositron")   # ← nicer background for borders

    # ------------------ Add US state borders ------------------
    STATE_BORDERS = "https://raw.githubusercontent.com/python-visualization/folium-example-data/main/us_states.json"

    folium.GeoJson(
        STATE_BORDERS,
        name="US States",
        style_function=lambda x: {
            'fillColor': 'transparent',     # ← no fill = only borders
            'color': '#333333',             # dark gray
            'weight': 2,                    # border thickness
            'opacity': 0.7
        }
    ).add_to(m)

    # Optional: make states slightly visible (very light fill)
    # 'fillColor': '#f0f0f0', 'fillOpacity': 0.1,
    # Create cluster group
    marker_cluster = plugins.MarkerCluster(
            name="Bridges",
            overlay=True,
            control=True,
            options={"maxClusterRadius": 80, "disableClusteringAtZoom": 15}  # adjust as needed
        ).add_to(m)
    # Add markers for each bridge
    for _, row in bridges_df.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"{row['bridge_name']}<br>{row['bridge_number']}",
            tooltip=row['bridge_name']
        ).add_to(marker_cluster)

    # Optional but useful: layer control
    folium.LayerControl().add_to(m)

    # Display the map in Streamlit
    col1, col2, col3 = st.columns([1, 4, 1])  # middle column is bigger
    with col2:
        folium_static(m, width=700, height=500)

else:
    st.write('No bridge locations available in the database.')

st.markdown("""
    <h1 style='
        text-align: center;
        color: #1f2937;   /* dark gray text */
        padding: 20px;
        font-weight: bold;
    '>
        SNBI KPIs
    </h1>
""", unsafe_allow_html=True)


@st.cache_data
def get_state_kpis():
    current_year = datetime.now().year  # 2026 in your case

    # Query main bridges + join features for traffic (take max AADT per bridge)
    query = """
    SELECT 
        b.state_code,
        b.bridge_number,
        b.year_built,
        b.deck_condition_rating,
        b.superstructure_condition_rating,
        b.substructure_condition_rating,
        b.culvert_condition_rating,
        b.calculated_deck_area,
        b.total_bridge_length,
        b.bridge_width_out_to_out,
        MAX(f.annual_average_daily_traffic) as aadt
    FROM bridges b
    LEFT JOIN features f 
        ON b.state_code = f.state_code AND b.bridge_number = f.bridge_number
    GROUP BY b.state_code, b.bridge_number
    """
    df = pd.read_sql_query(query, conn)

    # Convert ratings to numeric (handle 'N', NULL, etc. → NaN)
    for col in ['deck_condition_rating', 'superstructure_condition_rating', 
                'substructure_condition_rating', 'culvert_condition_rating']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Overall lowest condition (ignore NaN for culvert if not applicable)
    condition_cols = ['deck_condition_rating', 'superstructure_condition_rating', 
                      'substructure_condition_rating']
    df['lowest_condition'] = df[condition_cols].min(axis=1, skipna=True)
    
    # For culvert bridges (if lowest from main is NaN but culvert exists)
    df['lowest_condition'] = df.apply(
        lambda row: row['culvert_condition_rating'] 
        if pd.isna(row['lowest_condition']) and not pd.isna(row['culvert_condition_rating'])
        else row['lowest_condition'], axis=1
    )

    # Classify Good/Fair/Poor
    def classify_condition(rating):
        if pd.isna(rating):
            return 'Unknown'
        if rating >= 7:
            return 'Good'
        elif rating >= 5:
            return 'Fair'
        else:
            return 'Poor'

    df['condition_class'] = df['lowest_condition'].apply(classify_condition)

    # Deck area fallback
    df['deck_area'] = df['calculated_deck_area'].fillna(
        df['total_bridge_length'] * df['bridge_width_out_to_out']
    ).fillna(0)

    # Map state codes
    df['state_name'] = df['state_code'].map(STATE_MAP).fillna('Unknown')

    # Aggregate per state
    kpi_df = df.groupby(['state_code', 'state_name']).agg(
        total_bridges=('bridge_number', 'count'),
        good_bridges=('condition_class', lambda x: (x == 'Good').sum()),
        fair_bridges=('condition_class', lambda x: (x == 'Fair').sum()),
        poor_bridges=('condition_class', lambda x: (x == 'Poor').sum()),
        avg_age=('year_built', lambda x: current_year - x.mean() if x.notna().any() else None),
        total_deck_area=('deck_area', 'sum'),
        high_traffic_bridges=('aadt', lambda x: (x > 10000).sum()),
        old_bridges=('year_built', lambda x: (x < 1980).sum())
    ).reset_index()

    kpi_df['pct_good'] = (kpi_df['good_bridges'] / kpi_df['total_bridges'] * 100).round(1)
    kpi_df['pct_fair'] = (kpi_df['fair_bridges'] / kpi_df['total_bridges'] * 100).round(1)
    kpi_df['pct_poor'] = (kpi_df['poor_bridges'] / kpi_df['total_bridges'] * 100).round(1)
    kpi_df['pct_old'] = (kpi_df['old_bridges'] / kpi_df['total_bridges'] * 100).round(1)

    return kpi_df

kpi_df = get_state_kpis()

if not kpi_df.empty:

    st.subheader("Overview")

    cols = st.columns(5)

    total_bridges_all = int(kpi_df['total_bridges'].sum())
    poor_pct_all = kpi_df['pct_poor'].mean().round(1)
    avg_age_all = kpi_df['avg_age'].mean().round(1)
    total_poor_bridges = int(kpi_df['poor_bridges'].sum())
    pct_old_all = kpi_df['pct_old'].mean().round(1)

    cols[0].metric("Total Bridges (Nationwide)", f"{total_bridges_all:,}")
    cols[1].metric("Avg % Poor Condition", f"{poor_pct_all}%", delta_color="inverse")
    cols[2].metric("Total Poor Bridges", f"{total_poor_bridges:,}")
    cols[3].metric("Avg Bridge Age (years)", f"{avg_age_all}")
    cols[4].metric("% Built Pre-1980", f"{pct_old_all}%")


    # Detailed table with progress bars
    st.subheader("KPIs by State")

    st.dataframe(
        kpi_df[['state_name', 'total_bridges', 'pct_good', 'pct_fair', 'pct_poor',
                'poor_bridges', 'avg_age', 'high_traffic_bridges',
                'pct_old', 'total_deck_area']],
        column_config={
            "state_name": "State",
            "total_bridges": st.column_config.NumberColumn("Total Bridges"),
            "pct_good": st.column_config.ProgressColumn("% Good", min_value=0, max_value=100),
            "pct_fair": st.column_config.ProgressColumn("% Fair", min_value=0, max_value=100),
            "pct_poor": st.column_config.ProgressColumn("% Poor", min_value=0, max_value=100),
            "poor_bridges": "Poor Bridges",
            "avg_age": st.column_config.NumberColumn("Avg Age (years)", format="%.1f"),
            "high_traffic_bridges": "High Traffic (>10k AADT)",
            "pct_old": st.column_config.ProgressColumn("% Pre-1980", min_value=0, max_value=100),
            "total_deck_area": st.column_config.NumberColumn("Total Deck Area", format="%.0f")
        },
        hide_index=True,
        use_container_width=True
    )


    # Visualizations
    st.subheader("Dashboard")

    # Stacked bar for condition %
    fig_cond = px.bar(
        kpi_df.sort_values('state_name'),
        x='state_name',
        y=['pct_good', 'pct_fair', 'pct_poor'],
        title="Bridge Condition Distribution by State (%)",
        labels={'value': '% of Bridges', 'variable': 'Condition'},
        color_discrete_map={'pct_good': '#00CC96', 'pct_fair': '#FFA500', 'pct_poor': '#EF553B'},
        barmode='stack'
    )
    fig_cond.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_cond, use_container_width=True)

    # Choropleth for % poor
    kpi_df['state_abbr'] = kpi_df['state_name'].apply(
        lambda x: x.split('(')[-1].rstrip(')') if '(' in str(x) else ''
    )
    fig_map = px.choropleth(
        kpi_df,
        locations='state_abbr',
        locationmode="USA-states",
        color='pct_poor',
        scope="usa",
        color_continuous_scale="Reds",
        title="% of Bridges in Poor Condition by State",
        labels={'pct_poor': '% Poor'}
    )
    fig_map.update_layout(geo_visible=False)
    st.plotly_chart(fig_map, use_container_width=True)

    # Avg age bar
    fig_age = px.bar(
        kpi_df.sort_values('avg_age', ascending=False),
        x='state_name',
        y='avg_age',
        title="Average Bridge Age by State (years)",
        color='avg_age',
        color_continuous_scale="YlOrRd"
    )
    fig_age.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_age, use_container_width=True)

else:
    st.info("No bridge data available for KPI calculations.")



# ------------------ Bridge Editor Section ------------------







CHILD_TABLES = [
    "features",
    "span_sets",
    "substructure_sets",
    "elements",
    "inspections",
    "posting_evaluations",
    "posting_statuses",
    "works"
]

# ----------------------------
# Database helpers
# ----------------------------
def get_connection():
    conn = sqlite3.connect(USER_DB, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def update_bridge_id(old_state, old_bridge, new_state, new_bridge):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")

        for table in CHILD_TABLES:
            cur.execute(f"""
                UPDATE {table}
                SET state_code=?, bridge_number=?
                WHERE state_code=? AND bridge_number=?
            """, (new_state, new_bridge, old_state, old_bridge))

        cur.execute("""
            UPDATE bridges
            SET state_code=?, bridge_number=?
            WHERE state_code=? AND bridge_number=?
        """, (new_state, new_bridge, old_state, old_bridge))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def load_table(query, params=()):
    conn = get_connection()
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df


def save_table(df, table, state_code, bridge_number):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(f"""
        DELETE FROM {table}
        WHERE state_code=? AND bridge_number=?
    """, (state_code, bridge_number))

    df.to_sql(table, conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

# ----------------------------
# UI
# ----------------------------
st.markdown("""
    <h1 style='
        text-align: center;
        color: #1f2937;   /* dark gray text */
        padding: 20px;
        font-weight: bold;
    '>
        SNBI Editor
    </h1>
""", unsafe_allow_html=True)



# ----------------------------
# State filter (no sidebar)
# ----------------------------
STATE_OPTIONS = {v: k for k, v in STATE_MAP.items()}

selected_state_name = st.selectbox(
    "Select State to Edit Bridges",
    options=["All States"] + list(STATE_OPTIONS.keys()),
    index=0
)

selected_state_code = (
    None if selected_state_name == "All States"
    else STATE_OPTIONS[selected_state_name]
)








# ----------------------------
# Select bridge
# ----------------------------
if selected_state_code is None:
    bridges_df = load_table("""
        SELECT state_code, bridge_number, bridge_name
        FROM bridges
        ORDER BY state_code, bridge_number
    """)
else:
    bridges_df = load_table("""
        SELECT state_code, bridge_number, bridge_name
        FROM bridges
        WHERE state_code = ?
        ORDER BY bridge_number
    """, (selected_state_code,))


if bridges_df.empty:
    st.warning("No bridges found.")
    st.stop()

selected = st.selectbox(
    "Select Bridge",
    bridges_df.itertuples(index=False),
    format_func=lambda x: f"{x.state_code}-{x.bridge_number} | {x.bridge_name}"
)

old_state = selected.state_code
old_bridge = selected.bridge_number

bridge = load_table("""
    SELECT * FROM bridges
    WHERE state_code=? AND bridge_number=?
""", (old_state, old_bridge)).iloc[0]

def get_table_schema(table):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    rows = cur.fetchall()
    conn.close()
    return rows
def render_bridge_form(row, schema):
    updated = {}

    for cid, name, col_type, notnull, dflt, pk in schema:
        value = row[name]

        if name in ("state_code", "bridge_number"):
            st.text_input(name, value=str(value), disabled=True)
            updated[name] = value
            continue

        if "INT" in col_type.upper():
            updated[name] = st.number_input(
                name,
                value=int(value) if value is not None else None,
                step=1
            )

        elif "REAL" in col_type.upper():
            updated[name] = st.number_input(
                name,
                value=float(value) if value is not None else None
            )

        else:
            updated[name] = st.text_input(
                name,
                value=value if value is not None else ""
            )

    return updated




# ----------------------------
# Edit main bridge table
# ----------------------------
bridge_schema = get_table_schema("bridges")
bridge_row = load_table("""
    SELECT * FROM bridges
    WHERE state_code=? AND bridge_number=?
""", (old_state, old_bridge)).iloc[0]

st.header("Main Bridge Table")

def render_bridge_form_compact(row, schema, ncols=2):
    updated = {}
    columns = st.columns(ncols)

    for i, (cid, name, col_type, *_ ) in enumerate(schema):
        col = columns[i % ncols]

        value = row[name]

        if name in ("state_code", "bridge_number"):
            col.text_input(name, value=str(value), disabled=True)
            updated[name] = value
            continue

        if "INT" in col_type.upper():
            updated[name] = col.number_input(
                name,
                value=int(value) if value is not None else 0,
                step=1
            )
        elif "REAL" in col_type.upper():
            updated[name] = col.number_input(
                name,
                value=float(value) if value is not None else 0.0
            )
        else:
            updated[name] = col.text_input(
                name,
                value=value if value is not None else ""
            )
    return updated
with st.form("bridge_form"):
    updated = render_bridge_form_compact(bridge_row, bridge_schema, ncols=4)
    submitted = st.form_submit_button("Save Main Bridge Data")



if submitted:
    conn = get_connection()
    cur = conn.cursor()

    try:
        columns = [
            c for c in updated.keys()
            if c not in ("state_code", "bridge_number")
        ]

        set_clause = ", ".join(f"{c}=?" for c in columns)
        values = [updated[c] for c in columns]
        values.extend([old_state, old_bridge])

        cur.execute(f"""
            UPDATE bridges
            SET {set_clause}
            WHERE state_code=? AND bridge_number=?
        """, values)

        conn.commit()
        st.success("Main bridge updated successfully")

    except Exception as e:
        conn.rollback()
        st.error(f"Update failed: {e}")

    finally:
        conn.close()



# ----------------------------
# Child tables editor
# ----------------------------







st.header("Related Tables")

tabs = st.tabs(CHILD_TABLES)

for tab, table in zip(tabs, CHILD_TABLES):
    with tab:
        df = load_table(
            f"SELECT * FROM {table} WHERE state_code=? AND bridge_number=?",
            (old_state, old_bridge)
        )

        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            key=table
        )

        if st.button(f"Save {table}", key=f"save_{table}"):
            try:
                save_table(edited_df, table, old_state, old_bridge)
                st.success(f"{table} saved successfully")
            except Exception as e:
                st.error(f"Failed to save {table}: {e}")




# Reverse mapping: sql_column -> SNBI key
REVERSE_MAPPING = {v: k for k, v in mapping.items()}
def row_to_snbi_dict(row: dict):
    """Convert a SQL row dict into SNBI-tagged dict"""
    return {
        REVERSE_MAPPING[col]: val
        for col, val in row.items()
        if col in REVERSE_MAPPING and val is not None
    }
def build_snbi_bridge_json(conn, state_code, bridge_number):
    cur = conn.cursor()

    # ----------------------------
    # Main bridge
    # ----------------------------
    cur.execute("""
        SELECT * FROM bridges
        WHERE state_code=? AND bridge_number=?
    """, (state_code, bridge_number))

    bridge_row = dict(zip(
        [d[0] for d in cur.description],
        cur.fetchone()
    ))

    bridge_json = row_to_snbi_dict(bridge_row)

    # ----------------------------
    # Features + Routes
    # ----------------------------
    cur.execute("""
        SELECT * FROM features
        WHERE state_code=? AND bridge_number=?
    """, (state_code, bridge_number))

    features = []
    for f in cur.fetchall():
        fdict = dict(zip([d[0] for d in cur.description], f))
        feature_json = row_to_snbi_dict(fdict)

        cur.execute("""
            SELECT * FROM routes
            WHERE state_code=? AND bridge_number=? AND feature_type=?
        """, (state_code, bridge_number, fdict["feature_type"]))


        routes = [
            row_to_snbi_dict(dict(zip([d[0] for d in cur.description], r)))
            for r in cur.fetchall()
        ]

        if routes:
            feature_json["Routes"] = routes

        features.append(feature_json)

    if features:
        bridge_json["Features"] = features

    # ----------------------------
    # Generic child tables
    # ----------------------------
    CHILD_TABLES = {
        "SpanSets": "span_sets",
        "SubstructureSets": "substructure_sets",
        "PostingEvaluations": "posting_evaluations",
        "PostingStatuses": "posting_statuses",
        "Inspections": "inspections",
        "Elements": "elements",
        "Works": "works",
    }

    for json_key, table in CHILD_TABLES.items():
        cur.execute(f"""
            SELECT * FROM {table}
            WHERE state_code=? AND bridge_number=?
        """, (state_code, bridge_number))

        rows = cur.fetchall()
        if rows:
            bridge_json[json_key] = [
                row_to_snbi_dict(dict(zip([d[0] for d in cur.description], r)))
                for r in rows
            ]

    return bridge_json
if st.button("Export SNBI to JSON"):
    snbi_json = build_snbi_bridge_json(
        conn,
        selected.state_code,
        selected.bridge_number
    )

    json_bytes = json.dumps(
        [snbi_json],   # SNBI expects an array
        indent=2
    ).encode("utf-8")

    save_path = os.path.join(
        save_dir,
        f"SNBI_{selected.state_code}_{selected.bridge_number}.json"
    )

    with open(save_path, "wb") as f:
        f.write(json_bytes)

    st.success(f"Saved locally to: {save_path}")



# Close the connection
conn.close()