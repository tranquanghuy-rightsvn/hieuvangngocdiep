# GAS.md — Guideline CMS Hiệu Vàng Ngọc Diệp (hieuvangngocdiep.vn)

> Nguồn quyết định CHỐT của dự án này. Đọc TOÀN BỘ file này trước khi sửa bất kỳ file nào
> trong `gas/`. Không tự suy đoán/bịa thêm field, quy tắc, tên biến ngoài những gì ghi ở đây.
> Sửa code xong phải cập nhật ngược lại file này trong CÙNG 1 lượt sửa.
>
> Playbook chung: skill `free-cms-static-site-pipeline`. Dự án mẫu: xevip (bản sao nằm trong
> skill, `references/samples/xevip-gas/`).

## 0. Phạm vi (ĐÚNG 6 mục, không làm rộng hơn)

0. **Cập nhật giá vàng** (tab ĐẦU TIÊN, mở mặc định) — bảng giá vàng + giá bạc (mục II-A).
1. Quản lý sản phẩm — mặc định mọi sản phẩm là **Giá: Liên hệ**.
2. Cập nhật giá nhanh — 1 bảng hiện TẤT CẢ sản phẩm, admin chỉ điền giá rồi bấm **Lưu giá**.
3. Quản lý tin tức.
4. Quản lý liên hệ (khách gửi form `/lien-he/`).
5. Quản lý người dùng (root / admin / editor).

KHÔNG quản lý qua CMS (vẫn sửa trong repo như cũ): thông tin liên hệ cửa hàng, danh mục sản
phẩm + menu (`scripts/data/site.json`).

---

## I. Đăng nhập

1. Luồng: nhập email → gửi OTP qua email → nhập mã → vào Admin. Không mật khẩu, không phụ
   thuộc session Google.
2. Chỉ email ĐÃ ĐĂNG KÝ (có trong sheet `Users`) mới được gửi OTP.
3. Account chủ GAS (người deploy) LUÔN hợp lệ + LUÔN là `root` ngầm định — không lưu trong
   sheet `Users`, không hiện/không quản lý được trong tab Người dùng.
   ⚠️ `requestOtp()` phải kiểm tra `email === ownerEmail_()` SONG SONG với tra sheet `Users`.
4. Phân quyền 3 cấp `root > admin > editor` (`ROLE_RANK = { editor: 1, admin: 2, root: 3 }`).
   Ma trận quyền — CHỐT:

   | Chức năng | editor | admin | root |
   |---|---|---|---|
   | Sản phẩm (xem/thêm/sửa/xoá) | ✅ | ✅ | ✅ |
   | Cập nhật giá vàng (vàng + bạc) | ✅ | ✅ | ✅ |
   | Cập nhật giá nhanh | ✅ | ✅ | ✅ |
   | Tin tức (xem/thêm/sửa/xoá) | ✅ | ✅ | ✅ |
   | Liên hệ (xem/đổi trạng thái/xoá) | ❌ | ✅ | ✅ |
   | Người dùng (thêm/đổi quyền/xoá) | ❌ | ✅ | ✅ |

   `editor` toàn quyền với NỘI DUNG site. Ranh giới: không thấy thông tin khách hàng (tab Liên
   hệ) và không quản lý tài khoản. Chặn ở CẢ client (ẩn nav-item) LẪN server (`requireRole_`).
   Qua CMS chỉ gán được `admin` / `editor` (`CMS_MANAGEABLE_ROLES`). Dòng `root` chỉ sửa tay
   ngoài CMS. Không tự thao tác lên chính mình.
5. OTP sống 10 phút, cooldown 60 giây/email, tối đa 5 lần nhập sai rồi phải xin mã mới.
   Token phiên sống 30 ngày, lưu `localStorage`. `verifyOtp` gọi `purgeExpiredTokens_()`;
   Đăng xuất gọi `logout(token)` phía server để thu hồi token thật.
6. Server tự `requireRole_` ở MỌI hàm — ẩn nút trên UI không phải là bảo mật.

## II-A. Cập nhật giá vàng (chốt 10/10/2026)

