# SmartDrive: AI-Powered Google Drive Organizer

SmartDrive is an intelligent automation tool that declutters your Google Drive. Unlike simple organizers that rely on filenames, SmartDrive reads the **actual content** of your files—including PDFs, Google Docs, and Images—to intelligently categorize them into folders like Finance, HR, Marketing, and Projects.

Powered by **Google Gemini 2.5 Flash**, it uses Multimodal AI (Text + Vision) to "see" receipts, posters, and documents just like a human would.

## Key Features
* **Multimodal Classification:** Reads text from PDFs/Docs and *sees* images (JPG/PNG) to understand context.
* **Smart Rate Limiting:** Automatically handles API quotas with intelligent backoff and cooling periods.
* **Dry Run Mode:** Simulates organization without moving files, ensuring safety before execution.
* **Secure Configuration:** Uses environment variables (`.env`) to keep API keys safe.

## Tech Stack
* **Language:** Python 3.10+
* **AI Model:** Google Gemini 2.5 Flash (via `google-genai` SDK)
* **APIs:** Google Drive API v3
* **Libraries:** `PyPDF2`, `Pillow`, `python-dotenv`

## Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yuvii2109/edxso_assignment_3.git

cd edxso_assignment_3
```

### 2. Install Dependencies

```Bash
pip install -r requirements.txt
```

### 3. Configure Credentials

* **Google Cloud:** Enable the Google Drive API in your Google Cloud Console.
* **Credentials:** Create an OAuth 2.0 Client ID (Desktop App) and download the JSON file. Rename it to credentials.json and place it in the project root.
* **Environment Variables:** Create a .env file in the root folder:

GEMINI_API_KEY=your_gemini_api_key_here

### 4. Run the Organizer

```Bash
python main.py
```

**Note:** On the first run, a browser window will open asking you to log in to your Google account to authorize Drive access.