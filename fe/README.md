# Frontend — Quản lý đồ án tốt nghiệp

React + Vite + TypeScript, dùng npm, React Router và Axios client chung. Đã triển khai trang đăng nhập và điều hướng/bảo vệ route theo role. Các trang quản trị viên, giảng viên và sinh viên dùng chung dashboard với header, sidebar theo vai trò, thông tin tài khoản và đăng xuất; CRUD nghiệp vụ chưa được triển khai. Luồng auth đã được kiểm thử bằng API mock, chưa xác minh với tài khoản backend thực tế.

## Chạy tại máy

Dùng Node.js 24 LTS (CI dùng Node 24). Từ thư mục repository:

```powershell
cd fe
npm ci
Copy-Item .env.example .env
npm run dev
```

Mở `http://localhost:5173`. Cổng dev được cố định; nếu đang bận, dừng tiến trình đang sử dụng cổng hoặc truyền `--port` khác. Khi thay đổi `.env`, khởi động lại Vite.

| Lệnh | Chức năng |
| --- | --- |
| `npm run dev` | Chạy Vite dev server |
| `npm run build` | Kiểm tra TypeScript và build vào `dist/` |
| `npm run preview` | Xem bản build trên máy |
| `npm run lint` | Kiểm tra ESLint |
| `npm run typecheck` | Kiểm tra TypeScript riêng |
| `npm run test` | Chạy toàn bộ test một lần |
| `npm run test:watch` | Chạy test khi sửa file |

## Cấu trúc

```text
src/
  app/                  # Routes, trang đích theo role và integration tests
  config/               # Gateway dev proxy và test HTTP qua Vite thật
  features/auth/        # Login, DTO/API, auth context/provider, route guards
  services/
    api-client.ts       # Axios instance và quản lý access token trong bộ nhớ
    api-error.ts        # ApiError và chuẩn hóa lỗi
    api-client.test.ts  # Test qua mock adapter, không gọi backend
  styles/global.css
  test/setup.ts
  main.tsx
  vite-env.d.ts
```

Thêm `features/<feature>/` cho từng nghiệp vụ và `components/` cho thành phần dùng chung khi cần.

## Đăng nhập và route graph

```text
/ hoặc đường dẫn không tồn tại
  ├─ chưa đăng nhập -> /login
  └─ đã đăng nhập -> trang tương ứng role

/login -- POST /auth/login/ --> role từ response
  ├─ 1 -> /admin   (Quản trị viên)
  ├─ 2 -> /lecture (Giảng viên)
  └─ 3 -> /student (Sinh viên)

Protected route
  ├─ chưa đăng nhập -> /login
  ├─ sai role -> trang tương ứng role của tài khoản
  └─ đúng role -> hiển thị trang

Đăng xuất -> xóa user/access token -> /login
```

Form nhận MSSV/UserID và mật khẩu; có hiện/ẩn mật khẩu, validation, trạng thái đang gửi và thông báo lỗi an toàn. MSSV phải là UserID của tài khoản vì backend không cung cấp lookup riêng theo MSSV. Không có chọn role: role lấy từ response auth-service.

Request qua Axios/Gateway:

```http
POST /auth/login/
Content-Type: application/json
```

```json
{ "identifier": "SV001", "password": "your-password" }
```

Response contract theo [auth-service README](../services/auth-service/README.md):

```json
{
  "access": "<JWT access token>",
  "refresh": "<JWT refresh token>",
  "token_type": "Bearer",
  "user": {
    "user_id": "SV001",
    "first_name": "An",
    "last_name": "Nguyen",
    "role": 3
  }
}
```

Ví dụ trên chỉ hiển thị các field identity được frontend sử dụng; DTO backend có thêm các field được mô tả trong service README. `identifier` được trim, password giữ nguyên. HTTP 400/422 báo dữ liệu không hợp lệ; 401 báo sai thông tin đăng nhập; lỗi network/timeout hiển thị thông báo thử lại. Response thiếu field cần thiết hoặc role ngoài số 1/2/3 không tạo session.

`AuthProvider` giữ user và access token trong bộ nhớ; Axios gắn Bearer cho các request sau đăng nhập. Không dùng localStorage/sessionStorage, không giữ refresh token và không refresh tự động. Reload hoặc đóng tab sẽ cần đăng nhập lại. Đăng xuất chỉ xóa session frontend, không gọi API thu hồi token vì chưa có contract logout/revocation. Backend chịu trách nhiệm xác thực JWT, hạn token và quyền truy cập; frontend guard chỉ kiểm soát điều hướng.