- Tab tên **"Cập nhật giá vàng"**, nằm ĐẦU TIÊN trong menu và là tab mở mặc định. 2 section trong
  cùng tab: **Giá vàng** và **Giá bạc** (section riêng).
- Mỗi dòng: **Loại** (`name`), **Mua vào** (`buy`), **Bán ra** (`sell`) — VNĐ/chỉ, số nguyên dương.
  Thêm dòng, sửa, xoá, đổi thứ tự (↑ ↓). Mỗi section phải còn ÍT NHẤT 1 dòng (máy tính giá cần).
- Nút **"Lưu lại"** cố định ở đầu vùng nội dung (giống tab giá nhanh) → 1 lần `saveMetalPrices`
  ghi cả 2 section, 1 commit. Sửa/thêm/xoá/sắp xếp (↑ ↓) chỉ đổi BẢN NHÁP trên màn hình, KHÔNG
  ghi gì cho tới khi bấm Lưu lại (chốt 10/10/2026: tránh commit nhiều lần). Lưu lại y hệt dữ liệu cũ
  → không ghi. Rời tab khi chưa lưu → hỏi xác nhận.
- `id` mỗi dòng (dùng làm `data-id` trên site): dòng cũ GIỮ NGUYÊN id; dòng mới máy chủ tự sinh từ
  tên (chữ in hoa, không dấu). Không có ô nhập id.
- `updated_at` ("HH:mm dd/MM/yyyy", giờ VN) mỗi section: máy chủ tự đặt khi section đó có thay đổi
  — hiện ở dòng "Cập nhật lúc ..." trên site.
- **Đồng bộ MỌI nơi hiển thị giá** từ 1 nguồn `scripts/data/prices.json`: bảng giá vàng/bạc (trang
  chủ, `/bang-gia/`), dòng giá chạy (ticker), danh sách loại + đơn giá trong máy tính giá vàng
  (`/may-tinh-gia-vang/`) và máy tính giá bạc (`/may-tinh-gia-bac/`), dòng "Cập nhật lúc".
  `bake_static.py` in sẵn số vào HTML + nhúng `<script type="application/json" id="price-data">`
  cho máy tính giá; `main.js` KHÔNG còn giá viết cứng.
- ⛔ ĐÃ BỎ việc site tự lấy giá thế giới qua API (gold-api.com) rồi quy đổi đè lên bảng — giá trên
  site là giá ADMIN NHẬP. Nút "↻ Cập nhật lúc" thành dòng chữ thường (không bấm làm mới được nữa).

## II. Sản phẩm

Site KHÔNG có trang riêng cho từng sản phẩm — sản phẩm hiện ở thẻ (trang chủ, `/san-pham/`) và
khung "Xem nhanh". Vì vậy sản phẩm KHÔNG có slug/URL; định danh là **Mã sản phẩm**.

1. Field CÓ ô nhập (đúng tên key trong `scripts/data/catalog.json`):
   - **Mã sản phẩm** (`id`) — dạng `ND-XX00` (chữ in hoa, số, gạch ngang). Sản phẩm mới: CMS
     tự gợi ý mã kế tiếp theo tiền tố của danh mục đã chọn (vd Trang Sức Bạc → `ND-B09`), sửa
     được trước lần Lưu đầu. **Bất biến sau lần Lưu đầu** (chặn server + `disabled` client).
     Không trùng với sản phẩm khác (server kiểm).
   - **Tên sản phẩm** (`name`) — bắt buộc.
   - **Danh mục** (`cat`) — chọn trong danh sách CỐ ĐỊNH lấy từ `PRODUCTS` của
     `scripts/data/site.json` (server đọc file đó, client KHÔNG hard-code). Server tự chặn giá
     trị lạ. Không quản lý danh mục qua CMS.
   - **Nhóm** (`sub`) — chọn trong `children` của danh mục đã chọn (cùng nguồn `site.json`).
   - **Chất liệu** (`gold`) — gõ tự do, có gợi ý từ các giá trị đang dùng (`Vàng 24K`,
     `Vàng 999.9`, `Bạc 925`...). Để trống được (thẻ không hiện nhãn chất liệu).
   - **Trọng lượng** (`weight`) — tuỳ chọn, vd `5 li`.
   - **Giá** (`price`) — số nguyên VND, tuỳ chọn. Để trống/0 = **Liên hệ** (key `price` bị bỏ
     khỏi bản ghi). Ô nhập cho gõ `1.800.000` hoặc `1800000`.
   - **Nổi bật** (`featured`), **Mới** (`isNew`) — 2 ô tick. Chỉ ghi key khi `true` (giữ đúng
     quy ước file đang có).
   - **Mô tả** (`desc`) — dùng ở khung "Xem nhanh".
   - **Ảnh** — NHIỀU ảnh/sản phẩm (chốt 10/10/2026), tối thiểu 1. Ảnh ĐẦU TIÊN là ảnh chính
     (`img` — hiện trên thẻ sản phẩm); các ảnh sau nằm trong `gallery` (mảng tên file, đúng thứ tự).
     Trong form: tải thêm nhiều ảnh 1 lần, xoá từng ảnh, đổi thứ tự (← →), chọn ảnh chính.
     Key `gallery` chỉ có khi có từ 2 ảnh trở lên.
