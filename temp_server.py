from pathlib import Path
import socketserver
import http.server
import os

root_path = Path(__file__).resolve().parents[0]
temp_server_dir = root_path / "temp_server"
port = 5000

def start_temp_server():
    """
    临时 HTTP 文件服务器。
    """
    os.makedirs(temp_server_dir, exist_ok=True)
    os.chdir(temp_server_dir)
    
    handler = http.server.SimpleHTTPRequestHandler

    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"临时文件服务器已启动，端口: {port}，目录: {temp_server_dir}")
        httpd.serve_forever()

if __name__ == "__main__":
    start_temp_server()