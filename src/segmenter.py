import re
from typing import List, Dict, Any, Optional

# Countries ranked roughly by business contact density in Apollo
COUNTRIES = [
    'United States', 'United Kingdom', 'Canada', 'India', 'Germany',
    'France', 'Australia', 'Brazil', 'Netherlands', 'Spain',
    'Italy', 'Sweden', 'Switzerland', 'Singapore', 'Japan',
    'Israel', 'Ireland', 'Belgium', 'Denmark', 'Norway',
    'Finland', 'Austria', 'Poland', 'Portugal', 'South Korea',
    'Mexico', 'Argentina', 'Colombia', 'Chile', 'United Arab Emirates',
    'South Africa', 'Nigeria', 'Kenya', 'Egypt', 'Saudi Arabia',
    'Turkey', 'Indonesia', 'Philippines', 'Thailand', 'Vietnam',
    'Malaysia', 'Taiwan', 'New Zealand', 'Czech Republic', 'Romania',
    'Hungary', 'Ukraine', 'Greece', 'Croatia', 'Bulgaria',
    'Luxembourg', 'Estonia', 'Latvia', 'Lithuania', 'Slovakia',
    'Slovenia', 'Serbia', 'Iceland', 'Malta', 'Cyprus',
    'Hong Kong', 'China', 'Russia', 'Pakistan', 'Bangladesh',
    'Sri Lanka', 'Nepal', 'Peru', 'Ecuador', 'Venezuela',
    'Costa Rica', 'Panama', 'Uruguay', 'Dominican Republic', 'Guatemala',
    'Puerto Rico', 'Jamaica', 'Trinidad and Tobago', 'Ghana', 'Tanzania',
    'Ethiopia', 'Morocco', 'Tunisia', 'Algeria', 'Cameroon',
    'Senegal', 'Ivory Coast', 'Uganda', 'Mozambique', 'Zambia',
    'Zimbabwe', 'Botswana', 'Namibia', 'Rwanda', 'Mauritius',
    'Qatar', 'Bahrain', 'Kuwait', 'Oman', 'Jordan', 'Lebanon',
]

# US States for sub-segmentation
US_STATES = [
    'California', 'New York', 'Texas', 'Florida', 'Illinois',
    'Massachusetts', 'Pennsylvania', 'Washington', 'Georgia', 'Virginia',
    'New Jersey', 'North Carolina', 'Ohio', 'Colorado', 'Arizona',
    'Michigan', 'Maryland', 'Minnesota', 'Oregon', 'Tennessee',
    'Indiana', 'Missouri', 'Wisconsin', 'Connecticut', 'Utah',
    'Nevada', 'South Carolina', 'Alabama', 'Kentucky', 'Louisiana',
    'Oklahoma', 'Iowa', 'Kansas', 'Arkansas', 'Mississippi',
    'Nebraska', 'New Mexico', 'Hawaii', 'Idaho', 'Montana',
    'Rhode Island', 'Delaware', 'New Hampshire', 'Maine', 'Vermont',
    'North Dakota', 'South Dakota', 'Wyoming', 'West Virginia', 'Alaska',
    'District of Columbia',
]

SENIORITIES = [
    'owner', 'founder', 'c_suite', 'partner', 'vp',
    'head', 'director', 'manager', 'senior', 'entry',
]

EMPLOYEE_RANGES = [
    '1,10', '11,20', '21,50', '51,100', '101,200',
    '201,500', '501,1000', '1001,2000', '2001,5000',
    '5001,10000', '10001,',
]

INDUSTRIES = [
    'information technology & services', 'computer software', 'marketing & advertising',
    'financial services', 'hospital & health care', 'internet',
    'management consulting', 'real estate', 'construction',
    'retail', 'automotive', 'education management',
    'banking', 'insurance', 'telecommunications',
    'accounting', 'staffing & recruiting', 'consumer goods',
    'oil & energy', 'food & beverages', 'logistics & supply chain',
    'mechanical or industrial engineering', 'pharmaceuticals',
    'legal services', 'government administration',
    'media production', 'architecture & planning', 'civil engineering',
    'entertainment', 'design', 'environmental services',
    'nonprofit organization management', 'leisure, travel & tourism',
    'mining & metals', 'textiles', 'aviation & aerospace',
    'biotechnology', 'medical devices', 'semiconductors',
    'renewables & environment', 'sports', 'arts and crafts',
    'e-learning', 'venture capital & private equity',
    'investment banking', 'consumer electronics', 'apparel & fashion',
    'chemicals', 'publishing', 'printing', 'cosmetics',
    'furniture', 'health, wellness and fitness', 'wine and spirits',
]

def _slug(string: str) -> str:
    s = re.sub(r'[^a-z0-9]+', '_', string.lower())
    return re.sub(r'(^_|_$)', '', s)

