# findme
OSINT tool developed for KHE 2026 | [⚠️ Liability & Disclaimer](#%EF%B8%8F-liability--disclaimer)

## About
The Internet is a large and growing dangerous place, information is scattered everywhere and most are oblivious to this fact.
`findme` is a OSINT tool that runs locally, we have two use methods in place.
- Terminal CLI
- Flask App for GUI

This application is made using Python, Flask allows for the best integration of our tool, this application has `NONE` of the following:
- Database (only you can save your results)
- Backend (Flask just serves HTML pages)
- Data Distribution (no one but you can see the information you provide as input)

This tool currently does `not` utilize any LLM for data confidence analysis, this tool does not guarantee 100% accuracy.

As a reminder, this application does `NOT` save your actions anywhere off of the device it is ran on, the developers do `NOT` want to collect
your user or behavioural data.

## Usage:
This tool is primarily developed for Linux, this tool does work on WSL (Windows Sub-System for Linux)
```bash
# clone the repo
git clone https://github.com/UnDefinedCS/findme.git
cd findme

# run environment preperation
./prepare.sh
```

You can run this straight from the terminal via:
```bash
python3 findme-cli.py
```
or run the Flask App:
```bash
python3 app.py
```

## ⚠️ Liability & Disclaimer
**Important:** This OSINT tool is provided for educational, research, and lawful purposes only. By using this software, you agree that you are solely responsible for how you use it and that misuse may violate laws or terms of service. This tool is provided *as-is* without any warranty of accuracy, reliability, or fitness for a particular purpose. The authors and contributors are not liable for any damages, losses, or legal consequences resulting from its use. Always respect privacy, handle any collected data ethically, and ensure you are legally permitted to access the information you collect.