2. **Hiển thị giá ngoài site** (`price_html` trong `scripts/bake_static.py` + `priceHtml` trong
   `html/assets/js/main.js` — 2 chỗ phải ra cùng 1 markup):
   - Có giá → CHỈ hiện số tiền, không có chữ "Giá": `1.800.000đ`.
   - Chưa có giá → `Giá: Liên hệ` (chữ thường, không phải nút/link).
3. Lưu trữ: TOÀN BỘ sản phẩm trong **1 file `scripts/data/catalog.json`** (giống
   `services.json` của xevip — ~70 bản ghi, mỗi bản ghi nhỏ, không tách index/detail). Thứ tự
   trong file = thứ tự hiển thị (sản phẩm mới thêm vào cuối). File này là commit CHỐT.
4. Ảnh: `html/assets/img/catalog/<img>.jpg`, ghi THẲNG vào vị trí site thật.
   - Mỗi lần tải lên tạo 1 file MỚI `<mã viết thường>__<N>.jpg` (vd `nd-b09__3.jpg`, N tăng dần,
     không ghi đè). Dấu nối `__` vì mã sản phẩm chỉ có `[A-Z0-9-]` — tên ảnh của sản phẩm này không
     bao giờ trùng tiền tố ảnh của sản phẩm khác (bài học gotcha "ghép 2 slug bằng `-`").
   - Ảnh cũ đặt tên kiểu khác (vd `lac-bac-co-4-la-dinh-da.jpg`) vẫn giữ nguyên tên.
   - Lưu = client gửi DANH SÁCH ĐẦY ĐỦ ảnh theo thứ tự. Server chỉ nhận tên file đã có trên kho VÀ
     (đang thuộc sản phẩm này HOẶC mang tiền tố `<mã>__`). Ảnh cũ bị bỏ khỏi danh sách + file
     `<mã>__*` đã tải mà không dùng (tải rồi không Lưu) bị XOÁ — trừ ảnh đại diện danh mục.
   - Nén phía client (`<canvas>`): cạnh dài tối đa 1200px, JPEG q=0.85. Thẻ sản phẩm là khung
     VUÔNG (`object-fit: cover`) → nên dùng ảnh vuông. Hiện ảnh tạm ngay, upload chạy ngầm.
   - Ảnh thuộc riêng sản phẩm → xoá sản phẩm xoá kèm MỌI ảnh của nó, TRỪ ảnh đang làm ảnh đại diện
     danh mục (`img` trong `PRODUCTS` của `site.json`) — khi đó giữ ảnh lại.
   - Ngoài site: thẻ sản phẩm hiện ảnh chính + nhãn số ảnh; khung "Xem nhanh" là slide ảnh — vuốt
     (điện thoại), nút ← → và phím ← → để đổi ẢNH. Nút ← → KHÔNG còn đổi sang sản phẩm khác (chốt
     10/10/2026).
5. Xoá sản phẩm: pop-up xác nhận → gỡ khỏi `catalog.json` (+ ảnh theo mục 4).
6. Danh sách trong Admin: GAS đọc thẳng `scripts/data/catalog.json` + `scripts/data/site.json`
   từ kho mỗi lần `boot()` — luôn mới nhất kể cả site chưa build xong.

