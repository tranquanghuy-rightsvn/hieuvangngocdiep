# Behaviors — phulocjdn.com (homepage)

Stack gốc: Vite + React + Tailwind (shadcn/Radix) + framer-motion. Không dùng Lenis/smooth-scroll lib.
Theme: `html.light` mặc định; dark = bỏ class `light`. Lưu `localStorage['theme-preference']`.

| Thành phần | Trigger | Hành vi |
|---|---|---|
| Header | — | Sticky top, nền `rgba(186,145,94,.82)` (lấy màu từ ảnh hero), blur 12px, không đổi khi cuộn |
| Nút menu | hover | scale 1.1, 200ms |
| Nút "Bảng Giá Vàng" | hover / active / click | translateY(-2px) / scale .95 / smooth scroll tới `#bang-gia` |
| Drawer menu | click ☰ | Overlay black/60 + blur 4px fade; aside trượt từ -100% (~350ms, kiểu spring); đóng ~250ms; kéo sang trái để đóng; Esc/overlay đóng |
| Submenu | click | height 0↔auto ~250ms, chevron rotate 180° 200ms; 3 cấp |
| Tìm kiếm (menu) | click | thay item bằng ô input nền primary/10; X để quay lại |
| Marquee giá | time | translateX 0→-50%, 40s linear infinite |
| Tabs Bảng giá / Biểu đồ | click | Tab active bg-gold, chữ trắng, shadow. Biểu đồ = TradingView XAUUSD widget |
| Cập nhật lúc | click | reload giá (icon xoay) |
| Hàng bảng giá | vào viewport | opacity 0→1, y 12px→0 (mobile 10px), ~450ms ease-out, từng hàng |
| Hàng bảng giá | hover | bg gold/5 |
| Card sản phẩm | hover | shadow-md→xl 300ms, ảnh scale 1.05 500ms, overlay gradient đen 30% fade, pill "Xem thêm" đổi nền primary, mũi tên x+2px |
| Carousel SP (mobile <768) | time 3.5s / dots / thumbs | exit x 0→-40 + fade (~300ms) rồi enter x 40→0 + fade |
| Card liên hệ footer | hover | y -8px, rotate -1.25deg, border gold/50, shadow vàng, glow radial; icon scale 1.05 rotate 3deg; delay stagger 20ms |
| Nút nổi desktop (≥640) | time | `animate-ring` lắc 1s infinite; hover scale 1.05; ẩn khi mở chat |
| Toggle theme | click | moon ↔ sun |
| Live chat | click | panel bottom-right: opacity/scale .95/translateY 12px → 1, 300ms ease-out |
| Thông báo (megaphone) | click | Dialog Radix: overlay black/80, content fade+zoom 95%, 200ms |
| Đặt Thông Báo Giá Vàng | click | Dialog form email/loại vàng/mua-bán/điều kiện/giá |
| Toolbar mobile (<640) | click chevron | toolbar y→16px fade 200ms, rồi nút chevron-up hiện (y12 scale .9 → 0) |
| PWA prompt | load | 2 thẻ đen-vàng ở đáy, đóng lưu localStorage |

Responsive: sm 640 (bảng desktop, nút nổi, toggle riêng), md 768 (header desktop, grid sản phẩm 3+2), lg 1024 (footer 3 cột).
Hero: min-height 92vh; ảnh desktop/mobile khác nhau.
