# Expense Claims Management System

A desktop-based Expense Claims Management System built for managing employee reimbursements from receipt upload to final payment.

The application supports three main roles:

- Staff
- Manager
- Finance

It simplifies expense submission using OCR, provides manager approval workflows, prevents duplicate claims, tracks monthly expense limits, and provides Finance with expense analytics.

---

## Problem Statement

Employees often spend their own money on business expenses such as:

- Travel
- Meals
- Office supplies
- Taxi / local transport
- Accommodation

Traditional expense claim processes require employees to manually enter several fields, managers to manually review claims, and Finance teams to track reimbursements separately.

This project was designed to make that process faster and safer.

The workflow is:

Employee uploads receipt  
→ System extracts expense information  
→ Employee reviews/corrects it  
→ Manager approves/rejects claim  
→ Finance reviews approved claims  
→ Finance marks claim as paid  
→ Finance analyses company expenses

---

# Key Features

## Receipt Upload and OCR

Employees can upload receipt or invoice images.

The application uses OCR to extract information such as:

- Merchant name
- Expense date
- Amount
- Currency
- Expense category

The extracted information is shown to the employee before submission.

Since OCR may not always be perfect, all extracted fields can be corrected manually.

---

## Staff Dashboard

Staff members can:

- Upload receipts
- Create expense claims
- Review OCR extracted information
- Save claims as Draft
- Submit claims
- View previous claims
- Track unpaid claims

---

## Manager Dashboard

Managers can:

- Review claims submitted by their team
- Approve claims
- Reject claims with a reason
- View claims waiting for approval

Managers can also submit their own expense claims.

A manager is never allowed to approve their own claim.

Their claim is automatically routed to the next manager in the approval hierarchy.

---

## Finance Dashboard

Finance users can:

- View manager-approved claims
- View the original receipt
- Mark claims as Paid
- View paid claim history
- Analyse company spending
- Review duplicate alerts
- Review expense-limit violations

Once a claim is marked as **Paid**, it becomes final and cannot move backwards in the workflow.

---

# Expense Analytics

The Finance Analysis Dashboard provides filters for:

- Month
- Employee ID
- Expense Category
- Currency

It displays:

- Total Filed Amount
- Ready To Pay Amount
- Paid Amount
- Total Claims
- Over-Limit Claims
- Duplicate Alerts

The dashboard also includes:

- Expense Trend
- Expense Breakdown by Category
- Employee Spending
- Claim Status Distribution
- Expense Limit Alerts
- Business Insights

---

# Duplicate Receipt Detection

Duplicate reimbursement is an important business risk.

The application checks receipts using multiple signals.

These include:

- Receipt file hash
- OCR text similarity
- Merchant similarity
- Expense amount
- Expense date
- Currency

An exact duplicate receipt can be blocked.

Claims that appear very similar are flagged for Finance or Manager review.

This helps detect cases where the same receipt is submitted again even if some information is entered slightly differently.

---

# Expense Limits

Monthly spending limits are maintained for different expense categories.

Example categories include:

| Category | Example Monthly Limit |
|---|---:|
| Taxi / Local Travel | INR 6,000 |
| Meals | INR 5,000 |
| Travel | INR 12,000 |
| Accommodation | INR 20,000 |
| Office Supplies | INR 4,000 |
| Other | INR 5,000 |

If a claim exceeds the employee's monthly category limit, the system flags it.

The claim is not automatically rejected because the business may still decide that the expense was valid.

Instead, the manager and Finance team can review the limit warning.

---

# Claim Lifecycle

The main claim workflow is:

text
Draft
  ↓
Submitted
  ↓
Approved
  ↓
Paid


SUBMITED BUT REJECTED - 
Submitted
  ↓
Rejected

HIERARCHY 

Staff
  ↓
Level 1 Manager
  ↓
Level 2 Manager
  ↓
Level 3 Manager
  ↓
Level 4 Manager

A manager's personal claim is routed to the next higher-level manager.

The Level 4 manager is treated as the final approval level in the demo hierarchy and therefore does not submit personal expense claims.

This was an implementation assumption because no higher approver exists above Level 4 in the demo organisation.

Sample Users


Example demo accounts:

Role	Employee ID	Password Level
Staff	EMP001	      1234     0
Staff	EMP002	      1234     0 
Manager	EMP003	      1234     1
Manager	EMP005	      1234     2
Manager	EMP006	      1234     3
Manager	EMP007	      1234     4
Finance	FIN001	      1234     0 



Technology Stack

The application was built using:

Python
Tkinter
SQLite
Tesseract OCR
OpenCV
Pillow
Matplotlib
RapidFuzz
Python

Used for the application logic and business rules.

Tkinter

Used to build the desktop user interface.

SQLite

Used as the local application database.

Tesseract OCR

Used to extract text from receipt and invoice images.

OpenCV

Used to preprocess receipt images before OCR.

Matplotlib

Used to generate Finance analytics charts.

RapidFuzz

Used as part of similarity-based duplicate receipt detection.


project structure 
EXPENSE CLAIMS VSP/
│
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── database/
│   └── db.py
│
├── services/
│   ├── auth_service.py
│   ├── claim_service.py
│   ├── receipt_processor.py
│   ├── duplicate_checker.py
│   └── analytics_service.py
│
├── ui/
│   ├── login.py
│   ├── staff_dashboard.py
│   ├── manager_dashboard.py
│   ├── finance_dashboard.py
│   └── claim_form.py
│
├── utils/
│   ├── constants.py
│   └── helpers.py
│
├── assets/
│
├── data/
│
└── uploads/
    └── receipts/




