# This is a small Selenium project for scraping jobs
# It is only for educational purpose
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import time
from pathlib import Path

# Ask the user for a few values before starting the scrape
job_keyword = input("Enter a job keyword (press Enter for all): ").strip()
location = input("Enter a location (press Enter for all): ").strip()
max_results = input("How many results do you want to inspect? (press Enter for 10): ").strip()

if max_results.isdigit():
    max_results = int(max_results)
else:
    max_results = 10

print(f"Starting scrape for keyword: {job_keyword or 'all'}")
print(f"Location: {location or 'all'}")
print(f"Max results to inspect: {max_results}")

# Start a Chrome browser session
service = Service()
driver = webdriver.Chrome(service=service)

# Make the browser window larger so the page is easier to interact with
driver.maximize_window()

# Open the target website
url = "https://remoteok.com/"
driver.get(url)

# Create a wait object so Selenium waits up to 15 seconds for elements
wait = WebDriverWait(driver, 15)
job_records = []

try:
    # visibility_of_element_located() is used here because the popup close button
    # must be fully visible on the screen before we can interact with it.
    # Use visibility when the element exists in the DOM but may still be hidden,
    # not yet rendered, or covered by another element.
    close_button = wait.until(EC.visibility_of_element_located((By.ID, "premium-popup-close")))

    # Scroll the button into view and click it using JavaScript
    # This is more reliable than a simple click when the element is covered or not fully visible
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", close_button)
    print("Popup closed")

except Exception as e:
    # If the popup is not found or cannot be clicked, print the error and continue
    print(f"Popup close skipped: {e}")


try:
    # element_to_be_clickable() is used here because the location input is a form field
    # that must be ready to receive user interaction. It waits until the element is not
    # only present, but also visible, enabled, and not obstructed by another element.
    # Use this condition for buttons, links, and inputs that need to be clicked or typed into.
    location_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.location-filter-input")))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", location_input)
    location_input.click()
    location_input.clear()
    location_input.send_keys(location)
    time.sleep(2)

    # Try to click a suggestion from the dropdown if it appears.
    # presence_of_all_elements_located() is used because we only need to know whether
    # matching suggestion elements exist in the DOM, even if they are not yet fully visible.
    # Use presence when the element just needs to exist, and visibility/clickable is stricter.
    suggestion_xpath = "//div[contains(@class, 'location') or contains(@class, 'suggest') or contains(@class, 'option')]"
    suggestions = wait.until(EC.presence_of_all_elements_located((By.XPATH, suggestion_xpath)))
    if suggestions:
        suggestions[0].click()
        print(f"Selected suggestion for: {location}")
    else:
        location_input.send_keys(Keys.ENTER)
        print(f"Entered location without selecting a suggestion: {location}")
except Exception as e:
    print(f"Location input failed: {e}")

try:
    # element_to_be_clickable() is also used here for the search input because the element
    # should be ready for interaction before we type into it. This is the correct choice
    # when you want to click or send keys to a field that may appear after the page loads.
    search_role = wait.until(EC.element_to_be_clickable((By.CLASS_NAME , "search-filter-input")))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_role)
    search_role.click()
    search_role.clear()
    search_role.send_keys(job_keyword)
    search_role.send_keys(Keys.ENTER)
    time.sleep(2)
    
except Exception as e:
    print(f"job_keyboard input failed: {e}")


# Find the table that contains the job listings and then target rows inside <tbody>
try:
    jobs_table = wait.until(EC.presence_of_element_located((By.ID, "jobsboard")))
    job_rows = jobs_table.find_elements(By.CSS_SELECTOR, "tbody tr.job")
    print(f"Found {len(job_rows)} visible job rows in the table body")
    print('')

    for row in job_rows:
        title = row.find_element(By.CSS_SELECTOR, "h2").text.strip()
        company = row.find_element(By.CSS_SELECTOR, "span[itemprop='hiringOrganization']").text.strip()
        location_text = row.find_element(By.CSS_SELECTOR, "td.company.position.company_and_position").text.strip()
        posted_time = row.find_element(By.CSS_SELECTOR, "td.time").text.strip()
        apply_link = row.find_element(By.CSS_SELECTOR, "td.source a").get_attribute("href")

        job_records.append({
            "title": title,
            "company": company,
            "location_text": location_text,
            "posted_time": posted_time,
            "apply_link": apply_link
        })

        print(f"JOB TITLE: {title}")
        print(f"COMPANY: {company}")
        print(f"LOCATION/DETAILS: {location_text}")
        print(f"POSTED: {posted_time}")
        print(f"APPLY LINK: {apply_link}")
        print("_" * 40)
except Exception as e:
    print(f"Job rows not found: {e}")

# Save the scraped jobs to a CSV file named jobs.csv in the same folder as this script
csv_path = Path(__file__).resolve().parent / "jobs.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["title", "company", "location_text", "posted_time", "apply_link"])
    writer.writeheader()
    writer.writerows(job_records)

print(f"Saved {len(job_records)} jobs to {csv_path}")

# Keep the browser open briefly so you can inspect the page before it closes
for _ in range(3):
    time.sleep(1)
    print("waiting...")

# Close the browser when finished
driver.quit()

# Notes about the waiting attributes/conditions we did not use in this script:
# - EC.visibility_of(...) : use when you already have a WebElement and want to check if it is visible.
# - EC.invisibility_of_element_located(...) : use when waiting for an element to disappear, such as a loader or popup.
# - EC.text_to_be_present_in_element(...) : use when you need to wait for a specific text to appear inside an element.
# - EC.text_to_be_present_in_element_value(...) : use when waiting for text inside an input field value.
# - EC.staleness_of(...) : use when an old page element is removed and a new one is expected to appear.
# - EC.title_contains(...) and EC.url_contains(...) : use for page navigation checks after clicking links.
# - EC.number_of_windows_to_be(...) : use when a new browser tab or window is expected to open.
# - EC.frame_to_be_available_and_switch_to_it(...) : use when working with iframes.
# - EC.alert_is_present() : use when waiting for a JavaScript alert or confirmation dialog.
#
# In short:
# - Use visibility_of_element_located() when the element must be seen by the user.
# - Use element_to_be_clickable() when the element must be ready for interaction.
# - Use presence_of_element_located() / presence_of_all_elements_located() when the element only needs to exist in the DOM.
# - For this script, visibility and clickable conditions were better for interacting with popup and form elements,
#   while presence-based conditions were better for checking that containers or suggestion lists exist. 
