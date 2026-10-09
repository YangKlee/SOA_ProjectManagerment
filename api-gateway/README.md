# API Gateway

Gateway Nginx lắng nghe ở `http://localhost:8000` và chuyển tiếp request đến
các Django service đang chạy trên máy chủ:

| Gateway URL | Service đích |
| --- | --- |
| `/auth/*` | `http://localhost:8001/*` (auth-service) |
| `/academic/*` | `http://localhost:8002/*` (academic-service) |
| `/registrations/*` | `http://localhost:8003/*` (regist-service) |

## Chạy

Chạy ba Django service trước:

```powershell
cd services\auth-service; python manage.py runserver 8001
cd services\academic-services; python manage.py runserver 8002
cd services\regist-service; python manage.py runserver 8003
```

Sau đó, từ thư mục này:

```powershell
docker compose up -d
```

Kiểm tra gateway:

```powershell
Invoke-RestMethod http://localhost:8000/health/
```

Ví dụ đăng nhập qua gateway:

```text
POST http://localhost:8000/auth/login/
```

Gateway chuyển tiếp header `Authorization: Bearer <JWT>` đến service đích.
Mỗi service vẫn phải tự xác thực JWT cho các endpoint cần bảo vệ.