How to Run the Project
1. Clone the repository
git clone YOUR_GITHUB_REPOSITORY_URL

Move into the project directory:

cd expense-claims-management-system
2. Create a virtual environment
Windows
python -m venv venv

Activate it:

venv\Scripts\Activate.ps1

If PowerShell blocks activation, run:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

Then activate the environment again.

3. Install Python dependencies
pip install -r requirements.txt
Tesseract OCR Installation

Tesseract OCR must also be installed separately because it is not installed through pip.

On Windows, the typical installation path is:

C:\Program Files\Tesseract-OCR\tesseract.exe

The application currently uses this path for Tesseract.

If Tesseract is installed somewhere else, update the Tesseract executable path in the receipt processing configuration.

Example:

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
4. Run the application

From the project root:

python app.py

The Expense Claims application should open.


Decisions and Assumptions

Several business decisions were required because the task intentionally leaves implementation choices open.

1. Approved Means Ready To Pay

No separate Unpaid database status was created.

A claim with status:

Approved

means that the manager has approved it but Finance has not paid it yet.

The Staff dashboard therefore treats Submitted and Approved claims as unpaid.

2. Paid Claims Are Final

Once Finance marks a claim as Paid, the claim cannot return to any previous status.

This follows the requirement that a paid reimbursement should not go backwards.

3. Managers Cannot Approve Their Own Claims

Managers can create expense claims.

Their claims are automatically assigned to the next higher-level manager.

This prevents self-approval.

4. Highest-Level Manager

The demonstration hierarchy contains four management levels.

Since no manager exists above Level 4, the Level 4 manager is treated as the final approval authority and does not create personal claims in this implementation.

5. OCR Is Assistive, Not Fully Automatic

Receipt OCR can be unreliable when:

Images are blurred
Text is handwritten
Lighting is poor
Receipt formats differ significantly
Currency formatting differs

Therefore OCR results are presented to the employee for review instead of being submitted automatically.

6. Duplicate Detection Uses Multiple Signals

Exact receipt matching alone is not sufficient because an employee may submit the same receipt again with slightly different text.

Therefore duplicate detection considers file hashes as well as claim similarities.

7. Expense Limit Violations Are Flagged

An expense exceeding a limit is not automatically rejected.

It is flagged for business review because there may be legitimate exceptions.


Data Used

No company dataset was provided with the task.

Therefore realistic demonstration data was created, including:

Employees with realistic names
Multiple management levels
Finance users
Multiple expense categories
Different expense amounts
Expense limits
Duplicate receipt scenarios
Claims near or above expense limits

Receipt and invoice images were also used during OCR testing.

Some testing images were obtained from receipt/invoice datasets available through Kaggle and Roboflow.

Large third-party datasets are intentionally not included in this repository.

Challenges Faced
OCR Accuracy

Different receipts use different fonts, layouts, currencies, and image quality.

To improve OCR reliability, image preprocessing was added using OpenCV and multiple OCR configurations were tested.

The system still allows user correction because fully automatic extraction cannot be guaranteed.

Duplicate Detection

The same receipt may be submitted:

On a different date
With a slightly different merchant name
With altered description text
Weeks later

Therefore simple exact text matching was not sufficient.

The system combines file hashing and similarity checks.

Approval Hierarchy

Managers also need to claim expenses.

The workflow had to ensure that managers could submit their own claims without being able to approve them.

This was handled using a hierarchy-based approver assignment.

Claim State Safety

The application needed to prevent invalid transitions such as:

Paid → Approved

Business rules were added to ensure that Paid remains a final state.

AI Tools Used

AI tools were used during development.

ChatGPT

ChatGPT was used for:

Improving OCR extraction logic
UI design iteration
Designing the Finance analytics dashboard
README/documentation drafting

All generated or suggested code was reviewed and tested within the project before being used.

Application OCR

Tesseract OCR is used by the application itself to extract text from receipt images.

OpenCV preprocessing is used to improve receipt readability before OCR.

What I Would Do With Another Week

With additional development time, I would focus on the following improvements.

1. Machine Learning Receipt Understanding

Train or integrate a document understanding model to improve extraction of:

Merchant
Date
Total amount
Tax
Currency
Expense category

This would improve performance on complex and poorly formatted receipts.

2. Stronger Duplicate Detection

Improve duplicate detection using:

Image embeddings
OCR embeddings
Receipt layout similarity
Merchant normalization
Learned similarity models
3. Web Deployment

The current solution is a Tkinter desktop application.

With more time, I would migrate the application to a web-based interface so employees, managers, and Finance could access it through a browser.

A backend such as Flask or FastAPI could be combined with a modern web frontend.

4. Automated Testing

Add unit and integration tests for:

Claim lifecycle
Self-approval prevention
Duplicate detection
Expense limits
Finance payment processing
Authentication
5. Notifications

Add email or application notifications when:

A claim is submitted
A manager approves/rejects a claim
Finance pays a claim
A claim exceeds its spending limit
6. Cloud Storage and Database

Replace local receipt storage and SQLite with cloud storage and a production database.

7. Better Finance Reporting

Add:

Excel/PDF report export
Monthly summaries
Department-level analysis
Cost-centre reporting
Trend comparisons
Demo Video

A 3–5 minute walkthrough of the project is available here:

Video Link: https://drive.google.com/file/d/14SxiNR2q9N8K2ozTutTyMfDRkAsLly9d/view?usp=sharing


The video demonstrates:

Staff receipt submission
OCR extraction
Manager approval
Finance payment
Expense analytics
Design decisions
Challenges encountered