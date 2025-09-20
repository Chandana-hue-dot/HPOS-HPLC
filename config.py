# Configuration file for Project Chandana Dashboard

# Data Source URLs
DATA_SOURCES = {
    'hpos_data_url': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTVZqlJ7YBLKbPSWwYTA5tAr401wUIBpp7ALPvEOKch91uxdvTevpvWs1FuQ1hQKB84RsZyAFsJYRRr/pub?gid=1058968279&single=true&output=csv',
    'hplc_data_path':'https://docs.google.com/spreadsheets/d/e/2PACX-1vTAHLMLCH4GO0WGXgUXO7hz3Lvc66MIgMffh3JnqcO3QSGX2Pk_YmbCRuD2welz7-aDhINSixl9g-nN/pubhtml?gid=43184154&single=true'# Local file path as in original code
}

# HPOS Analysis Thresholds
HPOS_THRESHOLDS = {
    'low': 0.38,
    'high': 0.42
}

# Project Targets
PROJECT_TARGETS = {
    'total_hplc_tests': 1000,  # Adjust based on your actual target
    'completion_deadline': '2025-12-31'
}

# Theme Configuration (Anthropic-inspired)
THEME = {
    'primary_color': '#4F46E5',
    'secondary_color': '#667eea',
    'background_color': '#ffffff',
    'text_color': '#1f2937',
    'accent_color': '#764ba2'
}

# Dashboard Settings
DASHBOARD_SETTINGS = {
    'page_title': 'Project Chandana Dashboard',
    'page_icon': '🧬',
    'layout': 'wide',
    'cache_ttl': 3600,  # Cache timeout in seconds (1 hour)
    'auto_refresh_interval': 300  # Auto refresh every 5 minutes
}

# Column mappings for data processing
COLUMN_MAPPINGS = {
    'hplc_required_columns': [
        'SL No.',
        'Sickle Id',
        'Age',
        'Gender',
        'District',
        'Pathology stated HPLC RESULT',
        'Lab_HPOS_Test'
    ],
    'hpos_required_columns': [
        'deviceRatio'
    ]
}

# Gender standardization mapping
GENDER_MAPPING = {
    'M': 'Male',
    'F': 'Female',
    'MALE': 'Male',
    'FEMALE': 'Female',
    'NA': 'Unknown',
    '': 'Unknown',
    None: 'Unknown'
}
