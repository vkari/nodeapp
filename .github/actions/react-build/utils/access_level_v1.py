import argparse
import os
import time
import json
import requests
import threading
import mss
import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import mss
import cv2
import numpy as np
import threading


def get_config():
    """Retrieve configuration from secrets.txt or command-line arguments."""
    parser = argparse.ArgumentParser(description="Automate TSC accessibility scan.")
    parser.add_argument("--email", help="Login email")
    parser.add_argument("--password", help="Login password")
    parser.add_argument("--scan_url", help="URL to scan")
    parser.add_argument("--scan_title", help="Title of the scan")
    parser.add_argument("--record", action="store_true", help="Enable screen recording")
    parser.add_argument("--headless", type=lambda x: x.lower() == "true", help="Run browser in headless mode")
    parser.add_argument("--api_token", help="API authentication token")
    parser.add_argument("--property_id", help="Digital Property ID")

    args = parser.parse_args()
    secrets = {}

    if os.path.exists("secrets.txt"):
        with open("secrets.txt", "r") as file:
            for line in file:
                key, value = line.strip().split("=", 1)
                secrets[key.strip()] = value.strip()

    return {
        "email": args.email or secrets.get("email"),
        "password": args.password or secrets.get("password"),
        "scan_url": args.scan_url or secrets.get("scan_url"),
        "scan_title": args.scan_title or secrets.get("scan_title", "Default Scan Title"),
        "record": args.record,
        "headless": args.headless if args.headless is not None else secrets.get("headless", "False").lower() == "true",
        "api_token": args.api_token or secrets.get("api_token"),
        "property_id": args.property_id or secrets.get("property_id"),
    }



def record_screen(output_file, stop_flag):
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        fps = 20.0
        video_writer = cv2.VideoWriter(output_file, fourcc, fps, (monitor["width"], monitor["height"]))

        while not stop_flag["stop"]:
            img = np.array(sct.grab(monitor))
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            video_writer.write(img)

        video_writer.release()


def setup_webdriver(headless):
    options = Options()
    if headless:
        print("[INFO] Running WebDriver in Headless Mode")  # Debugging print
        options.add_argument("--headless=new")  # ✅ For Chrome 109+
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
    else:
        print("[INFO] Running WebDriver in GUI Mode")  # Debugging print

    service = Service(ChromeDriverManager().install())  # ✅ Use Service()
    driver = webdriver.Chrome(service=service, options=options)  # ✅ Pass service argument

    driver.maximize_window()
    return driver


