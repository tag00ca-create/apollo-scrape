"""
Data parsing and transformation for Apollo.io scraper.

Two modes of operation:
1. API mode (PRIMARY): Flattens structured JSON from Apollo's internal API responses
2. HTML mode (FALLBACK): Parses rendered HTML for non-API pages

The API mode produces the same 21-column output as the local exporter.
"""

from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import re
import json
from datetime import datetime
from src.utils import log_message


# ═══════════════════════════════════════════════════════════════════════════════
# API MODE — Primary data extraction from Apollo's internal API responses
# ═══════════════════════════════════════════════════════════════════════════════

def flatten_person(person: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a raw person object from Apollo's API into a flat dictionary
    with all 21 standard output columns.
    
    Args:
        person: Raw person dict from /api/v1/mixed_people/search response
    
    Returns:
        Flat dictionary with standardized column names
    """
    org = person.get('organization') or {}
    
    # Extract phone number (first available)
    phone = ''
    phone_numbers = person.get('phone_numbers') or []
    if phone_numbers and isinstance(phone_numbers, list):
        first_phone = phone_numbers[0] if phone_numbers else {}
        if isinstance(first_phone, dict):
            phone = first_phone.get('sanitized_number') or first_phone.get('number') or ''
        elif isinstance(first_phone, str):
            phone = first_phone
    
    # Extract all phone numbers
    all_phones = []
    for pn in phone_numbers:
        if isinstance(pn, dict):
            num = pn.get('sanitized_number') or pn.get('number') or ''
            if num:
                all_phones.append(num)
        elif isinstance(pn, str) and pn:
            all_phones.append(pn)
    
    # Build flat record
    record = {
        'id': person.get('id') or '',
        'first_name': person.get('first_name') or '',
        'last_name': person.get('last_name') or '',
        'name': person.get('name') or f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
        'title': person.get('title') or '',
        'headline': person.get('headline') or '',
        'seniority': person.get('seniority') or '',
        'email': person.get('email') or '',
        'email_status': person.get('email_status') or '',
        'phone': phone,
        'all_phones': ', '.join(all_phones) if all_phones else '',
        'linkedin_url': person.get('linkedin_url') or '',
        'city': person.get('city') or '',
        'state': person.get('state') or '',
        'country': person.get('country') or '',
        'company_name': org.get('name') or person.get('organization_name') or '',
        'company_domain': org.get('primary_domain') or org.get('website_url') or '',
        'company_industry': org.get('industry') or '',
        'company_size': org.get('estimated_num_employees') or '',
        'company_linkedin': org.get('linkedin_url') or '',
        'company_founded_year': org.get('founded_year') or '',
        'departments': ', '.join(person.get('departments') or []),
        'subdepartments': ', '.join(person.get('subdepartments') or []),
        'scraped_at': datetime.now().isoformat(),
    }
    
    return record


def flatten_organization(org: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a raw organization object from Apollo's API into a flat dictionary.
    
    Args:
        org: Raw organization dict from API response
    
    Returns:
        Flat dictionary with standardized column names
    """
    return {
        'id': org.get('id') or '',
        'name': org.get('name') or '',
        'domain': org.get('primary_domain') or org.get('website_url') or '',
        'industry': org.get('industry') or '',
        'estimated_employees': org.get('estimated_num_employees') or '',
        'founded_year': org.get('founded_year') or '',
        'city': org.get('city') or '',
        'state': org.get('state') or '',
        'country': org.get('country') or '',
        'linkedin_url': org.get('linkedin_url') or '',
        'twitter_url': org.get('twitter_url') or '',
        'facebook_url': org.get('facebook_url') or '',
        'phone': org.get('phone') or '',
        'short_description': org.get('short_description') or '',
        'annual_revenue': org.get('annual_revenue') or '',
        'total_funding': org.get('total_funding') or '',
        'keywords': ', '.join(org.get('keywords') or []),
        'scraped_at': datetime.now().isoformat(),
    }


def flatten_api_response(api_response: Dict[str, Any], search_type: str = 'people') -> List[Dict[str, Any]]:
    """
    Flatten an entire API search response into a list of flat records.
    
    Args:
        api_response: Full API response dict
        search_type: 'people' or 'organizations'
    
    Returns:
        List of flat record dicts ready for Apify dataset
    """
    records = []
    
    if search_type == 'people':
        people = api_response.get('people') or api_response.get('contacts') or []
        for person in people:
            try:
                flat = flatten_person(person)
                if flat.get('name') or flat.get('first_name'):
                    records.append(flat)
            except Exception as e:
                log_message(f"Error flattening person: {e}", 'DEBUG')
                continue
    else:
        organizations = api_response.get('organizations') or api_response.get('accounts') or []
        for org in organizations:
            try:
                flat = flatten_organization(org)
                if flat.get('name'):
                    records.append(flat)
            except Exception as e:
                log_message(f"Error flattening organization: {e}", 'DEBUG')
                continue
    
    return records


def get_pagination_info(api_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract pagination metadata from API response.
    
    Returns:
        Dict with total_entries, page, per_page, total_pages
    """
    pagination = api_response.get('pagination') or {}
    total = pagination.get('total_entries') or api_response.get('num_fetch_result') or 0
    page = pagination.get('page') or api_response.get('page') or 1
    per_page = pagination.get('per_page') or 25
    
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    
    return {
        'total_entries': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# URL PARSING — Extract search filters from Apollo URLs
# ═══════════════════════════════════════════════════════════════════════════════

def parse_apollo_search_url(url: str) -> Dict[str, Any]:
    """
    Parse an Apollo search URL into API filter parameters.
    
    Handles URL formats like:
        https://app.apollo.io/#/people?personLocations[]=Egypt&personTitles[]=CEO&page=1
    
    Args:
        url: Full Apollo search URL
    
    Returns:
        Dict with 'filters' (for API body), 'page' (starting page), and 'search_type'
    """
    from urllib.parse import urlparse, parse_qs, unquote
    
    # Apollo uses hash routing: everything after # is the real path
    # Extract the fragment part
    if '#' in url:
        fragment = url.split('#', 1)[1]
    else:
        fragment = url.replace('https://app.apollo.io', '')
    
    # Determine search type
    search_type = 'people'
    if '/companies' in fragment or '/accounts' in fragment:
        search_type = 'organizations'
    
    # Parse query string from fragment
    if '?' in fragment:
        query_string = fragment.split('?', 1)[1]
    else:
        query_string = ''
    
    params = parse_qs(query_string, keep_blank_values=True)
    
    # Map Apollo URL params to API body params
    # Apollo URL uses camelCase with [], API uses snake_case
    param_mapping = {
        'personLocations[]': 'person_locations',
        'personTitles[]': 'person_titles',
        'personSeniorities[]': 'person_seniorities',
        'organizationIndustries[]': 'organization_industries',
        'organizationNumEmployeesRanges[]': 'organization_num_employees_ranges',
        'qKeywords': 'q_keywords',
        'personDepartments[]': 'person_departments',
        'contactEmailStatus[]': 'contact_email_status',
        'organizationLocations[]': 'organization_locations',
        'personNames[]': 'person_names',
        'revenue_range[]': 'revenue_range',
    }
    
    filters = {}
    
    for url_key, api_key in param_mapping.items():
        if url_key in params:
            values = [unquote(v) for v in params[url_key] if v]
            if values:
                filters[api_key] = values
    
    # Handle single-value params
    if 'qKeywords' in params:
        filters['q_keywords'] = params['qKeywords'][0]
    
    # Extract page number
    page = 1
    if 'page' in params:
        try:
            page = int(params['page'][0])
        except (ValueError, IndexError):
            page = 1
    
    log_message(f"📋 Parsed URL filters: {json.dumps(filters, indent=2)}", 'DEBUG')
    log_message(f"📋 Search type: {search_type}, Starting page: {page}", 'INFO')
    
    return {
        'filters': filters,
        'page': page,
        'search_type': search_type,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE TYPE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def detect_page_type(url: str = '', html: str = '') -> str:
    """
    Detect the type of Apollo page from URL and/or HTML content.
    
    Now primarily uses URL-based detection (more reliable for SPA).
    
    Args:
        url: The page URL
        html: HTML content (fallback)
    
    Returns:
        Page type: 'people_search', 'company_search', 'contact_profile', 
                   'company_profile', or 'unknown'
    """
    url_lower = url.lower()
    
    # URL-based detection (primary — works for SPA)
    if '#/people' in url_lower or '/people?' in url_lower:
        return 'people_search'
    elif '#/companies' in url_lower or '/companies?' in url_lower or '#/accounts' in url_lower:
        return 'company_search'
    elif '/contacts/' in url_lower or '/people/' in url_lower:
        return 'contact_profile'
    elif '/companies/' in url_lower or '/accounts/' in url_lower:
        return 'company_profile'
    
    # HTML fallback for unknown URLs
    if html:
        soup = BeautifulSoup(html, 'lxml')
        if soup.find('div', class_=re.compile(r'.*search.*results.*', re.I)):
            return 'people_search'
        elif soup.find('div', class_=re.compile(r'.*person.*profile.*', re.I)):
            return 'contact_profile'
        elif soup.find('div', class_=re.compile(r'.*company.*profile.*', re.I)):
            return 'company_profile'
    
    return 'unknown'


# ═══════════════════════════════════════════════════════════════════════════════
# HTML MODE (FALLBACK) — Original HTML-based parsing, kept for non-API pages
# ═══════════════════════════════════════════════════════════════════════════════

def parse_search_results(html: str) -> List[Dict[str, Any]]:
    """Parse Apollo search results from HTML (fallback only)."""
    soup = BeautifulSoup(html, 'lxml')
    results = []
    
    result_items = (
        soup.find_all('tr', class_=re.compile(r'.*person.*row.*', re.I)) or
        soup.find_all('div', class_=re.compile(r'.*search.*result.*item.*', re.I)) or
        soup.find_all('div', {'data-cy': re.compile(r'.*person.*')})
    )
    
    log_message(f"Found {len(result_items)} result items on page (HTML fallback)", 'DEBUG')
    
    for item in result_items:
        try:
            result = extract_contact_from_element(item)
            if result:
                results.append(result)
        except Exception as e:
            log_message(f"Error parsing result item: {e}", 'DEBUG')
            continue
    
    return results


def extract_contact_from_element(element) -> Optional[Dict[str, Any]]:
    """Extract contact from HTML element (fallback)."""
    contact = {
        'type': 'contact',
        'scraped_at': datetime.now().isoformat()
    }
    
    name_elem = (
        element.find('a', class_=re.compile(r'.*name.*', re.I)) or
        element.find('div', class_=re.compile(r'.*name.*', re.I)) or
        element.find('span', class_=re.compile(r'.*name.*', re.I))
    )
    contact['name'] = clean_text(name_elem.get_text()) if name_elem else ''
    
    title_elem = (
        element.find('div', class_=re.compile(r'.*title.*', re.I)) or
        element.find('span', class_=re.compile(r'.*title.*', re.I))
    )
    contact['title'] = clean_text(title_elem.get_text()) if title_elem else ''
    
    company_elem = (
        element.find('a', class_=re.compile(r'.*company.*', re.I)) or
        element.find('div', class_=re.compile(r'.*company.*', re.I))
    )
    contact['company_name'] = clean_text(company_elem.get_text()) if company_elem else ''
    
    email_elem = (
        element.find('a', href=re.compile(r'^mailto:')) or
        element.find('span', class_=re.compile(r'.*email.*', re.I))
    )
    if email_elem:
        if email_elem.get('href'):
            contact['email'] = email_elem.get('href').replace('mailto:', '')
        else:
            email_text = email_elem.get_text()
            contact['email'] = clean_text(email_text) if '@' in email_text else ''
    else:
        contact['email'] = ''
    
    return contact if contact['name'] else None


def parse_contact_profile(html: str) -> Dict[str, Any]:
    """Parse contact profile page (fallback)."""
    soup = BeautifulSoup(html, 'lxml')
    profile = {
        'type': 'contact_profile',
        'scraped_at': datetime.now().isoformat()
    }
    
    name_elem = soup.find('h1')
    profile['name'] = clean_text(name_elem.get_text()) if name_elem else ''
    
    title_elem = soup.find('div', class_=re.compile(r'.*title.*', re.I))
    profile['title'] = clean_text(title_elem.get_text()) if title_elem else ''
    
    company_elem = soup.find('a', href=re.compile(r'/companies/'))
    if company_elem:
        profile['company_name'] = clean_text(company_elem.get_text())
    else:
        profile['company_name'] = ''
    
    return profile


def parse_company_profile(html: str) -> Dict[str, Any]:
    """Parse company profile page (fallback)."""
    soup = BeautifulSoup(html, 'lxml')
    company = {
        'type': 'company_profile',
        'scraped_at': datetime.now().isoformat()
    }
    
    name_elem = soup.find('h1')
    company['name'] = clean_text(name_elem.get_text()) if name_elem else ''
    
    return company


def clean_text(text: str) -> str:
    """Clean extracted text."""
    if not text:
        return ''
    text = ' '.join(text.split())
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    return text.strip()