## III. Cập nhật giá nhanh

- Tab riêng tên **"Cập nhật giá nhanh"**, hiện TẤT CẢ sản phẩm 1 lượt: ảnh nhỏ, mã, tên, ô **Giá**
  (KHÔNG có cột danh mục — chốt 10/10/2026).
- Lọc theo danh mục + ô tìm (tên/mã) — chỉ là lọc hiển thị, không đổi dữ liệu.
- Ô giá trống = Liên hệ. Ô đã sửa mà chưa lưu được tô nổi bật + đếm số ô đã đổi.
- **Thanh "Lưu giá" CỐ ĐỊNH ở đầu vùng nội dung** (`position: sticky; top: 0` trong `.content`),
  luôn nhìn thấy khi cuộn bảng dài — KHÔNG đặt trong sidebar/header. Nút bị khoá khi chưa đổi gì.
- Lưu = 1 lần gọi `savePrices(token, {id: price|null})` CHỈ gửi các ô đã đổi → server đọc
  `catalog.json` mới nhất, áp giá theo `id`, ghi lại đúng 1 lần (1 commit). Mã không còn tồn
  tại → báo lỗi, không ghi gì.
- Rời tab khi còn ô chưa lưu → hỏi xác nhận (pop-up), tránh mất giá vừa gõ.

## IV. Tin tức

1. Field CÓ ô nhập:
   - **Tiêu đề** (`title`).
   - **URL bài viết** (`slug`) — tự sinh từ tiêu đề; **bất biến sau lần Lưu đầu**. URL công
     khai: `https://hieuvangngocdiep.vn/tin-tuc/<slug>/`.
   - **Chuyên mục** (`cat`) — danh sách CỐ ĐỊNH `NEWS_CATS` trong `scripts/data/site.json`
     (`cua-hang` Tin cửa hàng, `kien-thuc` Kiến thức, `cam-nang` Cẩm nang, `san-pham` Sản phẩm
     mới). Bắt buộc chọn. `build_pages.py` và CMS cùng đọc 1 nguồn này — không có bản sao thứ 2.
   - **Mô tả** (`excerpt`) — DUY NHẤT 1 field, dùng cho CẢ thẻ bài ngoài `/tin-tuc/`, đoạn dẫn
     dưới tiêu đề bài LẪN `<meta name="description">`.
   - **Ảnh bìa** (`cover`) — tỉ lệ 16:10. Bài mới: `html/assets/img/news/<slug>-cover.jpg` (đuôi
     `-cover` để không bao giờ trùng tên ảnh bìa cũ đặt theo chủ đề như `qua-tang-vang.jpg` — server
     còn chặn thêm nếu trùng); bài đã có giữ tên file cũ, tải ảnh mới = ghi đè. Phải có slug (điền tiêu đề) TRƯỚC khi tải ảnh; tải
     xong slug tự khoá. Bắt buộc trước khi Lưu.
   - **Nội dung** (`body`) — TinyMCE **chế độ iframe** (KHÔNG `inline`), tự host tại
     `https://hieuvangngocdiep.vn/vendor/tinymce/` (bản 6.8.5, copy từ xevip). Toolbar: undo/redo,
     định dạng đoạn (Đoạn văn / h2 / h3 / h4), đậm/nghiêng/gạch chân, danh sách, link, bảng,
     **chèn ảnh nhanh** (`quickimage` — mở thẳng hộp chọn file, KHÔNG dùng dialog mặc định),
     xoá định dạng, xem mã.
2. Field server tự suy: `date` (dạng `dd/mm/yyyy` như dữ liệu đang có) = ngày Lưu lần đầu (giờ
   VN), sửa lại GIỮ NGUYÊN; `updated_at` mỗi lần Lưu.
