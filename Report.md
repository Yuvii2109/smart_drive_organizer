# Project Report: AI-Powered Google Drive Organizer

## 1. System Design

The system is architected as a Python-based middleware that bridges the **Google Drive API** and the **Gemini Generative AI API**. It operates on a "Scan-Analyze-Act" lifecycle:

1.  **Input Layer:** The script authenticates via OAuth 2.0 and scans a specific target folder for unorganized files, filtering out existing folders to prevent recursion loops.
2.  **Processing Layer (The "Brain"):**
    * **Content Extraction:** It uses `PyPDF2` to extract text from PDFs and the Drive API `export` method to read Google Docs. For images, it utilizes `Pillow` to load binary image data.
    * **Multimodal Analysis:** The extracted content (text or image) is sent to **Gemini 2.5 Flash**. We use a Zero-Shot classification approach, instructing the AI to categorize the file into strictly defined buckets (Finance, HR, Projects, etc.) based on its internal knowledge.
3.  **Action Layer:** Based on the AI's decision, the system dynamically checks for the existence of the target category folder (creating it if missing) and moves the file using the Drive API.

## 2. Tools & Technologies Proposed

The following stack was selected to ensure scalability, security, and multimodal capabilities:

* **Programming Language:** Python 3.10+
    * *Rationale:* Extensive library support for both Google APIs and Data Science tasks.
* **AI Model:** Google Gemini 2.5 Flash (via `google-genai` SDK)
    * *Rationale:* Chosen for its **Multimodal** capabilities (handling both text and images natively) and low latency compared to larger models.
* **Cloud Storage APIs:** Google Drive API v3
    * *Rationale:* Provides robust methods (`files.list`, `files.update`, `files.export`) needed to manage file metadata and movement.
* **Authentication:** OAuth 2.0 (`google-auth-oauthlib`)
    * *Rationale:* The industry standard for secure, user-scoped access without sharing passwords.
* **Data Processing Libraries:**
    * `PyPDF2`: Lightweight extraction of text from PDF binaries.
    * `Pillow (PIL)`: Image processing library to convert Drive streams into formats readable by the Vision model.
* **Security:** `python-dotenv`
    * *Rationale:* Ensures sensitive API keys are loaded from environment variables, preventing hardcoded secrets in source code.

## 3. AI Approach

We utilized a **Multimodal Zero-Shot Classification** strategy.
* **Why Zero-Shot?** Training a custom model requires a massive labeled dataset. By using a pre-trained LLM (Gemini 2.0), we leverage its vast existing knowledge of what an "Invoice" or "Resume" looks like without needing to train it ourselves.
* **Why Multimodal?** Standard scripts fail on image-based files (e.g., a photo of a receipt). By using Gemini's Vision capabilities, our system can "read" text inside images without needing a separate OCR library like Tesseract.

## 4. Sample Workflow

**Scenario:** A user uploads a file named `IMG_2025.jpg` (a photo of a conference poster).
1.  **Scan:** System detects `IMG_2025.jpg` in the input folder.
2.  **Read:** System downloads the image into memory (RAM).
3.  **Classify:** The image object is sent to Gemini with the prompt: *"Categorize this file... into [Finance, Marketing, HR...]"*.
4.  **Decision:** Gemini analyzes the visual text "Join us for the Annual Tech Summit" and classifies it as **Marketing**.
5.  **Act:** The system moves `IMG_2025.jpg` into the `Marketing` folder.

## 5. Limitations & Future Improvements

* **Rate Limits:** The current free tier of Gemini API has strict RPM (Requests Per Minute) limits. I implemented a `time.sleep(60)` mechanism to respect these quotas, but a production version would require a paid tier or a queue-based architecture (e.g., RabbitMQ).
* **File Sizes:** Extremely large PDFs are currently truncated to the first 2 pages to save bandwidth and token costs.
* **Future Improvement:** Implement a "Watch" mode using Google Drive Push Notifications (Webhooks) so files are organized the second they are uploaded, rather than requiring a manual script run.

## 6. Results & Visuals

The following screenshots demonstrate the system's performance on a test dataset containing mixed media (Posters, Resumes, Assignments).

### **Before Organization**

*The input folder contained a cluttered mix of images, PDFs, and documents.*
![Before Screenshot](https://drive.google.com/uc?export=view&id=1H78v1b5ZdV6AY8WToqiKM9u7dF51siwT)

### **After Organization**

*The system successfully created categories (Academics, Finance, HR, Marketing) and moved the files correctly based on their content.*
![After Screenshot](https://drive.google.com/uc?export=view&id=1KiGyq7I9eeZWHiEHwVFNz2yAplWw9cVV)

## 7. Flowchart

graph TD
    A([Start]) --> B[Authenticate with Google Drive API]
    B --> C[Scan Target Folder]
    C --> D{Files Found?}
    D -- No --> E([End Process])
    D -- Yes --> F[Iterate through next File]
    
    F --> G{Check File Type}
    
    G -- "Image (JPG/PNG)" --> H[Read Binary Image Data]
    G -- "Google Doc" --> I[Export to Plain Text]
    G -- "PDF / Text" --> J[Extract Text with PyPDF2]
    
    H --> K[Construct Multimodal Prompt]
    I --> L[Construct Text Prompt]
    J --> L
    
    K --> M[Send to Gemini 2.0 Flash]
    L --> M
    
    M --> N{AI Classification Result}
    
    N -- "Finance, HR, etc." --> O[Check if Category Folder Exists]
    N -- "Unsure / Error" --> P[Set Category to 'Misc']
    P --> O
    
    O -- No --> Q[Create New Folder]
    O -- Yes --> R[Get Folder ID]
    Q --> R
    
    R --> S[Move File to Destination]
    S --> T[Wait 60s Rate Limit Cooling]
    
    T --> D