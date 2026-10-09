# Hệ thống quản lý đồ án tốt nghiệp — SOA

Hệ thống quản lý sinh viên, đề tài và đăng ký đồ án tốt nghiệp. Dự án dùng
kiến trúc hướng dịch vụ (SOA): mỗi service là một Django project độc lập, cung
cấp REST API và giao tiếp qua HTTP.

## Kiến trúc

```text
                         +------------------+
                         |  Consul :8500    |
                         | Service registry |
                         +--------+---------+
                                  ^
                                  | register / discover
                                  |
Client ---> API Gateway :8000 ----+------------------------------+
             |                   |                              |
             v                   v                              v
     auth-service :8001  academic-service :8002  regist-service :8003
             |                   |                              |
             |                   |<---- REST validation ---------+
             v                   v                              v
          Users             Students, Topics                Registrations
```

- **API Gateway** nhận request từ client, định tuyến đến service và chuyển
  tiếp header `Authorization`.
- **auth-service** xác thực người dùng, phát hành JWT và trả profile hiện tại.
- **academic-service** quản lý sinh viên, khoa, ngành/chuyên ngành và đề tài.
- **regist-service** xử lý đăng ký đồ án; khi hoàn thiện sẽ gọi REST tới
  academic-service để xác thực sinh viên và đề tài.
- **log-service** dành cho audit log và hiện chưa có public route qua gateway.
- **Consul** là tùy chọn cho service discovery; auth-service đã hỗ trợ tự đăng
  ký khi bật biến môi trường.

## Cấu trúc thư mục

```text
SOA_ProjectManagerment/
├── api-gateway/                     # Nginx API Gateway
│   ├── nginx.conf
│   ├── docker-compose.yml
│   └── README.md
├── database/
│   └── DB_ProjectManagerment.db      # SQLite schema/dữ liệu hiện có
├── services/
│   ├── auth-service/                 # Login, JWT, Consul registration
│   ├── academic-services/            # Student, Topic, Major, Faculty...
│   ├── regist-service/               # Registrations
│   └── log-services/                 # Audit logs
├── .github/workflows/
│   └── python-tests.yml               # CI GitHub Actions
└── README.md
```

## Cổng dịch vụ

| Thành phần | Port | Đường dẫn qua gateway |
| --- | ---: | --- |
| API Gateway | `8000` | `http://localhost:8000` |
| Auth service | `8001` | `/auth/*` |
| Academic service | `8002` | `/academic/*` |
| Registration service | `8003` | `/registrations/*` |
| Consul UI/API (tùy chọn) | `8500` | `http://localhost:8500` |

```text
/auth/*          -> http://localhost:8001/*
/academic/*      -> http://localhost:8002/*
/registrations/* -> http://localhost:8003/*
```

## Database

Database SQLite hiện tại là `database/DB_ProjectManagerment.db`, gồm các bảng
chính:

```text
Users ──< Students ──< Registrations >── Topics
Users ──< Lecturers ──< Topics
Faculties ──< Majors ──< Specializations
Users ──< AuditLogs
```

| Yêu cầu bài toán | Bảng hiện có |
| --- | --- |
| SINHVIEN | `Students` |
| DETAI | `Topics` |
| DANGKY | `Registrations` |

Hiện auth-service kết nối vào database này để xác thực bảng `Users`. Khi các
service khác hoàn thiện, cần tôn trọng ranh giới dữ liệu: auth quản lý `Users`,
academic quản lý `Students`/`Topics`, và registration quản lý `Registrations`.
Không import model hay truy cập database nội bộ của service khác.

## Yêu cầu môi trường

- Python 3.12 trở lên.
- Docker Desktop (khuyến nghị để chạy API Gateway và Consul).
- File `database/DB_ProjectManagerment.db` phải tồn tại để auth-service đăng
  nhập được.

## Cài dependency

Từ thư mục gốc:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip

python -m pip install -r services\auth-service\requirements.txt
python -m pip install -r services\academic-services\requirements.txt
python -m pip install -r services\regist-service\requirements.txt
python -m pip install -r services\log-services\requirements.txt
```

## Chạy dự án

Mở các cửa sổ PowerShell riêng.

### 1. Auth service

```powershell
cd services\auth-service
..\..\venv\Scripts\python.exe manage.py runserver 8001
```

Kiểm tra trực tiếp:

```powershell
Invoke-RestMethod http://localhost:8001/health/
```

### 2. Academic service

```powershell
cd services\academic-services
..\..\venv\Scripts\python.exe manage.py runserver 8002
```

### 3. Registration service

```powershell
cd services\regist-service
..\..\venv\Scripts\python.exe manage.py runserver 8003
```

### 4. API Gateway

Sau khi các backend chạy:

```powershell
cd api-gateway
docker compose up -d
```

Kiểm tra gateway:

```powershell
Invoke-RestMethod http://localhost:8000/health/
```

Ví dụ gọi login qua gateway:

```powershell
$body = @{ identifier = "sv001@example.com"; password = "your-password" } | ConvertTo-Json
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/auth/login/ `
  -ContentType "application/json" `
  -Body $body
```

Tắt gateway:

```powershell
docker compose down
```

## Auth API hiện có

| Method | Qua Gateway | Mô tả |
| --- | --- | --- |
| `GET` | `/auth/health/` | Health check |
| `POST` | `/auth/login/` | Nhận access/refresh JWT |
| `POST` | `/auth/token/refresh/` | Làm mới access token |
| `GET` | `/auth/me/` | Lấy profile từ Bearer token |

DTO request/response và hướng dẫn JWT chi tiết có tại
[services/auth-service/README.md](services/auth-service/README.md).

## Chạy Consul (tùy chọn)

Khởi động Consul:

```powershell
docker run --rm --name soa-consul -p 8500:8500 hashicorp/consul agent -dev -client=0.0.0.0
```

Mở PowerShell khác để tự đăng ký auth-service:

```powershell
cd services\auth-service
$env:CONSUL_AUTO_REGISTER = "true"
$env:CONSUL_SERVICE_ADDRESS = "host.docker.internal"
$env:CONSUL_HEALTH_CHECK_URL = "http://host.docker.internal:8001/health/"
..\..\venv\Scripts\python.exe manage.py runserver 8001
```

Xem service registry tại `http://localhost:8500`. Xem thêm tại
[services/auth-service/README.md](services/auth-service/README.md).

## Kiểm thử và CI

Chạy test auth-service local:

```powershell
cd services\auth-service
..\..\venv\Scripts\python.exe manage.py check
..\..\venv\Scripts\python.exe manage.py test
```

GitHub Actions tại `.github/workflows/python-tests.yml` chạy `manage.py check`
và `manage.py test` cho bốn service khi push, tạo pull request hoặc chạy thủ
công từ tab **Actions** trên GitHub.

## Trạng thái hiện tại

- Auth-service, JWT DTO, health check, Consul registration và API Gateway đã
  có khung hoạt động.
- Academic, registration và log service hiện chủ yếu là bộ khung Django; cần
  bổ sung model, serializer, URL, REST API và test nghiệp vụ.
- Gateway đã có route cho academic và registration, nhưng hai route này chỉ
  có dữ liệu khi các service tương ứng triển khai endpoint.