3. Ảnh trong nội dung: `html/assets/img/news/<slug>-content-<N>.jpg`, đánh số tăng dần bất
   biến. `src` lưu dạng TUYỆT ĐỐI theo domain `/assets/img/news/<file>` (toàn site dùng đường
   dẫn tuyệt đối, trang bài nằm 2 cấp thư mục). Trong editor hiển thị qua
   `raw.githubusercontent.com`, lúc lưu đổi ngược về `/assets/img/...`.
   Bọc `<figure>` + `<figcaption>` placeholder `"Sửa caption ảnh..."`; `alt`/`title` = caption
   thật, rỗng thì = Tiêu đề (đồng bộ sống). Trước khi Lưu xoá `<figcaption>` còn placeholder.
4. **Bài Smart content** (`smart: true` — 4 bài thiết kế riêng theo quy trình `/smartcontent`,
   thân bài nằm ở `scripts/content/tin-tuc/<slug>.html`): trong CMS CHỈ sửa được Tiêu đề, Chuyên
   mục, Mô tả, Ảnh bìa. Ô Nội dung bị ẩn, thay bằng dòng giải thích. Server giữ nguyên `body`
   (không có) và cờ `smart`, không nhận `body` từ client cho bài này.
5. Lưu trữ:
   - `scripts/data/posts.json` — index nhẹ (không có `body`), sắp ngày mới nhất trước. **Commit
     CHỐT** của Lưu/Xoá bài → trigger CI.
   - `scripts/data/tin-tuc/<slug>.json` — bản ghi đầy đủ 1 bài (có `body`, trừ bài smart).
6. Xoá bài: pop-up xác nhận → xoá `scripts/data/tin-tuc/<slug>.json` + file smart content (nếu
   có) + ảnh bìa + mọi ảnh `<slug>-content-*` + gỡ khỏi `posts.json` (ghi SAU CÙNG).
   `build_pages.py` tự xoá thư mục `html/tin-tuc/<slug>/` không còn trong `posts.json`.
7. Bài mới nhất (theo `date`) là bài nổi bật đầu trang `/tin-tuc/`.

## V. Liên hệ (form công khai `/lien-he/`)

- Nguồn DUY NHẤT: form `#contact-form` (trang do `build_pages.py` sinh). Field: `cf-name`,
  `cf-phone`, `cf-need`, `cf-msg` → map thành `name`, `phone`, `need`, `message`.
- Honeypot: input ẩn tên `_hp` (class `hp-field`). Có giá trị → âm thầm trả `{ok:true}`, không
  lưu. ⚠️ Ô này CHỈ ẩn nhờ rule `.hp-field` trong `html/assets/css/style.css` — mất rule là hỏng
  im lặng (xem mục IX).
- Rate-limit: 20 giây/lần theo số điện thoại.
- Gọi `fetch()` tới `GAS_EXEC_URL` (hằng số trong `html/assets/js/main.js`) với
  `Content-Type: text/plain;charset=utf-8`. Chưa có URL → form báo lỗi + mời gọi hotline, KHÔNG
  giả vờ gửi thành công.
- Trong Admin: xem danh sách, đổi trạng thái, xoá — chỉ `admin`/`root`. `status`: `"Mới"` /
  `"Đã xử lý"`.
- Thông báo: email qua `MailApp` tới ĐÚNG địa chỉ chủ dự án tự điền trong Script Property
  `NOTIFY_EMAIL` (chốt 10/10/2026: người nhận do chủ dự án cấu hình, code không ghi cứng địa chỉ
  nào). Trống thì không gửi mail nhưng vẫn lưu. Dùng CHUNG quota ~100 mail/ngày với OTP. Gửi mail lỗi KHÔNG làm hỏng việc đã lưu.
