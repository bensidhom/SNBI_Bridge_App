import json
import sqlite3

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

# Connect to the database
conn = sqlite3.connect('bridges4.db')
cursor = conn.cursor()

# Load JSON data
with open('nj_bridges_converted.json', 'r') as f:
    data = json.load(f)

for bridge_data in data:
    state_code = bridge_data.get('BL01')
    bridge_number = bridge_data.get('BID01')
    
    # Insert into bridges
    bridge_insert = {}
    for key, value in bridge_data.items():
        if key in mapping and key not in ['Features', 'SpanSets', 'SubstructureSets', 'PostingEvaluations', 'PostingStatuses', 'Inspections', 'Elements', 'Works']:
            col = mapping[key]
            bridge_insert[col] = value
    if bridge_insert:
        columns = ', '.join(bridge_insert.keys())
        placeholders = ', '.join(['?'] * len(bridge_insert))
        values = list(bridge_insert.values())
        cursor.execute(f"INSERT OR IGNORE INTO bridges ({columns}) VALUES ({placeholders})", values)
    
    # Insert into features and routes
    features = bridge_data.get('Features', [])
    for feat in features:
        feat_insert = {'state_code': state_code, 'bridge_number': bridge_number}
        for k, v in feat.items():
            if k in mapping and k != 'Routes':
                col = mapping[k]
                feat_insert[col] = v
        if feat_insert:
            columns = ', '.join(feat_insert.keys())
            placeholders = ', '.join(['?'] * len(feat_insert))
            values = list(feat_insert.values())
            cursor.execute(f"INSERT OR IGNORE INTO features ({columns}) VALUES ({placeholders})", values)
        
        # Routes
        routes = feat.get('Routes', [])
        for route in routes:
            route_insert = {'state_code': state_code, 'bridge_number': bridge_number, 'feature_type': feat.get('BF01')}
            for rk, rv in route.items():
                if rk in mapping:
                    col = mapping[rk]
                    route_insert[col] = rv
            if route_insert:
                columns = ', '.join(route_insert.keys())
                placeholders = ', '.join(['?'] * len(route_insert))
                values = list(route_insert.values())
                cursor.execute(f"INSERT OR IGNORE INTO routes ({columns}) VALUES ({placeholders})", values)
    
    # Insert into span_sets
    span_sets = bridge_data.get('SpanSets', [])
    for span in span_sets:
        span_insert = {'state_code': state_code, 'bridge_number': bridge_number}
        for k, v in span.items():
            if k in mapping:
                col = mapping[k]
                span_insert[col] = v
        if span_insert:
            columns = ', '.join(span_insert.keys())
            placeholders = ', '.join(['?'] * len(span_insert))
            values = list(span_insert.values())
            cursor.execute(f"INSERT OR IGNORE INTO span_sets ({columns}) VALUES ({placeholders})", values)
    
    # Insert into substructure_sets
    sub_sets = bridge_data.get('SubstructureSets', [])
    for sub in sub_sets:
        sub_insert = {'state_code': state_code, 'bridge_number': bridge_number}
        for k, v in sub.items():
            if k in mapping:
                col = mapping[k]
                sub_insert[col] = v
        if sub_insert:
            columns = ', '.join(sub_insert.keys())
            placeholders = ', '.join(['?'] * len(sub_insert))
            values = list(sub_insert.values())
            cursor.execute(f"INSERT OR IGNORE INTO substructure_sets ({columns}) VALUES ({placeholders})", values)
    
    # Insert into posting_evaluations
    post_evals = bridge_data.get('PostingEvaluations', [])
    for pe in post_evals:
        pe_insert = {'state_code': state_code, 'bridge_number': bridge_number}
        for k, v in pe.items():
            if k in mapping:
                col = mapping[k]
                pe_insert[col] = v
        if pe_insert:
            columns = ', '.join(pe_insert.keys())
            placeholders = ', '.join(['?'] * len(pe_insert))
            values = list(pe_insert.values())
            cursor.execute(f"INSERT OR IGNORE INTO posting_evaluations ({columns}) VALUES ({placeholders})", values)
    
    # Insert into posting_statuses
    post_status = bridge_data.get('PostingStatuses', [])
    for ps in post_status:
        ps_insert = {'state_code': state_code, 'bridge_number': bridge_number}
        for k, v in ps.items():
            if k in mapping:
                col = mapping[k]
                ps_insert[col] = v
        if ps_insert:
            columns = ', '.join(ps_insert.keys())
            placeholders = ', '.join(['?'] * len(ps_insert))
            values = list(ps_insert.values())
            cursor.execute(f"INSERT OR IGNORE INTO posting_statuses ({columns}) VALUES ({placeholders})", values)
    
    # Insert into inspections
    insps = bridge_data.get('Inspections', [])
    for insp in insps:
        insp_insert = {'state_code': state_code, 'bridge_number': bridge_number}
        for k, v in insp.items():
            if k in mapping:
                col = mapping[k]
                insp_insert[col] = v
        if insp_insert:
            columns = ', '.join(insp_insert.keys())
            placeholders = ', '.join(['?'] * len(insp_insert))
            values = list(insp_insert.values())
            cursor.execute(f"INSERT OR IGNORE INTO inspections ({columns}) VALUES ({placeholders})", values)
    
    # Insert into elements
    elements = bridge_data.get('Elements', [])
    for elem in elements:
        elem_insert = {'state_code': state_code, 'bridge_number': bridge_number}
        for k, v in elem.items():
            if k in mapping:
                col = mapping[k]
                elem_insert[col] = v
        # Handle missing element_parent_number
        if 'element_parent_number' not in elem_insert:
            elem_insert['element_parent_number'] = '0'  # Assuming '0' for no parent
        if elem_insert:
            columns = ', '.join(elem_insert.keys())
            placeholders = ', '.join(['?'] * len(elem_insert))
            values = list(elem_insert.values())
            cursor.execute(f"INSERT OR IGNORE INTO elements ({columns}) VALUES ({placeholders})", values)
    
    # Insert into works
    works = bridge_data.get('Works', [])
    for work in works:
        work_insert = {'state_code': state_code, 'bridge_number': bridge_number}
        for k, v in work.items():
            if k in mapping:
                col = mapping[k]
                work_insert[col] = v
        if work_insert:
            columns = ', '.join(work_insert.keys())
            placeholders = ', '.join(['?'] * len(work_insert))
            values = list(work_insert.values())
            cursor.execute(f"INSERT OR IGNORE INTO works ({columns}) VALUES ({placeholders})", values)

# Commit and close
conn.commit()
conn.close()

print("Data inserted into the database successfully.")