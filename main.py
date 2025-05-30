import smtplib
import ssl
import requests
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import os

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")


TODAY = datetime.now().strftime("%Y-%m-%d")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def search_iimjobs():
    url = "https://www.iimjobs.com/search/data-engineering-azure-architect-bangalore"
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = []
    for job_card in soup.select('.job'):
        title = job_card.select_one('.title').get_text(strip=True)
        company = job_card.select_one('.org').get_text(strip=True)
        location = job_card.select_one('.loc').get_text(strip=True)
        date = job_card.select_one('.date').get_text(strip=True)
        link = "https://www.iimjobs.com" + job_card.select_one('a')['href']
        if "Bangalore" in location and ("Lead" in title or "Architect" in title):
            jobs.append((title, company, location, date, link))
    return jobs

def search_naukri():
    query = "lead architect data engineering azure cloud"
    url = f"https://www.naukri.com/{query.replace(' ', '-')}-jobs-in-bangalore"
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = []

    for card in soup.select("article.jobTuple"):
        title_elem = card.select_one("a.title")
        if not title_elem:
            continue
        title = title_elem.text.strip()
        link = title_elem["href"]
        company = card.select_one(".companyInfo span").text.strip() if card.select_one(".companyInfo span") else "N/A"
        location = card.select_one(".locWd span").text.strip() if card.select_one(".locWd span") else "N/A"
        date = card.select_one(".type br + span").text.strip() if card.select_one(".type br + span") else "N/A"
        if "bangalore" in location.lower() and ("lead" in title.lower() or "architect" in title.lower()):
            jobs.append((title, company, location, date, link))
    return jobs

def search_linkedin():
    url = (
        "https://www.linkedin.com/jobs/search/?"
        "keywords=lead%20data%20engineer%20azure%20architect&"
        "location=Bangalore%2C%20Karnataka%2C%20India&"
        "f_TPR=r86400&f_WT=2&position=1&pageNum=0"
    )
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = []

    for li in soup.select(".base-search-card"):
        title = li.select_one("h3").text.strip() if li.select_one("h3") else "N/A"
        company = li.select_one("h4").text.strip() if li.select_one("h4") else "N/A"
        location = li.select_one(".job-search-card__location").text.strip() if li.select_one(".job-search-card__location") else "N/A"
        link = li.select_one("a")["href"].split("?")[0]
        date = li.select_one("time")["datetime"] if li.select_one("time") else TODAY
        if "bangalore" in location.lower() and ("lead" in title.lower() or "architect" in title.lower()):
            jobs.append((title, company, location, date, link))
    return jobs


def format_email(jobs):
    html = "<h2>New Lead/Architect Roles in Bangalore</h2><table border='1' cellspacing='0'><tr><th>Title</th><th>Company</th><th>Location</th><th>Date</th><th>Link</th></tr>"
    for job in jobs:
        title, company, location, date, link = job
        tag = ""
        if any(k in title.lower() for k in ["hyper", "scale", "growth"]):
            tag = "🚀"
        html += f"<tr><td>{tag} {title}</td><td>{company}</td><td>{location}</td><td>{date}</td><td><a href='{link}'>Link</a></td></tr>"
    html += "</table>"
    return html

def send_email(body):
    message = MIMEMultipart("alternative")
    message["Subject"] = f"🏢 Job Alert: {TODAY}"
    message["From"] = EMAIL_HOST_USER
    message["To"] = EMAIL_TO
    part = MIMEText(body, "html")
    message.attach(part)

    context = ssl.create_default_context()
    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls(context=context)
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.sendmail(EMAIL_HOST_USER, EMAIL_TO, message.as_string())

def main():
    iimjobs = search_iimjobs()
    naukri = search_naukri()
    linkedin = search_linkedin()
    jobs = iimjobs + naukri + linkedin

    if jobs:
        jobs.sort(key=lambda x: x[3], reverse=True)  # Sort by posting date
        html = format_email(jobs)
        send_email(html)
    else:
        send_email(f"<p>No new Lead or Architect Role product postings since {TODAY}.</p>")


if __name__ == "__main__":
    main()