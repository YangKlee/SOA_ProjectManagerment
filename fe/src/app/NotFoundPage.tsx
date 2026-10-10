import { Link } from 'react-router-dom'

export function NotFoundPage({ withinLayout = false }: { withinLayout?: boolean }) {
  const Heading = withinLayout ? 'h2' : 'h1'
  const content = <section className="dash-surface dash-placeholder">
    <Heading>404 — Không tìm thấy trang</Heading>
    <p>Đường dẫn không tồn tại. Vui lòng kiểm tra URL hoặc trở về trang chủ.</p>
    <Link to="/">Về trang chủ</Link>
  </section>
  return withinLayout ? content : <main className="dashboard dash-main">{content}</main>
}