- **Mẫu email (chốt 10/10/2026): HTML chuyên nghiệp có logo** — CHỈ cho mail báo liên hệ mới. Mail
  mã OTP đăng nhập giữ dạng chữ thường (chủ dự án chốt: không cần làm đẹp). Mẫu nằm RIÊNG ở
  `gas/email.html` (template; `contactEmailHtml_()` trong `Code.js` chỉ đổ dữ liệu vào): logo
  `https://hieuvangngocdiep.vn/assets/img/logo-header.jpg` (JPG nền trắng — hiển thị ổn định mọi
  trình đọc mail), viền vàng, chân mail nâu lấy địa chỉ/hotline/giờ mở cửa từ `CONTACT` của
  `site.json` (đọc lỗi thì bỏ dòng đó, không chặn gửi mail). Bố cục bảng + style inline (trình
  đọc mail không hỗ trợ CSS hiện đại). Luôn kèm bản chữ thường (`body`) cho máy không hiện HTML.
  Tên người gửi hiển thị: "Hiệu Vàng Ngọc Diệp". Dữ liệu khách nhập chỉ chèn bằng thẻ template tự
  escape (dấu-hỏi-bằng), KHÔNG dùng thẻ chèn thô.
  ⚠️ KHÔNG viết cú pháp thẻ template trong comment của `email.html` — máy chủ đọc thẻ ở mọi nơi kể
  cả trong comment → mẫu hỏng, mail liên hệ ngừng gửi (âm thầm, vì gửi mail nằm trong try). Đã gặp
  khi test 10/10/2026.
  Mail liên hệ có nút "Gọi lại ngay" (`tel:`) và "Mở trang quản trị" (`/admin/`).
- Dữ liệu khách CHỈ nằm trong bảng dữ liệu nội bộ của CMS, **KHÔNG bao giờ ghi vào repo**.

## VI. Người dùng

- Tab chỉ hiện với `admin`/`root` (server vẫn tự chặn `requireRole_(token, "admin")`).
- Thêm: email + quyền (`admin` / `editor`); người đó tự đăng nhập bằng OTP.
- Đổi quyền chỉ giữa `admin` ↔ `editor`; không tự sửa/xoá chính mình; không hiện chủ GAS.

## VII. UX chung (MỌI thao tác trong Admin)

- ⛔ Không nhắc tới hạ tầng phía sau (bảng tính, kho mã, Apps Script...) trong BẤT KỲ thứ gì gửi
  xuống trình duyệt — chữ, gợi ý, thông báo lỗi, comment trong `app.html`/`js.html`/
  `index.html`/`css.html`. Không có nút mở thẳng kho dữ liệu. Kiểm trước mỗi lần deploy:
  `grep -niE 'sheet|spreadsheet|drive|apps script|github' gas/app.html gas/js.html gas/index.html gas/css.html`
  — chỉ được phép còn đúng các chỗ dựng URL ảnh xem trước (`raw.githubusercontent.com`).
- **Đăng xuất đặt TÁCH XA các mục khác**: nằm dưới đáy sidebar, cách khối menu một khoảng lớn
  + vạch ngăn, chữ màu đỏ nhạt — tránh bấm nhầm.
- 2 loại pop-up giữa màn hình (không `alert()`/`confirm()` native, không toast):
  Xác nhận (Huỷ/Đồng ý) TRƯỚC khi xử lý; Thông báo kết quả (1 nút Đóng) SAU khi xong.
- Mọi thao tác đổi nội dung site kèm dòng nhắc: *"Website sẽ được cập nhật sau 1-2 phút!"*.
- Mọi nút async: `disabled` + spinner, tự phục hồi trong `finally`.
- Sau Lưu/Xoá: quay về DANH SÁCH của chính mục đó, danh sách tự cập nhật, cache đồng bộ ngay.
- Chuyển tab chỉ ẩn/hiện, không tải lại. Lần đầu: 1 round-trip `boot(token)` (me, appHtml,
  products, categories, posts, newsCats, github). Lần sau: hiện ngay từ cache rồi revalidate ngầm.
- Mọi key `localStorage` (TRỪ token) mang hậu tố `CLIENT_BUILD` do server băm từ nội dung
  `app.html` + `js.html` (`clientBuild_()`), + `purgeStaleCaches_()` dọn key bản cũ. Không có
  hằng số gõ tay. Revalidate ngầm thấy `appHtml` đổi thì vẽ lại DOM (trừ khi đang mở form).
- TinyMCE chỉ `init` SAU KHI tab chứa nó đã `display:block`.

## VIII. Kiến trúc lưu trữ

**Bảng dữ liệu nội bộ "Ngoc Diep CMS Data"** (Google Sheet tự tạo lần đầu, `SPREADSHEET_ID` tự
lưu lại) — tên sheet/cột CỐ ĐỊNH:
- `Users` — `email`, `role`.
- `Contacts` — `id`, `created_at`, `name`, `phone`, `need`, `message`, `status`.

