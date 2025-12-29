from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import os
import csv
import requests
import json
from pathlib import Path
import re
import time
import yt_dlp
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

app = Flask(__name__)
CORS(app)

# Default download directory
DEFAULT_DOWNLOAD_DIR = os.path.expanduser("~/downloads/daily_mentor")

# Ensure default download directory exists
os.makedirs(DEFAULT_DOWNLOAD_DIR, exist_ok=True)

# Global progress tracking
download_progress = {}
progress_lock = Lock()

def read_csv_data():
    """Read videos from CSV file"""
    csv_path = os.path.join(os.path.dirname(__file__), 'daily_mentor_videos.csv')
    videos = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Chapter'] and row['Video Name'] and row['Loom link']:
                videos.append({
                    'chapter': row['Chapter'],
                    'videoName': row['Video Name'],
                    'loomLink': row['Loom link']
                })
    
    return videos

def generate_filename(chapter, video_name, sequential_number):
    """Generate filename in format: Chapter_VideoName_01.mp4"""
    # Clean filename of special characters and emoji codes
    clean_chapter = re.sub(r'[/:*?"<>|]', '', chapter)
    clean_video_name = re.sub(r'[/:*?"<>|]', '', video_name)
    clean_video_name = re.sub(r':[^:]+:', '', clean_video_name)  # Remove emoji codes
    padded_number = str(sequential_number).zfill(2)
    return f"{clean_chapter}_{clean_video_name}_{padded_number}.mp4"

def get_loom_video_id(url):
    """Extract Loom video ID from URL"""
    match = re.search(r'loom\.com/share/([a-zA-Z0-9]+)', url)
    return match.group(1) if match else None

def download_loom_video(loom_url, output_path, video_id=None):
    """Download Loom video to specified path using yt-dlp with progress tracking"""
    try:
        loom_id = get_loom_video_id(loom_url)
        if not loom_id:
            return {'success': False, 'error': 'Invalid Loom URL'}
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Get filename without extension
        output_template = output_path.replace('.mp4', '')
        
        print(f"\n{'='*60}")
        print(f"Downloading: {loom_url}")
        print(f"Output: {output_path}")
        print(f"{'='*60}")
        
        # Progress hook for yt-dlp
        def progress_hook(d):
            if video_id and d['status'] in ['downloading', 'finished']:
                with progress_lock:
                    if d['status'] == 'downloading':
                        # Calculate progress percentage
                        downloaded = d.get('downloaded_bytes', 0)
                        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                        
                        if total > 0:
                            percent = (downloaded / total) * 100
                            # Cap at 95% during download (video + audio streams)
                            # Reserve 5% for post-processing (merging)
                            download_progress[video_id] = min(percent * 0.95, 95)
                            print(f"\r{video_id}: {download_progress[video_id]:.1f}%", end='', flush=True)
                    elif d['status'] == 'finished':
                        # Don't set to 100% yet - still need to merge audio/video
                        download_progress[video_id] = 95
                        print(f"\n{video_id}: Merging audio...")
        
        # Fallback: Use yt-dlp to download
        # For Loom, download 720p (lowest available) with audio and merge
        ydl_opts = {
            'format': 'hls-cdn-1500+hls-cdn-audio-audio',  # 720p video + audio
            'outtmpl': output_template + '.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'concurrent_fragment_downloads': 5,  # Download 5 fragments at once for speed
            'http_chunk_size': 10485760,  # 10MB chunks for faster download
            'progress_hooks': [progress_hook],
        }
        
        # Initialize progress
        if video_id:
            with progress_lock:
                download_progress[video_id] = 0
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(loom_url, download=True)
            
            # Get the actual downloaded file path
            if info:
                downloaded_file = ydl.prepare_filename(info)
                file_size = os.path.getsize(downloaded_file) if os.path.exists(downloaded_file) else 0
                
                print(f"\n✅ Successfully downloaded: {downloaded_file}")
                print(f"Size: {file_size / (1024*1024):.2f} MB\n")
                
                # Mark as complete
                if video_id:
                    with progress_lock:
                        download_progress[video_id] = 100
                
                return {
                    'success': True, 
                    'path': downloaded_file,
                    'size': file_size
                }
            else:
                return {'success': False, 'error': 'Download failed - no info returned'}
        
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if 'private' in error_msg.lower() or 'permission' in error_msg.lower():
            return {'success': False, 'error': 'Video is private or requires authentication'}
        elif 'not found' in error_msg.lower() or '404' in error_msg:
            return {'success': False, 'error': 'Video not found or has been deleted'}
        else:
            return {'success': False, 'error': f'Download error: {error_msg}'}
    except Exception as e:
        return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    finally:
        # Clean up progress after a delay
        if video_id:
            time.sleep(2)
            with progress_lock:
                if video_id in download_progress:
                    del download_progress[video_id]

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/videos')
def get_videos():
    """Get all videos from CSV"""
    try:
        videos = read_csv_data()
        
        # Organize by chapter and add sequential numbers
        chapters = {}
        for video in videos:
            chapter = video['chapter']
            if chapter not in chapters:
                chapters[chapter] = []
            
            sequential_number = len(chapters[chapter]) + 1
            filename = generate_filename(chapter, video['videoName'], sequential_number)
            
            chapters[chapter].append({
                'chapter': chapter,
                'videoName': video['videoName'],
                'loomLink': video['loomLink'],
                'sequentialNumber': sequential_number,
                'filename': filename
            })
        
        # Convert to list format
        all_videos = []
        video_id = 0
        for chapter, chapter_videos in chapters.items():
            for video in chapter_videos:
                video['id'] = f'video_{video_id}'
                all_videos.append(video)
                video_id += 1
        
        return jsonify({'success': True, 'videos': all_videos})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/download', methods=['POST'])