def run_automation(config):
    stop_flag = {"stop": False}
    if config["record"]:
        output_video = "automation_record.avi"
        record_thread = threading.Thread(target=record_screen, args=(output_video, stop_flag))
        record_thread.start()
        print("[INFO] Screen recording started.")

    driver = setup_webdriver(headless=config["headless"])
    try:
        print("[INFO] Starting automation...")

        driver.get("https://tractorsupply.hub.essentia11y.com/login?returnTo=%2Fhome")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email")))

        driver.find_element(By.ID, "email").send_keys(config["email"])
        driver.find_element(By.ID, "password").send_keys(config["password"])
        driver.find_element(By.XPATH, "//button[contains(text(),'Login')]").click()

        WebDriverWait(driver, 10).until(EC.url_contains("home"))
        print("[SUCCESS] Login successful!")

        websites_apps_tab = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Websites/apps")))
        websites_apps_tab.click()
        time.sleep(3)

        tractorsupply_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "tractorsupply.com")))
        tractorsupply_link.click()
        time.sleep(3)

        scans_tab = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Scans")))
        scans_tab.click()
        time.sleep(3)

        run_scan_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "automated-modal-run-scan-btn")))
        run_scan_button.click()
        print("[SUCCESS] Run scan button clicked successfully!")
        time.sleep(3)

        advanced_tab = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Advanced')]")))
        driver.execute_script("arguments[0].click();", advanced_tab)
        print("[SUCCESS] Advanced tab clicked successfully!")
        time.sleep(3)

        scan_title_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "title")))
        scan_title_field.clear()
        scan_title_field.send_keys(config["scan_title"])

        deprecated_scan_tag = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "deprecated-scan-tag-selector")))
        Select(deprecated_scan_tag).select_by_visible_text("Default")
        print("[SUCCESS] Scan title and tag selected successfully!")
        # Define wait explicitly
        wait = WebDriverWait(driver, 10)

        if "," in config["scan_url"]:  # Multiple URLs detected
            print("[INFO] Using List of Pages scan...")

            # Click on "List of pages" tab
            list_of_pages_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="tab-customLinks"]')))
            list_of_pages_button.click()
            time.sleep(2)

            # Locate text box and input multiple URLs
            urls_box = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="listOfUrls"]')))
            urls_box.clear()

            # Convert the comma-separated URLs into a newline-separated format
            formatted_urls = config["scan_url"].replace(",", "\n")
            urls_box.send_keys(formatted_urls)
            print("[SUCCESS] Multiple URLs entered successfully.")

        else:  # Single webpage detected
            print("[INFO] Using Single Webpage scan...")
            single_webpage_url = wait.until(EC.presence_of_element_located((By.ID, "url")))
            single_webpage_url.clear()
            single_webpage_url.send_keys(config["scan_url"])
            print("[SUCCESS] Single URL entered successfully.")

        # Step 10: Click the "Modify headers" Checkbox
        print("[INFO] Checking the required checkbox for 'Modify headers'.")
        try:
            modify_headers_checkbox = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="section-advanced-scan"]/div[1]/app-automated-scan-advanced-scan-scope[1]/form[1]/app-advanced-scan-extra-headers[1]/app-scan-extra-headers[1]/div[1]/app-common-checkbox[1]/div[1]/label[1]/span[1]'))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", modify_headers_checkbox)
            modify_headers_checkbox.click()
            print("[SUCCESS] Checkbox for 'Modify headers' selected.")
        except Exception as e:
            print(f"[ERROR] Could not locate or interact with the 'Modify headers' checkbox: {e}")
            driver.save_screenshot("modify_headers_checkbox_error.png")
            raise

        # Step 11: Enter Header and Value
        print("[INFO] Adding header and value.")
        header_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "name")))
        header_input.clear()
        header_input.send_keys("x-tsc-lap")
        value_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "value")))
        value_input.clear()
        value_input.send_keys("LVLACSTSC")
        print("[SUCCESS] Header and value added.")

        # Step 12: Select Accessibility Conformance Level
        print("[INFO] Selecting accessibility conformance level.")
        conformance_level_dropdown = Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "conformanceLevel"))
        ))
        conformance_level_dropdown.select_by_visible_text("WCAG 2.2 Level AAA")
        print("[SUCCESS] Accessibility conformance level selected.")

        # Step 13: Enable Optional Configurations
        print("[INFO] Enabling optional configurations.")
        try:
            color_blind_emulator_checkbox = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="advanced-scan-color-blind-emulator"]'))
            )
            if not color_blind_emulator_checkbox.is_selected():
                color_blind_emulator_checkbox.click()
                print("[SUCCESS] Color-blind emulator enabled.")
        except TimeoutException:
            print("[WARNING] 'Color-blind emulator' checkbox not found.")

        try:
            pdf_discovery_checkbox = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="section-advanced-scan"]/div/app-advanced-scan-audit-options/form/div/div/div/div/app-common-checkbox[2]/div/label/div[1]/span'))
            )
            if not pdf_discovery_checkbox.is_selected():
                pdf_discovery_checkbox.click()
                print("[SUCCESS] PDF Discovery enabled.")
        except TimeoutException:
            print("[WARNING] 'PDF Discovery' checkbox not found.")

        # Step 14: Click "Run Scan"
        print("[INFO] Clicking the 'Run Scan' button.")
        final_run_scan_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//ds-button-group/div/button[1]/div")))
        driver.execute_script("arguments[0].scrollIntoView(true);", final_run_scan_button)
        final_run_scan_button.click()
        print("[SUCCESS] Scan initiated successfully!")

        time.sleep(60)
    finally:
        print("[INFO] Automation completed.")
        driver.quit()
        stop_flag["stop"] = True
        if config["record"]:
            record_thread.join()
            print(f"[INFO] Recording saved to {output_video}")

BASE_URL = "https://tractorsupply.hub.essentia11y.com/api/v1"