**GitHub repo `tranquanghuy-rightsvn/hieuvangngocdiep` (Contents API)** — đường dẫn CỐ ĐỊNH:
- `scripts/data/prices.json` — giá vàng + bạc. 1 file, tự nó là **commit CHỐT** của Lưu giá vàng.
- `scripts/data/catalog.json` — toàn bộ sản phẩm. **Commit CHỐT** của sản phẩm + giá.
- `scripts/data/posts.json` — index tin tức. **Commit CHỐT** của tin tức.
- `scripts/data/tin-tuc/<slug>.json` — bản ghi đầy đủ 1 bài.
- `scripts/data/site.json` — CMS chỉ ĐỌC (danh mục sản phẩm, `NEWS_CATS`), không ghi.
- `scripts/content/tin-tuc/<slug>.html` — thân bài smart content; CMS chỉ XOÁ khi xoá bài.
- `html/assets/img/catalog/*.jpg`, `html/assets/img/news/*.jpg` — ảnh, ghi thẳng vị trí site.

File commit CHỐT LUÔN ghi SAU CÙNG trong 1 thao tác.

**Build/deploy**: GitHub Actions `.github/workflows/build.yml` chạy khi push đụng 2 file chốt
(hoặc `scripts/*.py`) → `python3 scripts/build_pages.py && python3 scripts/bake_static.py` →
commit `html/`. Cloudflare tự deploy mỗi commit trên `master`. Độ trễ thực tế ~1-2 phút.

| Thư mục | Ai ghi | Sửa tay được? |
|---|---|---|
| `scripts/data/catalog.json`, `posts.json`, `tin-tuc/*.json` | CMS | ❌ (CMS ghi đè) |
| `scripts/data/site.json`, `scripts/*.py`, `scripts/content/**` | Người | ✅ |
| `html/tin-tuc/**`, `html/lien-he/`, `html/bang-gia/`, `html/may-tinh-*`, `html/chinh-sach-bao-mat/`, `html/404.html` | `build_pages.py` | ❌ (sửa trong `build_pages.py`) |
| `html/index.html`, `html/san-pham/`, `html/gioi-thieu/` | Người + `bake_static.py` vá vùng động | ✅ ngoài vùng vá |
| `html/admin/index.html`, `html/vendor/tinymce/` | Người | ✅ (build không đụng) |

**Trang quản trị**: `https://hieuvangngocdiep.vn/admin/` — nhúng CMS bằng iframe (cắt 25px thanh
cảnh báo bằng CSS), tự hiện nút "Mở ở tab riêng" (URL `/exec` thật) nếu 12 giây không tải được.
`noindex` bằng meta + header `X-Robots-Tag` (`html/_headers`); `robots.txt` CỐ Ý không khai.

## IX. Checklist bug (đã gặp ở dự án này + đúc kết cùng playbook)

- **[ĐÃ GẶP 10/10/2026] Sửa tay 1 trang do `build_pages.py` sinh → lần build sau mất sạch.**
  Hotline phụ thêm tay vào `html/lien-he/index.html` bị `build_pages.py` xoá lại (script còn
  cố ý `re.sub` gỡ `hotline2`). CI chạy build mỗi lần CMS lưu → sửa tay kiểu này mất ngay lần
  lưu đầu. Né: tra bảng mục VIII trước khi sửa; sửa ở `build_pages.py`, rồi chạy build 2 lần
  phải ra `git status` sạch.
- **[ĐÃ GẶP 10/10/2026 khi test] Gõ Tiêu đề bài trong 1-2 giây đầu mở form → lỗi
  `Cannot read properties of undefined (reading 'select')`.** `EDITORS.post` được gán ngay trong
  `setup()` của TinyMCE, TRƯỚC khi init xong, nên `syncEditorAlts_` gọi `editor.dom` lúc chưa có.
  Vá: chỉ đồng bộ khi `editor.initialized`. (Bản mẫu xevip trong skill có cùng lỗi này.)
