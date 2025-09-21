# 🎾 Wimbledon Ballot Entry Automation Bot

An automated Python script that streamlines the Wimbledon ticket ballot application process. This bot can handle multiple entries simultaneously using auto CAPTCHA solving and a stealth chrome browser.



## 📺 Demo Video
A Python script that automates the Wimbledon ticket ballot application process. It processes multiple profiles from a CSV, solves CAPTCHAs automatically (via CapSolver), and uses a stealth Chrome browser to reduce detection — all designed to make repeated ballot entries quick and repeatable.

[![Wimbledon Ballot Bot Demo](https://img.youtube.com/vi/LzWIgH-1iZ8/0.jpg)](https://youtu.be/LzWIgH-1iZ8)

*Click the image above to watch the full demonstration*


## ✨ Features

- 🤖 **Fully Automated**: Complete end-to-end ballot application without manual intervention
- 🔄 **Multiple Entries**: Process unlimited profiles from a CSV file in sequence
- 🛡️ **CAPTCHA Solving**: Integrated CapSolver API for automatic CAPTCHA resolution
- 🕵️ **Stealth Technology**: Undetected Chrome browser to avoid bot detection
- 📊 **Progress Tracking**: Real-time logging and success/failure statistics
- ⚡ **Rate Limiting**: Built-in delays to prevent overwhelming the website
- 🎯 **High Success Rate**: Optimized for reliable form submission


## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Chrome browser installed
- CapSolver API account (for CAPTCHA solving)

### Installation

1. **Clone or download** this repository
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Get your CapSolver API key**:
   - Sign up at [capsolver.com](https://capsolver.com/)
   - Copy your API key from the dashboard

4. **Configure the bot**:
   - Open `wb.py`
   - Replace `CAPSOLVER_API_KEY = "REPLACE"` with your actual API key:
     ```python
     CAPSOLVER_API_KEY = "CAP-YOUR-ACTUAL-API-KEY-HERE"
     ```

### Setup Your Profiles

Edit the `profiles.csv` file with your application details. Each row represents one ballot entry:

MAKE THE INFORMATION UNIQUE. WIMBOLEDON MAY REJECT DUPLICATE ENTRIES.
Use uniqeue emails, phone numbers, and addresses. USE A REAL NAME AS THEY CHECK ID AT THE ENTRANCE.
```csv
Email,Name,AddressLine1,City,Postcode,MobileNumber,password,dob_day,dob_month,dob_year
john.doe@email.com,John Doe,123 Main Street,London,SW1A 1AA,07123456789,SecurePass123!,15,March,1990
jane.smith@email.com,Jane Smith,456 Park Avenue,Manchester,M1 1AA,07987654321,AnotherPass456!,22,July,1985
```

**Required Fields:**
- `Email`: Valid email address for the application
- `Name`: Full name for the ballot entry
- `AddressLine1`: Street address
- `City`: City name
- `Postcode`: UK postcode
- `MobileNumber`: UK mobile number (11 digits)
- `password`: Secure password for the account
- `dob_day`: Day of birth (1-31)
- `dob_month`: Month of birth (January, February, etc.)
- `dob_year`: Year of birth (YYYY format)

## 🎮 Running the Bot

Simply run the script:

```bash
python wb.py
```

### What Happens:

1. **Profile Loading**: Loads all profiles from `profiles.csv`
2. **Sequential Processing**: Processes each profile one by one
3. **Automated Steps** for each profile:
   - Opens stealth Chrome browser
   - Navigates to Wimbledon ballot page
   - Solves initial CAPTCHA automatically
   - Handles cookie consent
   - Clicks "JOIN THE BALLOT" button
   - Fills all form fields with profile data
   - Solves any additional CAPTCHAs
   - Submits the application
4. **Progress Tracking**: Shows real-time status updates
5. **Final Summary**: Displays success/failure statistics

### Example Output:

```
============================================================
Processing Profile 1/3
Email: john.doe@email.com
Name: John Doe
============================================================
🌐 Opening stealth browser...
📍 Navigating to ballot page...
🔐 Solving CAPTCHA automatically...
✅ CAPTCHA solved successfully
📝 Filling application form...
✅ Profile 1 (john.doe@email.com) - Application completed successfully
⏳ Waiting 30 seconds before processing next profile...

============================================================
FINAL SUMMARY
Total Profiles: 3
Successful Applications: 3
Failed Applications: 0
Success Rate: 100.0%
============================================================
```

## ⚙️ Configuration

### CAPTCHA Settings
- The bot uses CapSolver API for automatic CAPTCHA solving
- Set `AUTO_SOLVE_CAPTCHA = True` to enable automatic solving
- Set `AUTO_SOLVE_CAPTCHA = False` for manual CAPTCHA handling

### Rate Limiting
- Default 30-second delay between profiles
- Modify the delay in the main function if needed:
  ```python
  time.sleep(30)  # Change this value
  ```

## 🛠️ Troubleshooting

### Common Issues:

**❌ "CSV file not found"**
- Ensure `profiles.csv` is in the same directory as `wb.py`
- Check file permissions

**❌ "CAPTCHA solving failed"**
- Verify your CapSolver API key is correct
- Check your CapSolver account balance
- Ensure stable internet connection

**❌ "Failed to find/click JOIN button"**
- The website layout may have changed
- Check if the ballot is currently open
- Verify the ballot URL is accessible

**❌ Chrome driver issues**
- The script auto-installs Chrome driver
- Ensure Chrome browser is installed and updated
- Check internet connection for driver download

### Debug Mode:
For detailed debugging, modify the logging level in `wb.py`:
```python
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
```

## 📋 Requirements

- **Python Packages** (see `requirements.txt`):
  - seleniumbase
  - chromedriver-autoinstaller
  - requests
  - fake-useragent

- **External Services**:
  - CapSolver API account for CAPTCHA solving
  - Chrome browser

---

**⚠️ Disclaimer**: This tool is provided as-is for educational purposes. Users are responsible for complying with all applicable terms of service and regulations. The authors are not responsible for any misuse or consequences of using this software.

**🎾 Good luck with your Wimbledon ballot applications!**