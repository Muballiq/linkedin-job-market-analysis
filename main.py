from bs4 import BeautifulSoup
import pandas as pd
import requests
import seaborn as sns
import matplotlib.pyplot as plt
import re

job_id_list = []
final_job_ids = []
job_titles = []
company = []
skills = []
locations = []

master_skills = [
    "python","java","c++","c#","javascript","typescript","html","css","sql","php","ruby","go","rust","scala","shell","bash","powershell",
    "react","angular","vue.js","next.js","node.js","express.js","django","flask","spring boot","laravel","rails","bootstrap","tailwind","jquery",
    "mysql","postgresql","mongodb","oracle","sqlite","redis","sql server",
    "aws","azure","gcp","cloud computing","serverless","lambda","cloudwatch","ec2","s3",
    "docker","kubernetes","jenkins","ci/cd","ansible","terraform","prometheus","grafana","git","github","gitlab",
    "machine learning","deep learning","nlp","computer vision","data analysis","data cleaning","data preprocessing","feature engineering",
    "data visualization","statistical analysis","predictive modeling","model deployment","mlops","data mining",
    "numpy","pandas","matplotlib","seaborn","scikit-learn","tensorflow","keras","pytorch","open cv","tableau","power bi","excel",
    "hadoop","spark","kafka","hive","airflow","snowflake","bigquery",
    "network security","cybersecurity","penetration testing","ethical hacking","vulnerability assessment","firewalls","siem","splunk",
    "wireshark","tcp/ip","dns","routing","switching",
    "android development","ios development","swift","kotlin","flutter","react native",
    "manual testing","automation testing","selenium","api testing","postman","test cases","quality assurance","quality control",
    "ui design","ux design","wireframing","prototyping","figma","adobe photoshop","illustrator","after effects","premiere pro","canva",
    "graphic design","video editing","motion graphics",
    "financial analysis","budgeting","forecasting","investment analysis","taxation","audit","bank reconciliation","accounts payable",
    "accounts receivable","tally","sap","erp","bookkeeping",
    "digital marketing","seo","sem","google ads","facebook ads","email marketing","content writing","copywriting",
    "social media management","lead generation","market research","brand management","campaign management",
    "sales","b2b sales","b2c sales","negotiation","cold calling","prospecting","crm","salesforce","hubspot","revenue generation",
    "account management","client relationship management","key account management",
    "project management","operations management","strategic planning","team management","stakeholder management","product management",
    "agile","scrum","kanban","pmp","change management","risk management",
    "recruitment","talent acquisition","onboarding","payroll","employee engagement","performance management","hr analytics",
    "training and development","attendance management",
    "office management","administration","data entry","typing","back office","front desk","documentation","email communication",
    "scheduling","calendar management","travel planning","ms office","ms excel","ms powerpoint",
    "supply chain","logistics","procurement","purchase management","inventory management","warehouse management","dispatch",
    "vendor management","production planning","lean manufacturing","six sigma","automotive","quality inspection",
    "autocad","solidworks","mechanical design","electrical wiring","plc programming","hvac","robotics","embedded systems",
    "arduino","raspberry pi","civil drafting","construction management","blueprint reading","estimating",
    "nursing","medical coding","pharmacology","clinical research","patient care","hospital administration","healthcare operations",
    "customer service","customer handling","complaint resolution","store management","billing","cash handling","pos",
    "front office","housekeeping","event management","hotel management","hospitality",
    "teamwork","leadership","problem solving","critical thinking","time management","decision making",
    "adaptability","presentation skills","public speaking","creativity","innovation","analytical skills","multitasking","organizational skills"
]

master_skills = sorted(master_skills, key=len, reverse=True)

base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
location_param = "india"
keywords = ""

for start in range(0, 800, 10): 
    url = f"{base_url}?keywords={keywords}&location={location_param}&start={start}"
    response = requests.get(url)

    if response.status_code != 200:
        break

    soup = BeautifulSoup(response.content, "html.parser")
    jobs_list = soup.find_all("li")
    if not jobs_list:
        break

    for job in jobs_list:
        base_card_div = job.find("div", class_="base-card")
        if not base_card_div:
            continue

        urn = base_card_div.get("data-entity-urn")
        if not urn or ":" not in urn:
            continue

        job_id = urn.split(":")[3]
        job_id_list.append(job_id)

# Remove duplicate ids, so some job posts can't repeat
job_id_list = list(dict.fromkeys(job_id_list))
print("Total unique job IDs collected:", len(job_id_list))

