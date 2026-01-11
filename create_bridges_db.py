import sqlite3

# Connect to the SQLite database (creates the file if it doesn't exist)
conn = sqlite3.connect('bridges1.db')
cursor = conn.cursor()

# SQL schema as a multi-line string
schema = """
-- Enable foreign key support (optional, but recommended)
PRAGMA foreign_keys = ON;

-- 1. Main Bridges table (PRIMARY)
CREATE TABLE bridges (
    state_code INTEGER NOT NULL CHECK(state_code BETWEEN 1 AND 99),
    bridge_number TEXT NOT NULL,
    bridge_name TEXT,
    previous_bridge_number TEXT,
    county_code INTEGER CHECK(county_code BETWEEN 1 AND 999),
    place_code INTEGER CHECK(place_code BETWEEN 0 AND 99999),
    highway_agency_district TEXT,
    latitude REAL CHECK(latitude BETWEEN -99.999999 AND 99.999999),
    longitude REAL CHECK(longitude BETWEEN -999.999999 AND 999.999999),
    border_bridge_number TEXT,
    border_bridge_state_or_country_code TEXT,
    border_bridge_inspection_responsibility TEXT,
    border_bridge_designated_lead_state TEXT,
    bridge_location TEXT,
    metropolitan_planning_organization TEXT,
    owner_ TEXT,
    maintenance_responsibility TEXT,
    federal_or_tribal_land_access TEXT,
    historical_significance TEXT,
    toll TEXT,
    emergency_evacuation_designation TEXT,
    bridge_railings TEXT,
    transitions TEXT,
    nbis_bridge_length REAL CHECK(nbis_bridge_length >= 0),
    total_bridge_length REAL CHECK(total_bridge_length >= 0),
    maximum_span_length REAL CHECK(maximum_span_length >= 0),
    minimum_span_length REAL CHECK(minimum_span_length >= 0),
    bridge_width_out_to_out REAL CHECK(bridge_width_out_to_out >= 0),
    bridge_width_curb_to_curb REAL CHECK(bridge_width_curb_to_curb >= 0),
    left_curb_or_sidewalk_width REAL CHECK(left_curb_or_sidewalk_width >= 0),
    right_curb_or_sidewalk_width REAL CHECK(right_curb_or_sidewalk_width >= 0),
    approach_roadway_width REAL CHECK(approach_roadway_width >= 0),
    bridge_median TEXT,
    skew INTEGER CHECK(skew BETWEEN 0 AND 99),
    curved_bridge TEXT,
    maximum_bridge_height INTEGER CHECK(maximum_bridge_height >= 0),
    sidehill_bridge TEXT,
    irregular_deck_area REAL CHECK(irregular_deck_area >= 0),
    calculated_deck_area REAL CHECK(calculated_deck_area >= 0),
    designed_load TEXT,
    designed_method TEXT,
    load_rating_date TEXT,
    load_rating_method TEXT,
    inventory_load_rating_factor REAL CHECK(inventory_load_rating_factor BETWEEN 0 AND 99.99),
    operating_load_rating_factor REAL CHECK(operating_load_rating_factor BETWEEN 0 AND 99.99),
    controlling_legal_load_rating_factor REAL CHECK(controlling_legal_load_rating_factor BETWEEN 0 AND 99.99),
    routine_permit_loads TEXT,
    nstm_inspection_required TEXT,
    fatigue_details TEXT,
    underwater_inspection_required TEXT,
    complex_feature TEXT,
    deck_condition_rating TEXT,
    superstructure_condition_rating TEXT,
    substructure_condition_rating TEXT,
    culvert_condition_rating TEXT,
    bridge_railings_condition_rating TEXT,
    bridge_railings_transitions_condition_rating TEXT,
    bridge_bearings_condition_rating TEXT,
    bridge_joints_condition_rating TEXT,
    channel_condition_rating TEXT,
    channel_protection_condition_rating TEXT,
    scour_condition_rating TEXT,
    bridge_condition_classification TEXT,
    lowest_condition_rating_code TEXT,
    nstm_inspection_condition TEXT,
    underwater_inspection_condition TEXT,
    approach_roadway_alignment TEXT,
    overtopping_likelihood TEXT,
    scour_vulnerability TEXT,
    scour_plan_of_action TEXT,
    seismic_vulnerability TEXT,
    year_built INTEGER CHECK(year_built BETWEEN 0 AND 9999),
    PRIMARY KEY (state_code, bridge_number)
);

-- 3. Features (2 - FEATURES)
CREATE TABLE features (
    state_code INTEGER NOT NULL,
    bridge_number TEXT NOT NULL,
    feature_type TEXT NOT NULL,
    feature_location TEXT,
    feature_name TEXT,
    functional_classification TEXT,
    urban_code TEXT,
    nhs_designation TEXT,
    national_highway_freight_network TEXT,
    strahnet_designation TEXT,
    lrs_route_id TEXT,
    lrs_mile_point REAL CHECK(lrs_mile_point BETWEEN 0 AND 99999.999),
    lanes_on_highway INTEGER CHECK(lanes_on_highway BETWEEN 0 AND 99),
    annual_average_daily_traffic INTEGER CHECK(annual_average_daily_traffic BETWEEN 0 AND 99999999),
    annual_average_daily_truck_traffic INTEGER CHECK(annual_average_daily_truck_traffic BETWEEN 0 AND 99999999),
    year_of_annual_average_daily_traffic INTEGER CHECK(year_of_annual_average_daily_traffic BETWEEN 0 AND 9999),
    highway_max_usable_vertical_clearance REAL CHECK(highway_max_usable_vertical_clearance >= 0),
    highway_min_vertical_clearance REAL CHECK(highway_min_vertical_clearance >= 0),
    highway_min_horizontal_clearance_left REAL CHECK(highway_min_horizontal_clearance_left >= 0),
    highway_min_horizontal_clearance_right REAL CHECK(highway_min_horizontal_clearance_right >= 0),
    highway_max_usable_surface_width REAL CHECK(highway_max_usable_surface_width >= 0),
    bypass_detour_length INTEGER CHECK(bypass_detour_length BETWEEN 0 AND 999),
    crossing_bridge_number TEXT,
    railroad_service_type TEXT,
    railroad_min_vertical_clearance REAL CHECK(railroad_min_vertical_clearance >= 0),
    railroad_min_horizontal_offset REAL CHECK(railroad_min_horizontal_offset >= 0),
    navigable_waterway TEXT,
    navigable_min_vertical_clearance REAL CHECK(navigable_min_vertical_clearance >= 0),
    movable_bridge_max_navigation_vertical_clearance REAL CHECK(movable_bridge_max_navigation_vertical_clearance >= 0),
    navigation_channel_width REAL CHECK(navigation_channel_width >= 0),
    navigation_channel_min_horizontal_clearance REAL CHECK(navigation_channel_min_horizontal_clearance >= 0),
    substructure_navigation_protection TEXT,
    FOREIGN KEY (state_code, bridge_number) REFERENCES bridges(state_code, bridge_number) ON DELETE CASCADE,
    PRIMARY KEY (state_code, bridge_number, feature_type)
);

-- 2. Routes (10 - ROUTES)
CREATE TABLE routes (
    feature_type TEXT NOT NULL,
    state_code INTEGER NOT NULL,
    bridge_number TEXT NOT NULL,
    route_designation TEXT NOT NULL,
    route_number TEXT,
    route_direction TEXT,
    route_type TEXT,
    service_type TEXT,
    FOREIGN KEY (state_code, bridge_number, feature_type) REFERENCES features (state_code, bridge_number, feature_type) ON DELETE CASCADE,
    PRIMARY KEY (state_code, bridge_number, feature_type, route_designation)
);

-- 4. Span Sets (3 - SPAN SETS)
CREATE TABLE span_sets (
    state_code INTEGER NOT NULL,
    bridge_number TEXT NOT NULL,
    span_configuration_designation TEXT NOT NULL,
    number_of_spans INTEGER CHECK(number_of_spans >= 0),
    number_of_beam_lines INTEGER CHECK(number_of_beam_lines >= 0),
    span_material TEXT,
    span_continuity TEXT,
    span_type TEXT,
    span_protective_system TEXT,
    deck_interaction TEXT,
    deck_material_and_type TEXT,
    wearing_surface TEXT,
    deck_protective_system TEXT,
    deck_reinforcing_protective_system TEXT,
    deck_stay_in_place_forms TEXT,
    FOREIGN KEY (state_code, bridge_number) REFERENCES bridges(state_code, bridge_number) ON DELETE CASCADE,
    PRIMARY KEY (state_code, bridge_number, span_configuration_designation)
);

-- 5. Substructure Sets (4 - SUBSTRUCTURE SETS)
CREATE TABLE substructure_sets (
    state_code INTEGER NOT NULL,
    bridge_number TEXT NOT NULL,
    substructure_configuration_designation TEXT NOT NULL,
    number_of_substructure_units INTEGER CHECK(number_of_substructure_units >= 0),
    substructure_material TEXT,
    substructure_type TEXT,
    substructure_protective_system TEXT,
    foundation_type TEXT,
    foundation_protective_system TEXT,
    FOREIGN KEY (state_code, bridge_number) REFERENCES bridges(state_code, bridge_number) ON DELETE CASCADE,
    PRIMARY KEY (state_code, bridge_number, substructure_configuration_designation)
);

-- 6. Elements (8 - ELEMENTS)
CREATE TABLE elements (
    state_code INTEGER NOT NULL,
    bridge_number TEXT NOT NULL,
    element_number TEXT NOT NULL,
    element_parent_number TEXT NOT NULL,
    element_total_quantity INTEGER CHECK(element_total_quantity >= 0),
    element_quantity_condition_state_one INTEGER CHECK(element_quantity_condition_state_one >= 0),
    element_quantity_condition_state_two INTEGER CHECK(element_quantity_condition_state_two >= 0),
    element_quantity_condition_state_three INTEGER CHECK(element_quantity_condition_state_three >= 0),
    element_quantity_condition_state_four INTEGER CHECK(element_quantity_condition_state_four >= 0),
    FOREIGN KEY (state_code, bridge_number) REFERENCES bridges(state_code, bridge_number) ON DELETE CASCADE,
    PRIMARY KEY (state_code, bridge_number, element_number, element_parent_number)
);

-- 7. Inspections (7 - INSPECTIONS)
CREATE TABLE inspections (
    state_code INTEGER NOT NULL,
    bridge_number TEXT NOT NULL,
    inspection_type TEXT NOT NULL,
    inspection_begin_date TEXT,  -- YYYYMMDD
    inspection_completion_date TEXT,
    nationally_certified_bridge_inspector TEXT,
    inspection_interval INTEGER CHECK(inspection_interval BETWEEN 0 AND 99),
    inspection_due_date TEXT,
    risk_based_inspection_interval_method TEXT,
    inspection_quality_control_date TEXT,
    inspection_quality_assurance_date TEXT,
    inspection_data_update_date TEXT,
    inspection_note TEXT,
    inspection_equipment TEXT,
    FOREIGN KEY (state_code, bridge_number) REFERENCES bridges(state_code, bridge_number) ON DELETE CASCADE,
    PRIMARY KEY (state_code, bridge_number, inspection_type, inspection_begin_date)
);

-- 8. Posting Evaluations (6 - POSTING EVALUATION)
CREATE TABLE posting_evaluations (
    state_code INTEGER NOT NULL,
    bridge_number TEXT NOT NULL,
    legal_load_configuration TEXT NOT NULL,
    legal_load_rating_factor REAL CHECK(legal_load_rating_factor BETWEEN 0 AND 99.99),
    posting_type TEXT,
    posting_value TEXT,
    FOREIGN KEY (state_code, bridge_number) REFERENCES bridges(state_code, bridge_number) ON DELETE CASCADE,
    PRIMARY KEY (state_code, bridge_number, legal_load_configuration)
);

-- 9. Posting Statuses (5 - POSTING STATUS)
CREATE TABLE posting_statuses (
    state_code INTEGER NOT NULL,
    bridge_number TEXT NOT NULL,
    posting_status_change_date TEXT NOT NULL,  -- YYYYMMDD
    load_posting_status TEXT,
    FOREIGN KEY (state_code, bridge_number) REFERENCES bridges(state_code, bridge_number) ON DELETE CASCADE,
    PRIMARY KEY (state_code, bridge_number, posting_status_change_date)
);

-- 10. Works (9 - WORK)
CREATE TABLE works (
    state_code INTEGER NOT NULL,
    bridge_number TEXT NOT NULL,
    year_work_performed INTEGER NOT NULL CHECK(year_work_performed BETWEEN 0 AND 9999),
    work_performed TEXT,
    FOREIGN KEY (state_code, bridge_number) REFERENCES bridges(state_code, bridge_number) ON DELETE CASCADE,
    PRIMARY KEY (state_code, bridge_number, year_work_performed)
);
"""

# Execute the schema
cursor.executescript(schema)

# Commit changes and close the connection
conn.commit()
conn.close()

print("SQLite database 'bridges.db' created successfully with the given schema.")