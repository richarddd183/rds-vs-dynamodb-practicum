## Executive Summary
This project aims to compare two distinct cloud database architectures: Instance-based (Amazon RDS) and Serverless (Amazon DynamoDB). Using 10 years of enrollment data from Andrews University, this research will demonstrate how modern "Serverless" technologies can reduce operational costs for storing historical records while maintaining high performance during retrieval.
## Problem Statement
Many organizations currently pay high monthly fees for "Instance-based" databases to store historical records.
● The “Car Rental” Problem: Using an instance-based database like RDS is like renting a car by the day. You pay for the car even when it is sitting in your garage.
● The Reality of Historical Data: Organizations (like universities) often keep records for 10+ years for auditing, government compliance, or trend analysis. Monitoring tools (like AWS CloudWatch) show that these records are often only queried once a month for specific reports.
● The Opportunity: By moving this "Cold Data" to a Serverless model, the university could potentially reduce its database costs, as it would only pay when a staff member actually clicks "Run Report."
## Technical Approach (How DynamoDB Works)
For this project, I will implement Amazon DynamoDB, which is a NoSQL, Serverless database.
● No Server Management: Unlike the traditional SQL databases discussed in our textbook, DynamoDB does not require me to manage a virtual server.

● The "Taxi" Solution to the Problem: If RDS is a "Car Rental," DynamoDB is like a Taxi. You only pay for the distance you travel. If the database is not being used, the cost
is $0.00.
● Schema Design: I will structure the AU Enrollment data using a "Partition Key" (the Year) and a "Sort Key" (the Department), allowing for extremely fast lookups of specific historical trends without the need for complex table JOINs.
## Methodology & Stress Testing
To validate the research, I will conduct a series of Stress Tests.
What is a Stress Test? Imagine the Teleférico (cable car) in La Paz, Bolivia. On a normal day, people enter slowly and the system is fine. A Stress Test is what happens if 5,000 people try to enter one single station at the exact same time. We want to see if the cable car system slows down or breaks, hypothetically, of course.

In my database, I will use a Python script to send 1,000 requests per second to both RDS and DynamoDB to see:
1. Which system answers faster (Latency).
2. Which system is more stable under high pressure.

## Project Timeline
Month 1: Setup & Data Collection: Gather enrollment figures from the AU Office of Institutional Effectiveness (Fact Books 2014-2024). Configure the initial
AWS RDS and DynamoDB environments.
Month 2: Implementation & Testing: Import all CSV data into both systems. Write and execute a Python program to perform Stress Tests and measure
retrieval speeds.
Month 3: Financial Analysis & Writing: Review the AWS Billing Dashboard to compare costs. Document findings in the final research paper and prepare
the oral presentation.

## Appendix: Finding the Data at Andrews University
To gather the data for this project, I will access the "Andrews University Fact Book" via the Office of Institutional Effectiveness; if not updated, I will request the most updated records.
These public reports provide:

● Headcount Enrollment: Total students per year.
● Department Breakdown: Number of students in the School of Computing vs. other colleges.
● Demographics: International vs. Domestic student ratios.
