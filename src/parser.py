"""
HTML parsing functions for extracting data from Apollo.io pages.
Handles different page types: search results, company profiles, contact profiles.
"""

from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import re
import json
from datetime import datetime
from src.utils import log_message


def parse_search_results(html: str) -> List[Dict[str, Any]]:
    """
    Parse Apollo search results page to extract lead/company data.
    
    Args:
        html: HTML content of search results page
    
    Returns:
        List of dictionaries containing extracted data
    """
    soup = BeautifulSoup(html, 'lxml')
    results = []
    
    # Apollo uses various class names - we need to be flexible
    # Try multiple selectors as Apollo's DOM changes frequently
    result_items = (
        soup.find_all('tr', class_=re.compile(r'.*person.*row.*', re.I)) or
        soup.find_all('div', class_=re.compile(r'.*search.*result.*item.*', re.I)) or
        soup.find_all('div', {'data-cy': re.compile(r'.*person.*')})
    )
    
    log_message(f"Found {len(result_items)} result items on page", 'DEBUG')
    
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
    """
    Extract contact information from a single search result element.
    
    Args:
        element: BeautifulSoup element containing contact data
    
    Returns:
        Dictionary with contact information
    """
    contact = {
        'type': 'contact',
        'scraped_at': datetime.now().isoformat()
    }
    
    # Extract name - try multiple selectors
    name_elem = (
        element.find('a', class_=re.compile(r'.*name.*', re.I)) or
        element.find('div', class_=re.compile(r'.*name.*', re.I)) or
        element.find('span', class_=re.compile(r'.*name.*', re.I))
    )
    contact['name'] = clean_text(name_elem.get_text()) if name_elem else ''
    
    # Extract title/position
    title_elem = (
        element.find('div', class_=re.compile(r'.*title.*', re.I)) or
        element.find('span', class_=re.compile(r'.*title.*', re.I))
    )
    contact['title'] = clean_text(title_elem.get_text()) if title_elem else ''
    
    # Extract company
    company_elem = (
        element.find('a', class_=re.compile(r'.*company.*', re.I)) or
        element.find('div', class_=re.compile(r'.*company.*', re.I))
    )
    contact['company'] = clean_text(company_elem.get_text()) if company_elem else ''
    
    # Extract location
    location_elem = element.find(text=re.compile(r'.*,.*'))  # Often contains commas
    if location_elem and isinstance(location_elem, str):
        contact['location'] = clean_text(location_elem)
    else:
        location_elem = element.find('div', class_=re.compile(r'.*location.*', re.I))
        contact['location'] = clean_text(location_elem.get_text()) if location_elem else ''
    
    # Extract email - may be hidden/locked on free accounts
    email_elem = (
        element.find('a', href=re.compile(r'^mailto:')) or
        element.find('span', class_=re.compile(r'.*email.*', re.I))
    )
    if email_elem:
        if email_elem.get('href'):
            contact['email'] = email_elem.get('href').replace('mailto:', '')
        else:
            email_text = email_elem.get_text()
            if '@' in email_text:
                contact['email'] = clean_text(email_text)
            else:
                contact['email'] = 'locked'  # Email hidden by free account
    else:
        contact['email'] = None
    
    # Extract phone
    phone_elem = element.find(text=re.compile(r'[\+\(\)0-9\-\s]{10,}'))
    contact['phone'] = clean_text(str(phone_elem)) if phone_elem else None
    
    # Extract LinkedIn URL
    linkedin_elem = element.find('a', href=re.compile(r'linkedin\.com'))
    contact['linkedin_url'] = linkedin_elem.get('href') if linkedin_elem else None
    
    # Extract profile URL
    profile_link = element.find('a', href=re.compile(r'/people/'))
    contact['profile_url'] = 'https://app.apollo.io' + profile_link.get('href') if profile_link else None
    
    return contact if contact['name'] else None


def parse_contact_profile(html: str) -> Dict[str, Any]:
    """
    Parse individual contact profile page for detailed information.
    
    Args:
        html: HTML content of contact profile page
    
    Returns:
        Dictionary with detailed contact information
    """
    soup = BeautifulSoup(html, 'lxml')
    
    profile = {
        'type': 'contact_profile',
        'scraped_at': datetime.now().isoformat()
    }
    
    # Extract name from header
    name_elem = soup.find('h1') or soup.find('div', class_=re.compile(r'.*name.*header.*', re.I))
    profile['name'] = clean_text(name_elem.get_text()) if name_elem else ''
    
    # Extract title
    title_elem = soup.find('div', class_=re.compile(r'.*title.*', re.I))
    profile['title'] = clean_text(title_elem.get_text()) if title_elem else ''
    
    # Extract company information
    company_elem = soup.find('a', href=re.compile(r'/companies/'))
    if company_elem:
        profile['company'] = clean_text(company_elem.get_text())
        profile['company_url'] = 'https://app.apollo.io' + company_elem.get('href')
    else:
        profile['company'] = ''
        profile['company_url'] = None
    
    # Extract location
    location_elem = soup.find(text=re.compile(r'.*\w+,\s*\w+.*'))
    profile['location'] = clean_text(str(location_elem)) if location_elem else ''
    
    # Extract emails - may be multiple
    profile['emails'] = extract_emails(soup)
    
    # Extract phones - may be multiple
    profile['phones'] = extract_phones(soup)
    
    # Extract social links
    profile['social_links'] = extract_social_links(soup)
    
    # Extract bio/summary
    bio_elem = soup.find('div', class_=re.compile(r'.*bio.*|.*summary.*', re.I))
    profile['bio'] = clean_text(bio_elem.get_text()) if bio_elem else ''
    
    # Extract experience/work history
    profile['experience'] = extract_experience(soup)
    
    # Extract education
    profile['education'] = extract_education(soup)
    
    # Extract technologies/skills
    profile['technologies'] = extract_technologies(soup)
    
    return profile