for job_id in job_id_list:
    job_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    job_response = requests.get(job_url)
    if job_response.status_code != 200:
        continue

    job_soup = BeautifulSoup(job_response.content, "html.parser")

    title_tag = job_soup.find("h2", class_="top-card-layout__title")
    company_tag = job_soup.find("span", class_="topcard__flavor")
    location_tag = job_soup.find("span", class_="topcard__flavor--bullet")
    desc_tag = job_soup.find("div", class_="description__text")

    if not (title_tag and company_tag and location_tag and desc_tag):
        continue

    title_text = title_tag.get_text(strip=True)
    company_text = company_tag.get_text(strip=True)

    loc_full = location_tag.get_text(strip=True)
    loc_city = loc_full.split(",")[0].strip()

    job_desc_text = desc_tag.get_text(separator=" ", strip=True).lower()

    matched_skills = []
    for skill in master_skills:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, job_desc_text):
            matched_skills.append(skill)

    unique_matched_skills = sorted(set(matched_skills))

    final_job_ids.append(job_id)
    job_titles.append(title_text)
    company.append(company_text)
    locations.append(loc_city)
    skills.append(", ".join(unique_matched_skills))

    print("---------------------------------------------------------")
    print("Job Title :", title_text)
    print("Company   :", company_text)
    print("Location  :", loc_city)
    print("Skills    :", ", ".join(unique_matched_skills))
    print("---------------------------------------------------------")


job_dataset = pd.DataFrame({
    "Job ID": final_job_ids,
    "Job Title": job_titles,
    "Company": company,
    "Location": locations,
    "Skills": skills
})

print("\n\nBefore cleaning shape:", job_dataset.shape)


# Strip extra spaces from string columns
for col in ["Job Title", "Company", "Location", "Skills"]:
    job_dataset[col] = job_dataset[col].astype(str).str.strip()

# Replace empty strings with NaN
job_dataset.replace(r'^\s*$', pd.NA, regex=True, inplace=True)

# Drop duplicate rows (same job id + title + company + location)
job_dataset.drop_duplicates(subset=["Job ID", "Job Title", "Company", "Location"], inplace=True)

# Drop rows where critical fields are missing
job_dataset.dropna(subset=["Job ID", "Job Title", "Company", "Location"], inplace=True)

# For skills, keep NaN as "Not specified"
job_dataset["Skills"] = job_dataset["Skills"].fillna("Not specified")

print("\nAfter cleaning shape:", job_dataset.shape)

print("\nNull values per column after cleaning:")
print(job_dataset.isnull().sum())
print("\nPreview after cleaning:")
print(job_dataset.head())

final_job_ids = job_dataset["Job ID"].tolist()
job_titles = job_dataset["Job Title"].tolist()
company = job_dataset["Company"].tolist()
locations = job_dataset["Location"].tolist()
skills = job_dataset["Skills"].tolist()

job_dataset.to_excel("linkedin_jobs.xlsx", index=False)

# Convert skills string -> list per job
job_skill_lists = []
for s in skills:
    if isinstance(s, str) and s.strip() and s != "Not specified":
        job_skill_lists.append(s.split(", "))
    else:
        job_skill_lists.append([])

# Build records: each row = (Location, Skill)
records = []
for i in range(len(locations)):
    loc = locations[i]
    for skill in job_skill_lists[i]:
        records.append([loc, skill])

skill_loc_df = pd.DataFrame(records, columns=["Location", "Skill"])

# Pivot table: rows = locations, columns = skills, values = counts
pivot = pd.pivot_table(
    skill_loc_df,
    index="Location",
    columns="Skill",
    aggfunc="size",
    fill_value=0
)

# pivot.to_excel("skill_location_counts.xlsx")

# TOP 10 LOCATIONS × TOP 10 SKILLS
top_locations = pivot.sum(axis=1).sort_values(ascending=False).head(10).index
top_skills = pivot.sum(axis=0).sort_values(ascending=False).head(10).index

heatmap_df = pivot.loc[top_locations, top_skills]


plt.figure(figsize=(10, 6))
sns.heatmap(heatmap_df, cmap="Reds", annot=True, fmt="d")
plt.title("Top Skill Counts per Top Locations")
plt.ylabel("Location")
plt.xlabel("Skill")
plt.tight_layout()
plt.show()

# -----PIE CHART: TOP 10 JOB ROLES ----------

role_counts = job_dataset["Job Title"].value_counts().head(10)

print(role_counts)

plt.figure(figsize=(11, 11))
plt.pie(
    role_counts,
    labels=role_counts.index,
    autopct='%1.1f%%',
    startangle=140,
)
plt.title("Top 10 Highest Job Demanding Roles (Overall)")
plt.tight_layout()
plt.show()
