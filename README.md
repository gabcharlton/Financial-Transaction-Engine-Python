# 💰 Financial Transaction Engine

A lightweight Flask application that helps small businesses transform raw bank transactions into organized financial statements.

Import CSV files from your bank or credit card, automatically categorize transactions, review them, and generate professional Income Statements and Balance Sheets—all while keeping your financial data completely local.

---

## ✨ Features

- 📥 Import CSV files from bank or credit card exports
- 🏦 Support for multiple financial accounts
- 💳 Mark accounts as Assets or Liabilities
- 🏢 Select your business structure
  - Sole Proprietorship
  - Partnership
  - Corporation
  - LLC
- 🤖 Automatic transaction categorization using rule-based logic
- ✏️ Manual category editing with dropdown menus
- 📊 Generate professional financial statements
  - Income Statement
  - Balance Sheet
- 📄 Export categorized transactions as CSV
- 🖨️ Print financial statements directly from your browser
- 🔒 Runs entirely on your computer—no cloud storage or subscriptions

---

# 📸 Screenshots

*(Coming Soon)*

Recommended screenshots:

- Home screen
- Transaction import
- Categorization page
- Income Statement
- Balance Sheet

---

# 🚀 Why I Built This

Small businesses often rely on spreadsheets or expensive bookkeeping software to organize financial transactions.

This project demonstrates how software engineering and accounting concepts can be combined to automate bookkeeping workflows using Python and Flask while keeping user data private.

It also serves as a portfolio project showcasing backend development, frontend JavaScript, data processing, and financial reporting.

---

# 🛠 Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend logic |
| Flask | Web framework |
| HTML5 | Interface |
| CSS3 | Styling |
| JavaScript | Interactive frontend |
| CSV | Transaction import/export |

---

# 📁 Project Structure

```text
financial-transaction-engine/
│
├── app.py                  # Flask application
├── requirements.txt        # Python dependencies
├── README.md
│
├── templates/
│   └── index.html          # User interface
│
└── static/
    ├── css/
    │   └── style.css       # Styling
    └── js/
        └── app.js          # Frontend functionality
```

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/financial-transaction-engine.git

cd financial-transaction-engine
```

---

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

If your system uses Python 3 separately:

```bash
pip3 install -r requirements.txt
```

---

## 3. Start the application

```bash
python app.py
```

or

```bash
python3 app.py
```

Open your browser and navigate to:

```
http://localhost:5000
```

---

# 📥 Importing Transactions

The application accepts standard CSV exports from most Canadian and US financial institutions.

Your CSV should contain at least:

| Date | Description | Amount |
|------|-------------|--------|
| 2024-01-05 | Client Payment | 3200.00 |
| 2024-01-08 | Office Supplies | -124.50 |
| 2024-01-15 | Payroll | -2100.00 |

### Amount Conventions

Positive numbers

- Money entering the account

Negative numbers

- Money leaving the account

Header rows are optional and will automatically be detected.

---

# 📊 Workflow

1. Select your business structure
2. Add a bank or credit card account
3. Import CSV transactions
4. Review automatic transaction categories
5. Adjust categories if needed
6. Generate financial statements
7. Export results

---

# 📈 Financial Statements Generated

### Income Statement

- Revenue
- Cost of Goods Sold
- Operating Expenses
- Operating Income (EBIT)
- Net Income

### Balance Sheet

- Assets
- Liabilities
- Equity
- Retained Earnings

---

# 🤖 AI Ready

The project currently uses a fast rule-based categorization engine.

The application architecture was intentionally designed so the categorization function can easily be replaced by an AI model such as:

- OpenAI GPT
- Anthropic Claude
- Google Gemini
- Local LLMs

Only the `ai_suggest()` function needs to be updated to connect to your preferred API.

---

# 🔒 Privacy

Unlike many bookkeeping tools, this application processes all data locally.

- No cloud uploads
- No subscriptions
- No external database
- Your financial data stays on your computer

---

# 🎯 Future Improvements

Planned features include:

- AI-powered transaction categorization
- PDF statement export
- Receipt OCR
- Interactive financial dashboard
- Cash flow forecasting
- Budget analysis
- Multi-currency support
- QuickBooks integration
- Bank API integrations
- Machine learning categorization

---

# 📚 Learning Outcomes

This project demonstrates experience with:

- Python development
- Flask applications
- REST APIs
- JavaScript frontend development
- Financial data processing
- Data validation
- CSV parsing
- Business logic implementation
- Accounting fundamentals
- User interface design

---

# 🤝 Contributing

Contributions, suggestions, and feature requests are welcome.

Feel free to fork the repository and submit a pull request.

---

# 📄 License

This project is licensed under the MIT License.

You are free to use, modify, and distribute this software.

---

## 👩‍💻 About the Author

**Gabrielle Charlton**

MSc Data Science Candidate | Physics Graduate | Aspiring Financial Data Scientist

I'm passionate about building practical data science and software solutions that help small businesses make better financial decisions. This project combines my interests in accounting, analytics, and software engineering.

---

⭐ If you found this project helpful, consider giving it a star!
