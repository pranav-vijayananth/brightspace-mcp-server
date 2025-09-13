"""
Brightspace MCP Server - Playwright-based web scraping for Purdue University
"""

from playwright.sync_api import sync_playwright, Browser, Page
import time
import json
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Course:
    """Data class for course information"""
    name: str
    code: str
    instructor: str
    url: str


@dataclass
class Assignment:
    """Data class for assignment information"""
    title: str
    due_date: str
    course: str
    status: str
    url: str


class BrightspaceScraper:
    """Main class for scraping Purdue Brightspace data"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    def __enter__(self):
        """Context manager entry"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.page = self.browser.new_page()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.browser:
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop()
    
    def login(self, username: str, password: str) -> bool:
        """
        Login to Purdue Brightspace with Duo Mobile 2FA
        
        Args:
            username: Purdue Career Account username
            password: Purdue Career Account password
            
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            # Navigate to Purdue Brightspace login
            print("Navigating to Purdue Brightspace...")
            self.page.goto("https://purdue.brightspace.com")
            
            # Wait for login form to load
            self.page.wait_for_selector("#username", timeout=10000)
            
            # Fill in credentials
            print("Entering credentials...")
            self.page.fill("#username", username)
            self.page.fill("#password", password)
            
            # Click login button
            self.page.click("#login-button")
            
            # Wait for Duo Mobile prompt
            print("Waiting for Duo Mobile authentication...")
            print("Please approve the login request on your Duo Mobile app...")
            
            # Wait for successful authentication (adjust selector as needed)
            try:
                self.page.wait_for_selector(".duo-success", timeout=60000)
                print("Duo Mobile authentication successful!")
                return True
            except Exception as e:
                print(f"Authentication failed or timed out: {e}")
                return False
                
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def get_courses(self) -> List[Course]:
        """
        Scrape list of enrolled courses
        
        Returns:
            List[Course]: List of course objects
        """
        try:
            # Navigate to home page
            self.page.goto("https://purdue.brightspace.com/d2l/home")
            
            # Wait for courses to load
            self.page.wait_for_selector(".course-title", timeout=10000)
            
            # Extract course information
            courses = []
            course_elements = self.page.query_selector_all(".course-title")
            
            for element in course_elements:
                try:
                    name = element.text_content().strip()
                    url = element.get_attribute("href")
                    
                    # Extract course code from name if possible
                    course_code = self._extract_course_code(name)
                    
                    courses.append(Course(
                        name=name,
                        code=course_code,
                        instructor="",  # Would need additional scraping
                        url=url or ""
                    ))
                except Exception as e:
                    print(f"Error extracting course: {e}")
                    continue
            
            return courses
            
        except Exception as e:
            print(f"Error getting courses: {e}")
            return []
    
    def get_assignments(self, course_url: str) -> List[Assignment]:
        """
        Scrape assignments for a specific course
        
        Args:
            course_url: URL of the course
            
        Returns:
            List[Assignment]: List of assignment objects
        """
        try:
            self.page.goto(course_url)
            
            # Navigate to assignments (adjust selector as needed)
            assignments_link = self.page.query_selector("a[href*='assignments']")
            if assignments_link:
                assignments_link.click()
                self.page.wait_for_load_state("networkidle")
            
            assignments = []
            # Extract assignment information (selectors will need adjustment)
            assignment_elements = self.page.query_selector_all(".assignment-row")
            
            for element in assignment_elements:
                try:
                    title_element = element.query_selector(".assignment-title")
                    due_date_element = element.query_selector(".due-date")
                    status_element = element.query_selector(".status")
                    
                    title = title_element.text_content().strip() if title_element else "Unknown"
                    due_date = due_date_element.text_content().strip() if due_date_element else "No due date"
                    status = status_element.text_content().strip() if status_element else "Unknown"
                    
                    assignments.append(Assignment(
                        title=title,
                        due_date=due_date,
                        course=self._extract_course_from_url(course_url),
                        status=status,
                        url=title_element.get_attribute("href") if title_element else ""
                    ))
                except Exception as e:
                    print(f"Error extracting assignment: {e}")
                    continue
            
            return assignments
            
        except Exception as e:
            print(f"Error getting assignments: {e}")
            return []
    
    def _extract_course_code(self, course_name: str) -> str:
        """Extract course code from course name"""
        # Simple regex to extract course codes like "CS 18000" or "MATH 16500"
        import re
        match = re.search(r'([A-Z]{2,4})\s+(\d{5})', course_name)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        return course_name.split(' - ')[0] if ' - ' in course_name else course_name
    
    def _extract_course_from_url(self, url: str) -> str:
        """Extract course name from URL"""
        # Extract course identifier from URL
        parts = url.split('/')
        for part in parts:
            if 'course' in part.lower():
                return part
        return "Unknown Course"
    
    def save_data(self, data: Dict, filename: str):
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving data: {e}")


def main():
    """Example usage of the Brightspace scraper"""
    
    # Configuration
    USERNAME = "your_purdue_username"  # Replace with your username
    PASSWORD = "your_purdue_password"  # Replace with your password
    
    # Use the scraper with context manager
    with BrightspaceScraper(headless=False) as scraper:
        # Login
        if scraper.login(USERNAME, PASSWORD):
            print("Login successful! Scraping data...")
            
            # Get courses
            courses = scraper.get_courses()
            print(f"Found {len(courses)} courses:")
            for course in courses:
                print(f"  - {course.name} ({course.code})")
            
            # Get assignments for first course (if any)
            if courses:
                first_course_url = courses[0].url
                if first_course_url:
                    assignments = scraper.get_assignments(first_course_url)
                    print(f"\nFound {len(assignments)} assignments in {courses[0].name}:")
                    for assignment in assignments:
                        print(f"  - {assignment.title} (Due: {assignment.due_date})")
            
            # Save data
            data = {
                "courses": [
                    {
                        "name": course.name,
                        "code": course.code,
                        "url": course.url
                    } for course in courses
                ],
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            scraper.save_data(data, "brightspace_data.json")
            
        else:
            print("Login failed!")


if __name__ == "__main__":
    main()