def parse_company_profile(html: str) -> Dict[str, Any]:
    """
    Parse company profile page for detailed company information.
    
    Args:
        html: HTML content of company profile page
    
    Returns:
        Dictionary with company information
    """
    soup = BeautifulSoup(html, 'lxml')
    
    company = {
        'type': 'company_profile',
        'scraped_at': datetime.now().isoformat()
    }
    
    # Extract company name
    name_elem = soup.find('h1') or soup.find('div', class_=re.compile(r'.*company.*name.*', re.I))
    company['name'] = clean_text(name_elem.get_text()) if name_elem else ''
    
    # Extract website
    website_elem = soup.find('a', class_=re.compile(r'.*website.*', re.I))
    company['website'] = website_elem.get('href') if website_elem else None
    
    # Extract industry
    industry_elem = soup.find(text=re.compile(r'Industry', re.I))
    if industry_elem:
        industry_value = industry_elem.find_next('div') or industry_elem.find_next('span')
        company['industry'] = clean_text(industry_value.get_text()) if industry_value else ''
    else:
        company['industry'] = ''
    
    # Extract employee count
    employee_elem = soup.find(text=re.compile(r'Employees|Employee Count', re.I))
    if employee_elem:
        employee_value = employee_elem.find_next('div') or employee_elem.find_next('span')
        company['employee_count'] = clean_text(employee_value.get_text()) if employee_value else ''
    else:
        company['employee_count'] = ''
    
    # Extract revenue
    revenue_elem = soup.find(text=re.compile(r'Revenue', re.I))
    if revenue_elem:
        revenue_value = revenue_elem.find_next('div') or revenue_elem.find_next('span')
        company['revenue'] = clean_text(revenue_value.get_text()) if revenue_value else ''
    else:
        company['revenue'] = ''
    
    # Extract location/headquarters
    location_elem = soup.find(text=re.compile(r'Headquarters|Location', re.I))
    if location_elem:
        location_value = location_elem.find_next('div') or location_elem.find_next('span')
        company['headquarters'] = clean_text(location_value.get_text()) if location_value else ''
    else:
        company['headquarters'] = ''
    
    # Extract founded year
    founded_elem = soup.find(text=re.compile(r'Founded', re.I))
    if founded_elem:
        founded_value = founded_elem.find_next('div') or founded_elem.find_next('span')
        company['founded'] = clean_text(founded_value.get_text()) if founded_value else ''
    else:
        company['founded'] = ''
    
    # Extract description
    desc_elem = soup.find('div', class_=re.compile(r'.*description.*', re.I))
    company['description'] = clean_text(desc_elem.get_text()) if desc_elem else ''
    
    # Extract technologies
    company['technologies'] = extract_technologies(soup)
    
    # Extract social links
    company['social_links'] = extract_social_links(soup)
    
    # Extract phone numbers
    company['phones'] = extract_phones(soup)
    
    # Extract funding information
    company['funding'] = extract_funding_info(soup)
    
    return company


def extract_emails(soup) -> List[str]:
    """Extract all visible email addresses from page"""
    emails = []
    
    # Find mailto links
    mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
    for link in mailto_links:
        email = link.get('href').replace('mailto:', '')
        if email and email != 'locked':
            emails.append(email)
    
    # Find text that looks like emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    all_text = soup.get_text()
    found_emails = re.findall(email_pattern, all_text)
    emails.extend(found_emails)
    
    return list(set(emails))  # Remove duplicates


def extract_phones(soup) -> List[str]:
    """Extract all visible phone numbers from page"""
    phones = []
    
    # Find tel links
    tel_links = soup.find_all('a', href=re.compile(r'^tel:'))
    for link in tel_links:
        phone = link.get('href').replace('tel:', '')
        phones.append(phone)
    
    # Find text that looks like phone numbers
    phone_pattern = r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}'
    phone_elems = soup.find_all(text=re.compile(phone_pattern))
    for elem in phone_elems:
        phone_match = re.search(phone_pattern, str(elem))
        if phone_match:
            phones.append(phone_match.group())
    
    return list(set([clean_text(p) for p in phones]))