class SearchSegmenter:
    """
    Search Segmentation Engine
    Breaks down Apollo searches into thousands of non-overlapping segments
    to bypass the 2,500 record hard limit and collect millions of rows.
    """
    
    def __init__(self):
        self.segments = []

    def generate_segments(self, level: str = 'deep', filters: Optional[Dict] = None, include_us: bool = True, include_intl: bool = True) -> List[Dict[str, Any]]:
        self.segments = []
        base_filters = filters or {}
        
        # Check if user already provided locations
        custom_locations = base_filters.get('person_locations', [])
        
        if custom_locations:
            # If user provided locations, just segment by Seniority and Employee Ranges
            if level == 'light':
                f = dict(base_filters)
                self.segments.append({
                    'id': f"custom_{_slug(custom_locations[0])}",
                    'label': f"Custom / {custom_locations[0]}",
                    'filters': f
                })
            elif level == 'standard':
                for seniority in SENIORITIES:
                    f = dict(base_filters)
                    f['person_seniorities'] = [seniority]
                    self.segments.append({
                        'id': f"custom_{_slug(custom_locations[0])}_{seniority}",
                        'label': f"{custom_locations[0]} / {seniority}",
                        'filters': f
                    })
            elif level == 'deep':
                for seniority in SENIORITIES:
                    for emp_range in EMPLOYEE_RANGES:
                        f = dict(base_filters)
                        f['person_seniorities'] = [seniority]
                        f['organization_num_employees_ranges'] = [emp_range]
                        self.segments.append({
                            'id': f"custom_{_slug(custom_locations[0])}_{seniority}_emp{emp_range.replace(',', '-')}",
                            'label': f"{custom_locations[0]} / {seniority} / {emp_range} emp",
                            'filters': f
                        })
            return self.segments
            
        # Default behavior (global scrape) if no locations provided
        if level == 'light':
            countries = COUNTRIES if include_intl else ['United States']
            for country in countries:
                f = dict(base_filters)
                f['person_locations'] = [country]
                self.segments.append({
                    'id': f"country_{_slug(country)}",
                    'label': country,
                    'filters': f
                })
                
        elif level == 'standard':
            if include_us:
                for state in US_STATES:
                    for seniority in SENIORITIES:
                        f = dict(base_filters)
                        f['person_locations'] = [f"{state}, United States"]
                        f['person_seniorities'] = [seniority]
                        self.segments.append({
                            'id': f"us_{_slug(state)}_{seniority}",
                            'label': f"US / {state} / {seniority}",
                            'filters': f
                        })
            if include_intl:
                for country in [c for c in COUNTRIES if c != 'United States']:
                    for seniority in SENIORITIES:
                        f = dict(base_filters)
                        f['person_locations'] = [country]
                        f['person_seniorities'] = [seniority]
                        self.segments.append({
                            'id': f"intl_{_slug(country)}_{seniority}",
                            'label': f"{country} / {seniority}",
                            'filters': f
                        })
                        
        elif level == 'deep':
            if include_us:
                for state in US_STATES:
                    for seniority in SENIORITIES:
                        for emp_range in EMPLOYEE_RANGES:
                            f = dict(base_filters)
                            f['person_locations'] = [f"{state}, United States"]
                            f['person_seniorities'] = [seniority]
                            f['organization_num_employees_ranges'] = [emp_range]
                            self.segments.append({
                                'id': f"us_{_slug(state)}_{seniority}_emp{emp_range.replace(',', '-')}",
                                'label': f"US / {state} / {seniority} / {emp_range} emp",
                                'filters': f
                            })
            if include_intl:
                for country in [c for c in COUNTRIES if c != 'United States']:
                    for seniority in SENIORITIES:
                        for emp_range in EMPLOYEE_RANGES:
                            f = dict(base_filters)
                            f['person_locations'] = [country]
                            f['person_seniorities'] = [seniority]
                            f['organization_num_employees_ranges'] = [emp_range]
                            self.segments.append({
                                'id': f"intl_{_slug(country)}_{seniority}_emp{emp_range.replace(',', '-')}",
                                'label': f"{country} / {seniority} / {emp_range} emp",
                                'filters': f
                            })
                            
        return self.segments

    def split_segment(self, segment: Dict) -> List[Dict]:
        filters = segment.get('filters', {})
        sub_segments = []
        
        emp_ranges = filters.get('organization_num_employees_ranges', [])
        if not emp_ranges:
            for emp_range in EMPLOYEE_RANGES:
                f = dict(filters)
                f['organization_num_employees_ranges'] = [emp_range]
                sub_segments.append({
                    'id': f"{segment['id']}_emp{emp_range.replace(',', '-')}",
                    'label': f"{segment['label']} / {emp_range} emp",
                    'filters': f
                })
            return sub_segments
            
        industries = filters.get('organization_industries', [])
        if not industries:
            for industry in INDUSTRIES:
                f = dict(filters)
                f['organization_industries'] = [industry]
                sub_segments.append({
                    'id': f"{segment['id']}_ind_{_slug(industry)[:20]}",
                    'label': f"{segment['label']} / {industry}",
                    'filters': f
                })
            return sub_segments
            
        return [segment]
