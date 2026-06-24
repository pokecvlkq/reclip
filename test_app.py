import unittest
from unittest.mock import patch, MagicMock
import json
import os
import tempfile
from app import app, jobs

class ReClipTestCase(unittest.TestCase):
    def setUp(self):
        # Thiết lập client cho Flask app
        app.config['TESTING'] = True
        self.app = app.test_client()
        # Xóa các job trong memory trước mỗi test
        jobs.clear()

    def test_index_page(self):
        """Kiểm tra truy cập trang chủ '/'"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)

    def test_api_info_missing_url(self):
        """Kiểm tra API /api/info khi thiếu URL (mã lỗi 400)"""
        response = self.app.post('/api/info', 
                                 data=json.dumps({}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['error'], 'Chưa nhập đường dẫn')

    def test_api_info_empty_url(self):
        """Kiểm tra API /api/info khi URL rỗng (mã lỗi 400)"""
        response = self.app.post('/api/info', 
                                 data=json.dumps({'url': '   '}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['error'], 'Chưa nhập đường dẫn')

    def test_api_info_invalid_url_prefix(self):
        """Kiểm tra API /api/info khi URL không có tiền tố hợp lệ"""
        for invalid_url in ["youtube.com", "--help", "ftp://example.com"]:
            response = self.app.post('/api/info', 
                                     data=json.dumps({'url': invalid_url}),
                                     content_type='application/json')
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data.decode('utf-8'))
            self.assertEqual(data['error'], 'Đường dẫn không hợp lệ. Phải bắt đầu bằng http:// hoặc https://')

    @patch('subprocess.run')
    def test_api_info_success(self, mock_run):
        """Kiểm tra API /api/info lấy thông tin thành công với yt-dlp được mock"""
        # Giả lập kết quả trả về của yt-dlp
        mock_stdout = json.dumps({
            "title": "Test Video Title",
            "thumbnail": "https://example.com/thumb.jpg",
            "duration": 120,
            "uploader": "Test Uploader",
            "formats": [
                {"format_id": "137", "height": 1080, "vcodec": "h264", "tbr": 1000},
                {"format_id": "136", "height": 720, "vcodec": "h264", "tbr": 800},
                {"format_id": "251", "height": None, "vcodec": "none", "tbr": 160}
            ]
        })
        
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = mock_stdout
        mock_run.return_value = mock_process

        response = self.app.post('/api/info', 
                                 data=json.dumps({'url': 'https://www.youtube.com/watch?v=mock'}),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['title'], 'Test Video Title')
        self.assertEqual(data['uploader'], 'Test Uploader')
        self.assertEqual(len(data['formats']), 2)  # Chỉ giữ lại định dạng có resolution và vcodec != none
        self.assertEqual(data['formats'][0]['label'], '1080p')

    @patch('subprocess.run')
    def test_api_info_error(self, mock_run):
        """Kiểm tra API /api/info khi yt-dlp gặp lỗi"""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = "ERROR: Video unavailable\n"
        mock_run.return_value = mock_process

        response = self.app.post('/api/info', 
                                 data=json.dumps({'url': 'https://www.youtube.com/watch?v=error'}),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['error'], 'ERROR: Video unavailable')

    def test_api_download_missing_url(self):
        """Kiểm tra API /api/download khi thiếu URL (mã lỗi 400)"""
        response = self.app.post('/api/download', 
                                 data=json.dumps({}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['error'], 'Chưa nhập đường dẫn')

    def test_api_download_invalid_url_prefix(self):
        """Kiểm tra API /api/download khi URL không có tiền tố hợp lệ"""
        for invalid_url in ["youtube.com", "--help", "ftp://example.com"]:
            response = self.app.post('/api/download', 
                                     data=json.dumps({'url': invalid_url}),
                                     content_type='application/json')
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data.decode('utf-8'))
            self.assertEqual(data['error'], 'Đường dẫn không hợp lệ. Phải bắt đầu bằng http:// hoặc https://')

    @patch('threading.Thread')
    def test_api_download_success(self, mock_thread):
        """Kiểm tra API /api/download thành công khởi tạo tải video"""
        response = self.app.post('/api/download', 
                                 data=json.dumps({'url': 'https://www.youtube.com/watch?v=mock', 'title': 'Test'}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('job_id', data)
        
        # Kiểm tra job đã được thêm vào jobs
        job_id = data['job_id']
        self.assertIn(job_id, jobs)
        self.assertEqual(jobs[job_id]['status'], 'downloading')

    def test_api_status_not_found(self):
        """Kiểm tra API /api/status với job_id không tồn tại (mã lỗi 404)"""
        response = self.app.get('/api/status/nonexistent')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['error'], 'Không tìm thấy tác vụ')

    def test_api_status_success(self):
        """Kiểm tra API /api/status với job_id tồn tại"""
        jobs['test_job'] = {
            'status': 'downloading',
            'url': 'https://www.youtube.com/watch?v=mock',
            'title': 'Test Video'
        }
        response = self.app.get('/api/status/test_job')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'downloading')

    def test_api_file_not_ready(self):
        """Kiểm tra API /api/file khi job chưa hoàn thành (mã lỗi 404)"""
        jobs['test_job'] = {
            'status': 'downloading',
            'url': 'https://www.youtube.com/watch?v=mock',
            'title': 'Test Video'
        }
        response = self.app.get('/api/file/test_job')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['error'], 'File chưa sẵn sàng')

    def test_api_file_success(self):
        """Kiểm tra API /api/file tải file thành công khi job hoàn thành"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(b"mock video data")
            temp_file_path = temp_file.name

        try:
            jobs['test_job'] = {
                'status': 'done',
                'url': 'https://www.youtube.com/watch?v=mock',
                'title': 'Test Video',
                'file': temp_file_path,
                'filename': 'Test_Video.mp4'
            }
            response = self.app.get('/api/file/test_job')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, b"mock video data")
            self.assertIn('attachment; filename=Test_Video.mp4', response.headers.get('Content-Disposition', ''))
            response.close()
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

if __name__ == '__main__':
    unittest.main()