Khi thêm protected API calls, xử lý 401 bằng `useAuth().logout()` và cho người dùng đăng nhập lại. Hiện các trang role chưa gọi API nghiệp vụ nên chưa có luồng hết hạn token chủ động.

Production hosting phải trả `index.html` cho đường dẫn SPA `/login`, `/admin`, `/lecture`, `/student` (kể cả khi mở trực tiếp). Giữ API prefixes chuyển đến Gateway, không rewrite API thành HTML. Không thay đổi cổng hoặc route backend.

## Cấu hình Gateway

```dotenv
VITE_API_BASE_URL=/
VITE_API_PROXY_TARGET=http://localhost:8000
```

Mọi API request phải dùng đường dẫn Gateway. Giữ nguyên các prefix `/auth/*`, `/academic/*`, `/registrations/*` theo contract của backend; không gọi trực tiếp cổng service hoặc Consul từ trình duyệt. Các route khác chỉ được thêm khi đã xác minh contract.

Axios mặc định dùng `/` để request cùng origin với frontend. Trong development, Vite proxy các prefix `/auth`, `/academic`, `/registrations`, `/topics` đến Gateway được cấu hình bằng `VITE_API_PROXY_TARGET` (mặc định `http://localhost:8000`). Giữ nguyên đường dẫn, method, JSON body và Bearer token; Gateway tiếp tục chịu trách nhiệm route đến service. Các đường dẫn frontend `/login`, `/admin`, `/lecture`, `/student` không đi qua proxy.

```text
Browser http://localhost:5173/auth/login/
  -> Vite proxy http://localhost:8000/auth/login/
  -> API Gateway -> auth-service /login/
```

Browser chỉ gọi origin frontend nên development không cần CORS tại Gateway. Gateway và auth-service vẫn phải chạy/healthy để đăng nhập thực tế. Không cấu hình lại `VITE_API_BASE_URL=http://localhost:8000` khi muốn dùng proxy: URL tuyệt đối sẽ bỏ qua Vite và lại cần Gateway CORS.

Sau khi cập nhật `.env` hoặc proxy config, dừng Vite bằng Ctrl+C rồi chạy lại `npm run dev`. Không cần restart Gateway cho thay đổi frontend proxy.

Vite proxy phục vụ development, không được đóng gói vào `dist/`. Khi deploy production với `VITE_API_BASE_URL=/`, web server phải chuyển tiếp các API prefix trên cùng origin đến Gateway và trả SPA HTML cho route frontend. Nếu chọn API URL tuyệt đối, cấu hình CORS tại server cho origin production. Vite thay thế biến môi trường lúc build; sửa biến trên máy chủ sau build không thay đổi bundle. Dùng HTTPS trong production. Mọi biến `VITE_*` là cấu hình public, không chứa signing key, mật khẩu hoặc tokens.

## Dùng Axios client

```ts
import { apiClient, setAccessToken } from './services/api-client'
import { ApiError } from './services/api-error'

// AuthProvider đã thực hiện việc này cho luồng đăng nhập hiện tại.
setAccessToken(accessToken)

// Ví dụ đọc health qua Gateway; kiểu dữ liệu cần theo DTO thực tế.
const response = await apiClient.get<unknown>('/auth/health/')
const data = response.data

// Với giao diện hiện tại, dùng useAuth().logout() để xóa cả user và token.
setAccessToken(null)

try {
  await apiClient.get('/auth/me/')
} catch (error: unknown) {
  if (error instanceof ApiError) {
    // error.kind: http | network | timeout | cancelled | unknown
    // error.status: HTTP status nếu có
    // error.message: thông báo an toàn để hiển thị
    // error.details: dữ liệu response chưa xác thực kiểu, dùng cho lỗi field
  }
}
```

Client giữ chuẩn Axios: trả về `AxiosResponse<T>`, đọc DTO tại `response.data`. `Accept: application/json` là mặc định; Axios tự thiết lập Content-Type khi gửi JSON hoặc FormData. Timeout là 10 giây. Request nhận Bearer token hiện tại nếu có; token chỉ tồn tại trong bộ nhớ và mất khi reload. Không có refresh tự động hoặc retry; caller xử lý `401` theo luồng auth đã thống nhất. Dùng `AbortController` và tùy chọn `signal` để hủy request.