- **[ĐÃ GẶP 10/10/2026 khi test] Tiêu đề/mô tả bài có `<`, `&` làm vỡ HTML trang bài** — trước đây
  tiêu đề viết tay trong code nên không ai escape; giờ dữ liệu đến từ CMS. Vá: `text_fields()` trong
  `build_pages.py` escape `title`/`excerpt` (giữ nguyên dấu nháy để trang cũ không đổi byte).
- **[ĐÃ GẶP 10/10/2026 khi test] Gõ vào bảng giá vàng nổ lỗi JS, nút ↑ ↓ ✕ không chạy** — `attrJs_()`
  sinh literal bằng NHÁY KÉP, đặt trong thuộc tính `oninput="..."` (cũng nháy kép) làm cắt cụt thuộc
  tính. Quy tắc: thuộc tính handler có `attrJs_()` PHẢI bọc NHÁY ĐƠN (`onclick='fn(' + attrJs_(x) + ')'`).
- **[ĐÃ GẶP 10/10/2026 khi test] Rời tab "Cập nhật giá vàng" khi chưa lưu mà không được hỏi** —
  `isVisible_` chỉ đọc `style.display` inline, mà tab mở mặc định không có style inline. Đã đổi sang
  `getComputedStyle`.
- **Thẻ giá hiện khác giữa thẻ sản phẩm và khung Xem nhanh** → `price_html` (Python) và
  `priceHtml` (JS) lệch nhau. Sửa 1 chỗ phải sửa chỗ kia.
- **Form Liên hệ "gửi được" mà không có gì lưu** → mất rule `.hp-field`. Sau mỗi lần đổi
  `style.css`: `curl -s https://hieuvangngocdiep.vn/assets/css/style.css | grep -c hp-field` ≠ 0.
- **Sửa code, deploy đúng, F5 vẫn giao diện CŨ** → cache `appHtml`; đã có 2 lớp (mục VII).
  ⛔ Không bao giờ bảo khách tự xoá localStorage.
- **Trình soạn thảo trống/cao 0px** → init lúc tab còn ẩn, hoặc quên `tinymce.remove()` khi vẽ
  lại DOM. Khung lỗi đỏ `#fatal-error` + watchdog 10 giây hiện lỗi ra màn hình.
- **GitHub 422 "sha wasn't supplied"** khi ghi liên tiếp nhanh → retry-once + sleep 500ms.
- **`isNew` tính bằng độ truthy của id/slug** → sai; xác định bằng "đã có trong file chốt chưa".
- **CI trigger theo cả thư mục `scripts/data/**`** → build ở commit dở dang. Chỉ trigger 2 file chốt.
- **Sheets tự convert ngày** → luôn `Utilities.formatDate` khi đọc.
- **Đổi `let` → `const` khi dọn code** mà biến còn bị gán lại → `TypeError`.
- **Thêm tab mới mà revalidate ngầm truy cập DOM không null-safe** → kẹt giao diện cũ.
- **[ĐÃ GẶP 10/10/2026] Hàm `include` (không có `_`) gọi được từ trình duyệt** → ai cũng lấy được
  markup trang quản trị/mẫu mail mà chưa đăng nhập (lỗi có sẵn từ bản mẫu). Đổi thành `include_`:
  hàm tên có `_` cuối chỉ template phía máy chủ gọi được. Quy tắc: hàm nào không cho trình duyệt
  gọi thì PHẢI có `_` cuối tên.

## X. Script Properties (Project Settings > Script Properties) — TÊN CỐ ĐỊNH

- `GITHUB_TOKEN` — bắt buộc. Fine-grained PAT, repo `hieuvangngocdiep`, Contents: Read and write.
- `GITHUB_OWNER` — bắt buộc (`tranquanghuy-rightsvn`).
- `GITHUB_REPO` — bắt buộc (`hieuvangngocdiep`).
- `GITHUB_BRANCH` — bắt buộc (`master`).
- `NOTIFY_EMAIL` — địa chỉ nhận mail báo liên hệ mới, chủ dự án tự điền/đổi bất cứ lúc nào (không
  cần deploy lại). Trống = không gửi mail.
- `SPREADSHEET_ID` — KHÔNG cần điền, code tự tạo lần đầu và tự lưu lại.