class LevelAccessScan:
    """Class to handle Level Access API scan retrieval and reporting."""

    BASE_URL = "https://tractorsupply.hub.essentia11y.com/api/v1"
    SCAN_HISTORY_URL = BASE_URL + "/public/digital-properties/{digitalPropertyId}/scans"
    SCAN_RESULTS_URL = BASE_URL + "/public/digital-properties/{digitalPropertyId}/scans/{scanId}/scan-results"

    def __init__(self, digital_property_id, auth_token, scan_title, scan_url):
        """Initialize the class with necessary credentials."""
        self.digital_property_id = digital_property_id
        self.auth_token = auth_token
        self.scan_title = scan_title
        self.scan_url = scan_url  # ✅ Save scan_url inside the class
        self.headers = {
            "Content-Type": "application/json",
            "x-auth-token": self.auth_token,
        }

    def fetch_scan_history(self):
        """Fetch the scan history for the digital property."""
        try:
            url = self.SCAN_HISTORY_URL.format(digitalPropertyId=self.digital_property_id)
            response = requests.get(url, headers=self.headers, params={"limit": 10})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to fetch scan history: {e}")
            return []

    def fetch_scan_results(self, scan_id):
        """Fetch scan results for a specific scan ID."""
        try:
            url = self.SCAN_RESULTS_URL.format(digitalPropertyId=self.digital_property_id, scanId=scan_id)
            response = requests.get(url, headers=self.headers, params={"tool": "access-engine"})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to fetch scan results for ID {scan_id}: {e}")
            return None

    def generate_report(self):
        """Generate a detailed scan report with retry logic."""
        max_retries = 9
        retry_delay = 29  # Wait 29 seconds between retries

        for attempt in range(max_retries):
            print(f"[INFO] Attempt {attempt + 1}/{max_retries}: Fetching scan reports...")

            scan_history = self.fetch_scan_history()
            if not scan_history:
                print("[WARNING] No scan history available. Retrying in 29 seconds...")
                time.sleep(retry_delay)
                continue  # Try again

            for scan in scan_history:
                if scan.get("title", "") == self.scan_title:
                    scan_id = scan.get("id", "N/A")
                    completed_at = scan.get("completedAt", "N/A")

                    # Fetch scan results
                    scan_results = self.fetch_scan_results(scan_id)
                    if not scan_results:
                        print(f"[WARNING] No scan results found for scan ID {scan_id}. Retrying in 29 seconds...")
                        time.sleep(retry_delay)
                        continue  # Try again

                    # Extract summary details
                    score = scan_results.get("summary", {}).get("score", "N/A")
                    metrics = scan_results.get("summary", {}).get("metrics", {})
                    findings = scan_results.get("findings", [])

                    failed_issues = {}

                    # Process findings (detailed issues)
                    for finding in findings:
                        rule_id = finding.get("ruleName", "Unknown Rule")
                        severity = finding.get("severity", "Unknown Severity")

                        if severity in ["Critical", "High"]:
                            failed_issues[rule_id] = {
                                "Rule ID": rule_id,
                                "Description": finding.get("description", "No available description"),
                                "Severity": severity,
                                "Issue": finding.get("issue", "No issue details available"),
                            }

                    # Process metrics (general statistics)
                    for rule_id, rule_data in metrics.items():
                        if rule_data.get("triggered") and rule_data.get("errors", 0) > 0:
                            severity = "Critical" if rule_data.get("errors", 0) > 2 else "High"

                            if rule_id in failed_issues:
                                failed_issues[rule_id]["Description"] = (
                                        failed_issues[rule_id]["Description"]
                                        or f"Rule {rule_id} triggered with {rule_data.get('errors')} errors"
                                )
                                failed_issues[rule_id]["Issue"] = (
                                        failed_issues[rule_id]["Issue"]
                                        or rule_data.get("issue", "No issue details available")
                                )
                            else:
                                failed_issues[rule_id] = {
                                    "Rule ID": rule_id,
                                    "Description": f"Rule {rule_id} triggered with {rule_data.get('errors')} errors",
                                    "Severity": severity,
                                    "Issue": rule_data.get("issue", "No issue details available"),
                                }

                    # Determine scan status
                    scan_status = "Failed" if failed_issues else "Passed"

                    return {
                        "Title": self.scan_title,
                        "Scan ID": scan_id,
                        "Completed At": completed_at,
                        "Scanned URL": self.scan_url,
                        "Accessibility Score": score,
                        "Status": scan_status,
                        "Failed Issues": list(failed_issues.values()),
                    }

            print(f"[WARNING] No scan report found. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

        print("[ERROR] No scan report found after 9 attempts.")
        return None   # Return None after all attempts fail

    # Return None after 3 failed attempts

    def display_report(self):
        """Display the scan report in a structured format."""
        report = self.generate_report()

        if not report:
            print("[INFO] No scan report found.")
            return

        # print("\n=== Scan Report ===")
        # print(f"Title: {report['Title']}")
        # print(f"Scan ID: {report['Scan ID']}")
        # print(f"Scanned URL: {report['Scanned URL']}")
        # print(f"Completed At: {report['Completed At']}")
        # print(f"Accessibility Score: {report['Accessibility Score']}")
        # print("Status: Scan completed\n")

        if report["Failed Issues"]:
            print("🔴 **Failed Rules:**")
            for issue in report["Failed Issues"]:
                print(f"  - **Rule ID:** {issue['Rule ID']}")
                print(f"    **Description:** {issue['Description']}")
                print(f"    **Severity:** {issue['Severity']}")
                print(f"    **Issue:** {issue['Issue']}\n")
        else:
            print("✅ No failed rules. The scan passed successfully!\n")




def main():
    """Main function to run the script."""
    config = get_config()

    if not config["email"] or not config["password"] or not config["scan_url"]:
        print("[ERROR] Missing credentials. Provide them via arguments or in secrets.txt.")
        return

    run_automation(config)

    print("[INFO] Fetching scan reports...")

    # ✅ Pass scan_url correctly
    scan_reporter = LevelAccessScan(
        digital_property_id=config["property_id"],
        auth_token=config["api_token"],
        scan_title=config["scan_title"],
        scan_url=config["scan_url"]  # ✅ Pass scan_url here
    )

    scan_reporter.display_report()  # Call the class method properly
  # Call the class method properly


if __name__ == "__main__":
    main()