def download_videos():
    """Download selected videos"""
    try:
        data = request.json
        video_ids = data.get('videoIds', [])
        download_dir = data.get('downloadDir', DEFAULT_DOWNLOAD_DIR)
        
        # Expand user path
        download_dir = os.path.expanduser(download_dir)
        
        # Create directory if it doesn't exist
        os.makedirs(download_dir, exist_ok=True)
        
        if not video_ids:
            return jsonify({'success': False, 'error': 'No videos selected'})
        
        # Get all videos
        all_videos_response = get_videos()
        all_videos_data = all_videos_response.get_json()
        
        if not all_videos_data['success']:
            return jsonify({'success': False, 'error': 'Failed to load videos'})
        
        all_videos = all_videos_data['videos']
        
        # Filter selected videos
        selected_videos = [v for v in all_videos if v['id'] in video_ids]
        
        # Download videos (keep sequential for now to avoid rate limiting)
        # But make the process more efficient
        results = []
        for video in selected_videos:
            output_path = os.path.join(download_dir, video['filename'])
            
            print(f"\n{'='*60}")
            print(f"Downloading: {video['filename']}")
            print(f"{'='*60}")
            
            result = download_loom_video(video['loomLink'], output_path, video_id=video['id'])
            
            results.append({
                'videoId': video['id'],
                'filename': video['filename'],
                'success': result['success'],
                'error': result.get('error'),
                'path': result.get('path')
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'downloadDir': download_dir
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/check-downloaded')
def check_downloaded():
    """Check which videos are already downloaded"""
    try:
        download_dir = request.args.get('dir', DEFAULT_DOWNLOAD_DIR)
        
        # Expand user path
        download_dir = os.path.expanduser(download_dir)
        
        if not os.path.exists(download_dir):
            return jsonify({'success': True, 'downloaded': [], 'dir': download_dir})
        
        # Get list of downloaded files
        downloaded_files = []
        for filename in os.listdir(download_dir):
            if filename.endswith('.mp4'):
                downloaded_files.append(filename)
        
        return jsonify({'success': True, 'downloaded': downloaded_files, 'dir': download_dir})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/progress')
def get_progress():
    """Get current download progress for all videos"""
    try:
        with progress_lock:
            progress_copy = dict(download_progress)
        return jsonify({'success': True, 'progress': progress_copy})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/select-folder', methods=['POST'])
def select_folder():
    """Validate and create a custom download folder"""
    try:
        data = request.json
        folder_path = data.get('folderPath', '')
        
        if not folder_path:
            return jsonify({'success': False, 'error': 'No folder path provided'})
        
        # Expand user path (handles ~)
        folder_path = os.path.expanduser(folder_path)
        
        # Create directory if it doesn't exist
        os.makedirs(folder_path, exist_ok=True)
        
        # Verify it's a directory
        if not os.path.isdir(folder_path):
            return jsonify({'success': False, 'error': 'Path is not a directory'})
        
        return jsonify({
            'success': True, 
            'path': folder_path,
            'message': f'Folder ready: {folder_path}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Daily Mentor Video Downloader Server")
    print("="*60)
    print(f"\n📂 Default download location: {DEFAULT_DOWNLOAD_DIR}")
    print(f"\n🌐 Open your browser and go to: http://localhost:8888")
    print("\n⚠️  Press CTRL+C to stop the server")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=8888, debug=True)

