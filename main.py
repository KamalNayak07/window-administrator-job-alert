import logging
import os
import smtplib
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# --------------------------
# Logging Setup
# --------------------------
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("job_alert.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --------------------------
# Constants
# --------------------------
TODAY = datetime.now().strftime("%Y-%m-%d")
KEYWORDS = ["rapid scale", "hyper-growth", "fast-growing", "scaling fast"]

# --------------------------
# Email Sender
# --------------------------
def send_email(html_content):
    logger.info("Preparing to send email.")
    try:
        server = smtplib.SMTP(os.getenv("EMAIL_HOST"), int(os.getenv("EMAIL_PORT")))
        server.starttls()
        server.login(os.getenv("EMAIL_HOST_USER"), os.getenv("EMAIL_HOST_PASSWORD"))
        message = f"""From: Job Bot <{os.getenv("EMAIL_HOST_USER")}>
To: {os.getenv("EMAIL_TO")}
MIME-Version: 1.0
Content-type: text/html
Subject: Bangalore Tech Job Alerts ({TODAY})

{html_content}
"""
        server.sendmail(os.getenv("EMAIL_HOST_USER"), os.getenv("EMAIL_TO"), message)
        server.quit()
        logger.info("Email sent successfully.")
    except Exception as e:
        logger.error("Failed to send email.")
        logger.exception(e)
        raise

# --------------------------
# LinkedIn Placeholder
# --------------------------
def fetch_jobs_from_linkedin():
    logger.info("Fetching jobs from LinkedIn...")
    return []  # Use official API or Puppeteer scraping in a real setup

# --------------------------
# Naukri Scraper
# --------------------------
def fetch_jobs_from_naukri():
    logger.info("Fetching jobs from Naukri...")
    jobs = []

    try:
        url = "https://www.naukri.com/lead-data-engineer-jobs-in-bangalore"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        job_cards = soup.select(".jobTuple")
        for card in job_cards:
            title = card.select_one(".title").text.strip()
            company = card.select_one(".subTitle").text.strip()
            location = card.select_one(".loc").text.strip()
            job_url = card.select_one("a.title")["href"]
            date = card.select_one(".type br + span")
            post_date = date.text.strip() if date else "N/A"

            if "bangalore" in location.lower():
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": job_url,
                    "date": post_date,
                    "description": title.lower()  # for keyword tagging
                })

    except Exception as e:
        logger.error("Failed to fetch from Naukri")
        logger.exception(e)

    return jobs

# --------------------------
# IIMJobs Scraper
# --------------------------
def fetch_jobs_from_iimjobs():
    logger.info("Fetching jobs from IIMJobs...")
    jobs = []

    try:
        url = "https://www.iimjobs.com/search/data-engineer-azure-cloud-architect-bangalore"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        job_cards = soup.select("div.job-tuple")  # May need update
        for card in job_cards:
            link = card.select_one("a")
            if not link:
                continue
            title = link.text.strip()
            job_url = "https://www.iimjobs.com" + link["href"]
            company = card.select_one(".job-comp-name").text.strip() if card.select_one(".job-comp-name") else "Unknown"
            location = card.select_one(".job-location").text.strip() if card.select_one(".job-location") else "Unknown"
            post_date = card.select_one(".job-post-date").text.strip() if card.select_one(".job-post-date") else "N/A"

            if "bangalore" in location.lower():
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": job_url,
                    "date": post_date,
                    "description": title.lower()
                })

    except Exception as e:
        logger.error("Failed to fetch from IIMJobs")
        logger.exception(e)

    return jobs

# --------------------------
# Combine All Sources
# --------------------------
def fetch_jobs():
    all_jobs = []
    for source in [fetch_jobs_from_linkedin, fetch_jobs_from_naukri, fetch_jobs_from_iimjobs]:
        try:
            jobs = source()
            all_jobs.extend(jobs)
            logger.info(f"{len(jobs)} jobs found from {source.__name__}")
        except Exception as e:
            logger.error(f"Error running {source.__name__}")
            logger.exception(e)
    return all_jobs

# --------------------------
# Format Email Table
# --------------------------
def format_job_table(jobs):
    rows = ""
    for job in jobs:
        tag = ""
        if any(keyword in job.get("description", "").lower() for keyword in KEYWORDS):
            tag = "<b>[HOT]</b>"
        rows += f"""
        <tr>
            <td>{job['title']}</td>
            <td>{job['company']}</td>
            <td>{job['location']}</td>
            <td><a href="{job['url']}">Link</a></td>
            <td>{job['date']}</td>
            <td>{tag}</td>
        </tr>"""
    return f"""
    <html><body>
    <p>Here are the new job postings for {TODAY}:</p>
    <table border="1" cellpadding="4" cellspacing="0">
        <tr><th>Title</th><th>Company</th><th>Location</th><th>URL</th><th>Date</th><th>Tags</th></tr>
        {rows}
    </table>
    </body></html>
    """

# --------------------------
# Main Execution
# --------------------------
def main():
    logger.info("=== Starting Job Alert Task ===")
    jobs = fetch_jobs()
    if not jobs:
        logger.info("No new jobs found.")
        send_email(f"<p>No new Lead or Architect Role product postings since {TODAY}.</p>")
    else:
        logger.info(f"Found {len(jobs)} total jobs.")
        table_html = format_job_table(sorted(jobs, key=lambda x: x['date'], reverse=True))
        send_email(table_html)
    logger.info("=== Job Alert Task Completed ===")

# --------------------------
# Entrypoint
# --------------------------
if __name__ == "__main__":
    main()