Chỉ truyền URL tương đối thuộc Gateway vào instance này; không dùng nó cho dịch vụ ngoài vì interceptor sẽ đính kèm token. Không log token hoặc toàn bộ lỗi response; không hiển thị trực tiếp `details` như HTML. Authorization và validation nghiệp vụ vẫn thuộc backend.

## Kiểm thử và CI

```powershell
npm run lint
npm run test
npm run build
```

Vitest, Testing Library và Axios Mock Adapter kiểm tra login, payload/response DTO, cả ba role, route guards, logout, duplicate submits, validation, lỗi HTTP/network/timeout và cancellation. Các test Axios kiểm tra gắn/xóa Bearer token, xử lý lỗi và base URL mặc định/override. Test proxy khởi tạo Vite thật và Gateway giả lập trên các cổng loopback tạm thời để xác nhận đường dẫn, query, method/body/header, status lỗi và SPA fallback; server tự đóng sau test. Không cần Django, Gateway thật hoặc database. Frontend CI nằm tại `../.github/workflows/frontend-tests.yml`; Python CI giữ nguyên.

Không chạy Django checks cho thay đổi chỉ thuộc frontend. Test mock không xác nhận CORS hoặc tích hợp đăng nhập với service đang chạy; cần kiểm thử bằng tài khoản hợp lệ qua Gateway trong môi trường triển khai.

Tài liệu chính thức: [Vite](https://vite.dev/guide/), [Axios instance](https://axios-http.com/docs/instance), [Vitest](https://vitest.dev/guide/), [React Router](https://reactrouter.com/start/declarative/routing).

## Dashboard theo vai trò

`/admin`, `/lecture`, `/student` dùng `src/components/layout/MainLayout.tsx` với màu chủ đạo `#363199` và trắng. Header có tên trường, nút đóng/mở sidebar, bảng thông báo và bảng tài khoản. Sidebar hiển thị tên, UserID và vai trò từ phiên đăng nhập, các nhóm menu đóng/mở độc lập, mục đang chọn và nút đăng xuất.

Menu nghiệp vụ nằm trong `src/components/layout/dashboard-menu.ts`:

- Role 1 (quản trị viên): **Học vụ** gồm Quản lý khoa, Quản lý ngành, Quản lý sinh viên, Quản lý giảng viên; **Đề tài** gồm Quản lý đề tài, Quản lý đăng ký.
- Role 2 (giảng viên): **Đề tài** gồm Quản lý đề tài.
- Role 3 (sinh viên): mục **Đăng ký đề tài** trực tiếp, không có tiêu đề nhóm.

Các vai trò giữ Tổng quan và Đăng xuất. Sidebar không còn nhóm Trang cá nhân hoặc các mục học vụ/hướng dẫn cũ. Thông tin cá nhân truy cập từ bảng tài khoản trên header hoặc nút “Thông tin của tôi” ở trang tổng quan, độc lập với thứ tự menu nghiệp vụ. Trang tổng quan có lời chào, tối đa ba truy cập nhanh lấy từ menu của vai trò hiện tại và thông tin tài khoản.

Việc chọn mục menu hiện chỉ đổi nội dung trong route vai trò hiện tại, hiển thị “Đang phát triển”; chưa có route con, CRUD, dữ liệu học vụ hoặc API thông báo. Reload trở về tổng quan và cần đăng nhập lại theo cơ chế phiên hiện tại. Không hiển thị thống kê hoặc số thông báo giả. Logo đang dùng chữ QNU tạm thời, cần thay bằng ảnh chính thức khi có tài sản được cung cấp.

Trên màn hình rộng hơn 800px, sidebar mặc định mở và có thể ẩn. Ở màn hình nhỏ, sidebar mặc định đóng, mở dưới dạng drawer với nền che, khóa cuộn trang, giữ focus bàn phím bên trong và đóng bằng Escape/nút đóng/nhấn nền che/chọn mục. Các bảng trên header đóng bằng Escape hoặc nhấn ra ngoài. Có liên kết bỏ qua điều hướng để đến nội dung chính.

Test layout kiểm tra menu/identity của cả ba vai trò, fallback tên, sidebar, nhóm menu, chọn mục, truy cập nhanh, thông báo/tài khoản, logout, drawer mobile và thay đổi breakpoint. Integration tests tiếp tục kiểm tra đăng nhập, role guards và xóa token khi đăng xuất. Chạy `npm run lint`, `npm run test`, `npm run build` để xác minh.
