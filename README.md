# 📹 Daily Mentor Video Downloader

Automatic bulk download tool for Loom videos organized by chapters with real-time progress tracking.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

- 📊 **CSV-Based Video Management** - Load videos from CSV with chapters and Loom links
- ⬇️ **Bulk Downloads** - Select individual videos or entire chapters
- 📈 **Real-Time Progress** - Live download progress tracking (accurate within 5%)
- 🎯 **720p Quality** - Automatic download at 720p with audio
- 📂 **Custom Download Location** - Choose where to save videos
- 💾 **Smart Status Tracking** - Remember which videos are downloaded
- 🎨 **Clean Modern UI** - Minimalist black & white design

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **pip** (Python package manager)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/NickG-HM/daily_mentor_for_sasha.git
cd daily_mentor_for_sasha
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run the application:**
```bash
python3 app.py
```

5. **Open your browser:**
```
http://localhost:8888
```

## 📝 CSV Format

Your `daily_mentor_videos.csv` should have this format:

```csv
Chapter,Video Name,Loom link
AI for eCommerce,Start Here,https://www.loom.com/share/146dfda8816d4335b497a6cf207c6808
AI for eCommerce,LLM Foundations,https://www.loom.com/share/b7f10513747e4694a0f734ad77b1e8aa
```

## 📂 Default Download Location

Videos are saved to: `~/downloads/daily_mentor`

You can change this in the UI by entering a custom path.

## 🔧 Technical Details

### Built With

- **Flask** - Web framework
- **yt-dlp** - Video download engine
- **Flask-CORS** - Cross-origin support
- **Vanilla JavaScript** - Frontend (no frameworks)

### File Structure

```
daily_mentor_for_sasha/
├── app.py                      # Flask backend
├── templates/
│   └── index.html             # Frontend UI
├── daily_mentor_videos.csv    # Video database
├── requirements.txt           # Python dependencies
├── START_SERVER.command       # Quick start script (Mac)
└── README.md                  # This file
```

## ⚠️ Important Notes

### Deployment Limitations

This application is designed to run **locally on your machine**. It will NOT work on Vercel or similar serverless platforms because:

1. ❌ Requires local file system access to save videos
2. ❌ Uses `yt-dlp` binary (not available in serverless environments)
3. ❌ Long-running downloads exceed serverless timeout limits (10s)

### Recommended Deployment Options

✅ **Local Machine** - Run with `python3 app.py` (Best option)  
✅ **Docker Container** - Deploy on VPS/Cloud with Docker  
✅ **Desktop App** - Convert to Electron app for distribution  

## 🐛 Troubleshooting

### Videos not downloading?
- Ensure `yt-dlp` is properly installed: `pip install yt-dlp`
- Check that Loom links are valid and accessible
- Verify you have write permissions to the download folder

### Port 8888 already in use?
```bash
# Find and kill the process
lsof -ti:8888 | xargs kill -9
```

### Progress stuck at 0%?
- Hard refresh your browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
- Clear browser cache and reload

## 📄 License

MIT License - Feel free to modify and use as needed.

## 👨‍💻 Author

Created for Sasha's Daily Mentor video management.

---

**Need help?** Open an issue on GitHub or contact the developer.
