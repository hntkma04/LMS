# Gemini Security Chatbot — Terminal PoC

Chatbot này dùng Gemini API để thử nghiệm system prompt trong Terminal. Nó không dùng model local, không sửa giao diện, API, database hoặc router của LMS. Hội thoại chỉ được giữ trong RAM trong phiên chạy.

> Cảnh báo dữ liệu: system prompt, câu hỏi và lịch sử hội thoại được gửi tới Google Gemini API. Không nhập mật khẩu, token, dữ liệu cá nhân, log nhạy cảm hoặc tài liệu LMS nội bộ khi chưa được tổ chức phê duyệt.

## Kiến trúc

```text
Terminal -> ChatSession trong RAM -> Gemini REST client -> Google Gemini API
```

Client dùng endpoint `generateContent` qua `requests`, gửi API key bằng header `x-goog-api-key`, đặt `store=false`, không log prompt và loại bỏ response part được đánh dấu `thought`.

## Tạo API key

Tạo key trong Google AI Studio/Google Cloud theo [hướng dẫn API key chính thức](https://ai.google.dev/gemini-api/docs/api-key). Hãy giới hạn key cho Gemini API, đặt cảnh báo quota/billing và không commit key vào Git.

## Cấu hình

Từ thư mục repository:

```powershell
Copy-Item tools\security_chatbot\.env.example tools\security_chatbot\.env
```

Mở `tools/security_chatbot/.env` và điền:

```dotenv
GEMINI_API_KEY=your_real_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

`.env` đã thuộc mẫu ignore của repository; vẫn cần kiểm tra `git status` trước khi commit.

PoC dùng `gemini-3.5-flash-lite`, model ổn định đã được xác nhận trả lời với project hiện tại. Có thể thay model qua `GEMINI_MODEL`, nhưng phải kiểm thử khả năng truy cập và độ trễ của model bằng key/project tương ứng. Xem [danh sách model chính thức](https://ai.google.dev/gemini-api/docs/models).

## Chạy trực tiếp

Container LMS đã có `requests` trong dependency backend nên không cần cài thêm package:

```powershell
python -m tools.security_chatbot.cli
```

Lệnh trong chatbot: `/help`, `/clear`, `/exit`.

## Chạy trong Docker LMS

Source đang được bind-mount vào container backend nên không cần build lại image:

```powershell
docker compose exec backend python -m tools.security_chatbot.cli
```

Container đọc `/app/tools/security_chatbot/.env` từ file vừa tạo trên host.

Nếu muốn truyền key từ session PowerShell thay vì file:

```powershell
$env:GEMINI_API_KEY="your_real_key_here"
docker compose exec -e GEMINI_API_KEY backend python -m tools.security_chatbot.cli
Remove-Item Env:GEMINI_API_KEY
```

Không đặt key trực tiếp trong `docker-compose.yml`, source code hoặc tham số dòng lệnh.

## Test

```powershell
python -m unittest discover -s tools/security_chatbot/tests -v
python -m compileall -q tools/security_chatbot
```

Hoặc trong Docker:

```powershell
docker compose exec backend python -m unittest discover -s tools/security_chatbot/tests -v
```

Unit test dùng fake transport nên không gọi Google và không tốn quota. Một lần chạy CLI thật mới xác nhận API key, mạng, quota và model thực tế hoạt động.

## Lỗi thường gặp

- `GEMINI_API_KEY is required`: chưa điền key hoặc container chưa nhận biến môi trường.
- HTTP 401/403: key sai, bị thu hồi hoặc giới hạn API/project chưa đúng.
- HTTP 429: hết quota hoặc vượt rate limit; client chỉ retry hữu hạn.
- Model unavailable: đổi `GEMINI_MODEL` sang model được project cho phép, không hardcode model preview đã hết hạn.
- Timeout/kết nối: kiểm tra DNS, proxy, firewall và quyền truy cập `generativelanguage.googleapis.com` từ container.
- Nội dung bị chặn: client báo lý do an toàn và không tạo câu trả lời giả.

API Gemini và tên model có thể thay đổi theo thời gian; kiểm tra trang [deprecation chính thức](https://ai.google.dev/gemini-api/docs/deprecations) trước khi triển khai lâu dài.