def extract_social_links(soup) -> Dict[str, str]:
    """Extract social media profile links"""
    social = {}
    
    # LinkedIn
    linkedin = soup.find('a', href=re.compile(r'linkedin\.com/in/'))
    if linkedin:
        social['linkedin'] = linkedin.get('href')
    
    # Twitter
    twitter = soup.find('a', href=re.compile(r'twitter\.com/|x\.com/'))
    if twitter:
        social['twitter'] = twitter.get('href')
    
    # Facebook
    facebook = soup.find('a', href=re.compile(r'facebook\.com/'))
    if facebook:
        social['facebook'] = facebook.get('href')
    
    # GitHub
    github = soup.find('a', href=re.compile(r'github\.com/'))
    if github:
        social['github'] = github.get('href')
    
    return social


def extract_experience(soup) -> List[Dict[str, str]]:
    """Extract work experience/employment history"""
    experience = []
    
    # Apollo may show experience in various formats
    exp_section = soup.find('div', class_=re.compile(r'.*experience.*', re.I))
    if exp_section:
        job_items = exp_section.find_all('div', class_=re.compile(r'.*job.*|.*position.*', re.I))
        for job in job_items:
            exp_data = {
                'title': '',
                'company': '',
                'duration': '',
                'description': ''
            }
            
            title_elem = job.find('div', class_=re.compile(r'.*title.*', re.I))
            if title_elem:
                exp_data['title'] = clean_text(title_elem.get_text())
            
            company_elem = job.find('div', class_=re.compile(r'.*company.*', re.I))
            if company_elem:
                exp_data['company'] = clean_text(company_elem.get_text())
            
            duration_elem = job.find('div', class_=re.compile(r'.*duration.*|.*date.*', re.I))
            if duration_elem:
                exp_data['duration'] = clean_text(duration_elem.get_text())
            
            if exp_data['title'] or exp_data['company']:
                experience.append(exp_data)
    
    return experience


def extract_education(soup) -> List[Dict[str, str]]:
    """Extract education history"""
    education = []
    
    edu_section = soup.find('div', class_=re.compile(r'.*education.*', re.I))
    if edu_section:
        edu_items = edu_section.find_all('div', class_=re.compile(r'.*school.*|.*degree.*', re.I))
        for item in edu_items:
            edu_data = {
                'school': '',
                'degree': '',
                'field': '',
                'years': ''
            }
            
            school_elem = item.find('div', class_=re.compile(r'.*school.*|.*university.*', re.I))
            if school_elem:
                edu_data['school'] = clean_text(school_elem.get_text())
            
            degree_elem = item.find('div', class_=re.compile(r'.*degree.*', re.I))
            if degree_elem:
                edu_data['degree'] = clean_text(degree_elem.get_text())
            
            if edu_data['school'] or edu_data['degree']:
                education.append(edu_data)
    
    return education


def extract_technologies(soup) -> List[str]:
    """Extract technologies/tools/skills used"""
    technologies = []
    
    tech_section = soup.find('div', class_=re.compile(r'.*technolog.*|.*tech.*stack.*', re.I))
    if tech_section:
        tech_items = tech_section.find_all(['span', 'div'], class_=re.compile(r'.*tag.*|.*badge.*|.*chip.*', re.I))
        for item in tech_items:
            tech_name = clean_text(item.get_text())
            if tech_name and len(tech_name) > 1:
                technologies.append(tech_name)
    
    return list(set(technologies))


def extract_funding_info(soup) -> Dict[str, Any]:
    """Extract funding/investment information for companies"""
    funding = {
        'total_funding': '',
        'last_funding_round': '',
        'investors': []
    }
    
    funding_section = soup.find('div', class_=re.compile(r'.*funding.*', re.I))
    if funding_section:
        total_elem = funding_section.find(text=re.compile(r'Total Funding', re.I))
        if total_elem:
            total_value = total_elem.find_next('div') or total_elem.find_next('span')
            funding['total_funding'] = clean_text(total_value.get_text()) if total_value else ''
        
        round_elem = funding_section.find(text=re.compile(r'Last.*Round|Latest.*Round', re.I))
        if round_elem:
            round_value = round_elem.find_next('div') or round_elem.find_next('span')
            funding['last_funding_round'] = clean_text(round_value.get_text()) if round_value else ''
    
    return funding


def clean_text(text: str) -> str:
    """
    Clean extracted text by removing extra whitespace and special characters.
    
    Args:
        text: Raw text to clean
    
    Returns:
        Cleaned text
    """
    if not text:
        return ''
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove common UI artifacts
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def detect_page_type(html: str) -> str:
    """
    Detect the type of Apollo page from HTML content.
    
    Args:
        html: HTML content
    
    Returns:
        Page type: 'search', 'contact_profile', 'company_profile', or 'unknown'
    """
    soup = BeautifulSoup(html, 'lxml')
    
    # Check URL patterns in the page
    if soup.find('div', class_=re.compile(r'.*search.*results.*', re.I)):
        return 'search'
    elif soup.find('a', href=re.compile(r'/people/')) or soup.find('div', class_=re.compile(r'.*person.*profile.*', re.I)):
        return 'contact_profile'
    elif soup.find('a', href=re.compile(r'/companies/')) or soup.find('div', class_=re.compile(r'.*company.*profile.*', re.I)):
        return 'company_profile'
    
    return 'unknown'

