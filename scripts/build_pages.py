#!/usr/bin/env python3
"""Dựng các trang: /bang-gia/, /may-tinh-gia-vang/, /may-tinh-gia-bac/, /lien-he/, /tin-tuc/ và từng bài /tin-tuc/<slug>/.

Khung trang (head, header, menu, chat, nút nổi, drawer) lấy từ san-pham/index.html để mọi trang đồng bộ.
Khối bảng giá vàng / bạc lấy từ index.html (trang chủ).

Chạy lại sau khi sửa nội dung:  python3 scripts/build_pages.py && python3 scripts/bake_static.py
Thêm bài viết: thêm 1 mục vào POSTS (ảnh bìa đặt trong assets/img/news/, tỉ lệ 16:10).
"""
import html
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(REPO, 'html')  # thư mục web (được deploy)
read = lambda p: open(os.path.join(ROOT, p), encoding='utf-8').read()

SHOP = read('san-pham/index.html')
HOME = read('index.html')

# ---------------------------------------------------------------- khung trang
HEAD_END = SHOP.index('<body')
SPRITE_AND_HEADERS = SHOP[SHOP.index('>', HEAD_END) + 1: SHOP.index('    <!-- ============ DANH SÁCH SẢN PHẨM ============ -->')]
FOOTER = SHOP[SHOP.index('    <footer class="afooter">'): SHOP.index('  <!-- ============ LIVE CHAT PANEL')]
FOOTER = FOOTER.split('  <!-- ============ XEM NHANH')[0]  # khung xem nhanh chỉ cần ở trang có lưới sản phẩm
TAIL = SHOP[SHOP.index('  <!-- ============ LIVE CHAT PANEL'):]


def page(path, title, desc, main, active=None, og_image=None, page_id='page'):
    head = SHOP[:HEAD_END]
    head = re.sub(r'<title>.*?</title>', '<title>%s</title>' % html.escape(title), head)
    head = re.sub(r'(<meta name="description" content=")[^"]*', r'\g<1>' + html.escape(desc).replace('\\', r'\\'), head)
    head = re.sub(r'(<meta property="og:title" content=")[^"]*', r'\g<1>' + html.escape(title).replace('\\', r'\\'), head)
    head = re.sub(r'(<meta property="og:description" content=")[^"]*', r'\g<1>' + html.escape(desc).replace('\\', r'\\'), head)
    if og_image:
        head = re.sub(r'(<meta property="og:image" content=")[^"]*', r'\g<1>' + og_image, head)
    body = SPRITE_AND_HEADERS.replace('class="topnav__link dd__trigger is-active"', 'class="topnav__link dd__trigger"')
    if active:  # đánh dấu mục menu đang xem
        body = body.replace('<a href="%s" class="topnav__link">' % active, '<a href="%s" class="topnav__link is-active" aria-current="page">' % active)
    if 'class="tv-' in main:  # bài Smart content: nạp CSS các khối thiết kế
        head = head.replace('<link rel="stylesheet" href="/assets/css/style.css" />',
                            '<link rel="stylesheet" href="/assets/css/style.css" />\n  <link rel="stylesheet" href="/assets/css/blocks.css" />')
    out = head + '<body data-page="%s">' % page_id + body + main + '\n' + FOOTER + TAIL
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(out)
    print('  ✓', path)


def hero(crumbs, title_html, sub, cls=''):
    c = '<a href="/">Trang chủ</a>' + ''.join(
        '<span aria-hidden="true">/</span>' + ('<a href="%s">%s</a>' % (u, t) if u else '<span>%s</span>' % t) for t, u in crumbs)
    return '''      <section class="shop-hero %s">
        <div class="container">
          <nav class="crumb" aria-label="Đường dẫn">%s</nav>
          <h1 class="shop-hero__title">%s</h1>
          <p class="shop-hero__sub">%s</p>
        </div>
      </section>
''' % (cls, c, title_html, sub)


def section(src, start):
    i = src.index(start)
    j = src.index('</section>', i) + len('</section>')
    return src[i:j]


GOLD = section(HOME, '<section id="bang-gia"')
SILVER = section(HOME, '<section id="gia-bac"')


def calculator(metal):
    gold = metal == 'gold'
    name, unit = ('Vàng', 'Chỉ') if gold else ('Bạc', 'Chỉ')
    other = ('/may-tinh-gia-bac/', 'Máy tính giá bạc') if gold else ('/may-tinh-gia-vang/', 'Máy tính giá vàng')
    return '''    <section class="calc-sec" id="may-tinh">
      <div class="container calc-wrap">
        <div class="calc-head">
          <span class="calc-head__icon%(silver_cls)s"><svg class="i i-20" stroke-width="2"><use href="#i-calculator"/></svg></span>
          <h2 class="display-title"><span>Máy Tính Giá <span class="%(txt)s">%(name)s</span></span></h2>
          <p class="calc-head__sub">Tính nhanh giá trị mua vào / bán ra dựa theo bảng giá hiện tại</p>
        </div>
        <div class="calc%(silver_cls)s" data-calc="%(metal)s">
          <div class="calc-mode" role="group" aria-label="Loại giao dịch">
            <button type="button" class="calc-mode__btn is-on" data-mode="sell" aria-pressed="true"><b>Bán Ra</b><small>(Khách Hàng Mua)</small></button>
            <button type="button" class="calc-mode__btn" data-mode="buy" aria-pressed="false"><b>Mua Vào</b><small>(Khách Hàng Bán)</small></button>
          </div>
          <div class="calc-grid">
            <div class="calc-field calc-field--full">
              <label for="calc-type">Loại %(name)s</label>
              <div class="calc-select"><select id="calc-type"></select><svg class="i i-16" stroke-width="2"><use href="#i-chevron-down"/></svg></div>
            </div>
            <div class="calc-field">
              <label for="calc-weight">Khối Lượng %(name)s (%(unit)s)</label>
              <input id="calc-weight" type="text" inputmode="decimal" placeholder="Vd: 1,5" autocomplete="off" />
            </div>
            <div class="calc-field">
              <label for="calc-labor">Tiền Công (VNĐ)</label>
              <input id="calc-labor" type="text" inputmode="numeric" placeholder="Vd: 200.000" autocomplete="off" />
            </div>
            <div class="calc-field calc-field--full">
              <span class="calc-field__lbl">Đơn Giá (VNĐ / %(unit)s)</span>
              <div class="calc-unit" id="calc-unit">0 VNĐ</div>
            </div>
          </div>
          <div class="calc-sum">
            <div class="calc-sum__row"><span>Thành Tiền %(name)s</span><span id="calc-sub">0 VNĐ</span></div>
            <div class="calc-sum__row"><span>Tiền Công</span><span id="calc-labor-out">0 VNĐ</span></div>
            <div class="calc-sum__total"><span id="calc-total-lbl">Tổng Cộng</span><span id="calc-total">0 VNĐ</span></div>
          </div>
          <p class="calc-note">Kết quả chỉ mang tính tham khảo, giá thực tế được tính theo bảng giá niêm yết vào thời điểm giao dịch tại cửa hàng.</p>
        </div>
        <p class="calc-switch">Cần tính giá %(other_name)s? <a href="%(other_url)s">%(other_label)s <svg class="i i-16" stroke-width="2"><use href="#i-arrow-right"/></svg></a></p>
      </div>
    </section>
''' % dict(metal=metal, name=name, unit=unit, txt='gold-text' if gold else 'silver-text',
           silver_cls='' if gold else ' calc--silver', other_url=other[0], other_label=other[1],
           other_name='bạc' if gold else 'vàng')


TOOLS = '''    <section class="tools-sec">
      <div class="container">
        <div class="tools">
          <a href="/may-tinh-gia-vang/" class="tool">
            <span class="tool__icon"><svg class="i" stroke-width="1.75"><use href="#i-calculator"/></svg></span>
            <span class="tool__body"><b>Máy tính giá vàng</b><small>Tính nhanh giá trị mua vào / bán ra theo chỉ</small></span>
            <svg class="i i-20 tool__go" stroke-width="2"><use href="#i-arrow-right"/></svg>
          </a>
          <a href="/may-tinh-gia-bac/" class="tool tool--silver">
            <span class="tool__icon"><svg class="i" stroke-width="1.75"><use href="#i-coins"/></svg></span>
            <span class="tool__body"><b>Máy tính giá bạc</b><small>Tính nhanh giá trị trang sức bạc theo chỉ</small></span>
            <svg class="i i-20 tool__go" stroke-width="2"><use href="#i-arrow-right"/></svg>
          </a>
        </div>
      </div>
    </section>
'''

# ---------------------------------------------------------------- tin tức
CATS = {'cua-hang': 'Tin cửa hàng', 'kien-thuc': 'Kiến thức', 'cam-nang': 'Cẩm nang', 'san-pham': 'Sản phẩm mới'}

POSTS = [
    dict(slug='bo-suu-tap-qua-tang-vang-phong-thuy', cat='san-pham', date='03/10/2026', cover='qua-tang-vang.jpg',
         title='Bộ sưu tập quà tặng vàng phong thuỷ: Thần Tài, Tài Thần cưỡi ngựa, Di Lặc…',
         excerpt='Những linh vật vàng đặt trong hộp mica "Chiêu Tài Tiến Bảo" — món quà khai trương, tân gia, mừng thọ vừa sang trọng vừa mang lời chúc tài lộc.',
         body='''
<p>Bên cạnh trang sức, <strong>quà tặng vàng phong thuỷ</strong> đang là lựa chọn được nhiều Quý khách tìm đến tại Hiệu Vàng Ngọc Diệp. Mỗi linh vật được đặt trong hộp mica trong suốt có đế đỏ in chữ "Chiêu Tài Tiến Bảo", thắt nơ sẵn — mang đi tặng ngay mà không cần gói thêm.</p>
<h2>Các mẫu đang có tại cửa hàng</h2>
<ul>
  <li><strong>Tượng Thần Tài, Ông Địa</strong> — cặp đôi quen thuộc đặt bàn thờ, quầy thu ngân để cầu buôn may bán đắt.</li>
  <li><strong>Tài Thần cưỡi ngựa</strong> — mang ý nghĩa "mã đáo thành công", hợp làm quà khai trương.</li>
  <li><strong>Tượng Di Lặc</strong> — tượng trưng cho niềm vui, sự an lạc của gia chủ.</li>
  <li><strong>Linh vật 12 con giáp</strong>: rồng, rắn, ngựa, heo… — quà tặng theo tuổi rất được ưa chuộng.</li>
  <li><strong>Cây tài lộc, nén vàng, hồ lô</strong> — vật phẩm phong thuỷ nhỏ gọn đặt bàn làm việc.</li>
</ul>
<blockquote>Mẹo nhỏ: chọn linh vật theo tuổi hoặc theo mong muốn của người nhận (tài lộc, bình an, sức khoẻ) để món quà thêm ý nghĩa.</blockquote>
<h2>Gợi ý chọn quà theo dịp</h2>
<p><strong>Khai trương:</strong> Tài Thần cưỡi ngựa, Thần Tài – Ông Địa. <strong>Tân gia:</strong> hồ lô, cây tài lộc. <strong>Mừng thọ:</strong> Di Lặc, nén vàng. <strong>Sinh nhật:</strong> linh vật theo tuổi.</p>
<p>Quý khách có thể xem thêm các mẫu tại mục <a href="/san-pham/?cat=qua-tang">Quà Tặng Vàng</a> hoặc ghé trực tiếp cửa hàng để chọn mẫu ưng ý.</p>
'''),
    dict(slug='gia-cong-trang-suc-vang-bac-theo-yeu-cau', cat='san-pham', date='01/10/2026', cover='gia-cong-trang-suc.jpg',
         title='Gia công trang sức vàng bạc theo yêu cầu — biến ý tưởng thành món trang sức riêng',
         excerpt='Muốn một chiếc nhẫn khắc tên, bộ trang sức cưới theo mẫu riêng hay làm mới món đồ cũ? Hiệu Vàng Ngọc Diệp nhận gia công trang sức vàng bạc theo yêu cầu.',
         body='''
<p>Bên cạnh mua bán vàng 24K – 18K, <strong>gia công trang sức vàng bạc</strong> là dịch vụ mà Hiệu Vàng Ngọc Diệp đã gắn bó từ những ngày đầu. Với hơn 40 năm kinh nghiệm, chúng tôi giúp Quý khách sở hữu món trang sức mang dấu ấn riêng.</p>
<h2>Những yêu cầu thường gặp</h2>
<ul>
  <li><strong>Nhẫn cưới, nhẫn đôi khắc tên</strong> hoặc ngày kỷ niệm.</li>
  <li><strong>Trang sức cưới theo mẫu riêng</strong>: dây cổ, vòng, mặt khoá theo ý gia đình.</li>
  <li><strong>Làm mới, sửa chữa</strong>: nối dây, thay khoá, chỉnh size nhẫn, đánh bóng.</li>
  <li><strong>Đổi kiểu</strong> từ vàng cũ sang mẫu mới hợp xu hướng.</li>
</ul>
<h2>Quy trình đơn giản</h2>
<ol>
  <li><strong>Tư vấn:</strong> Quý khách mang mẫu tham khảo hoặc ý tưởng đến cửa hàng, hoặc gửi ảnh qua Zalo.</li>
  <li><strong>Báo giá:</strong> cửa hàng tư vấn loại vàng, trọng lượng dự kiến, tiền công và thời gian hoàn thành.</li>
  <li><strong>Chế tác:</strong> thợ kim hoàn thực hiện và cập nhật tiến độ khi cần.</li>
  <li><strong>Nhận hàng:</strong> kiểm tra sản phẩm, cân trọng lượng thực tế và thanh toán.</li>
</ol>
<blockquote>Gửi ảnh mẫu qua <a href="https://zalo.me/0905887044" target="_blank" rel="noopener noreferrer">Zalo 0905 887 044</a> để được tư vấn và báo giá nhanh nhất.</blockquote>
'''),
    dict(slug='bac-999-va-bac-925-khac-nhau-the-nao', cat='kien-thuc', date='30/09/2026', cover='bac-999-bac-925.jpg',
         title='Bạc 999 và bạc 925 khác nhau thế nào? Nên chọn loại nào?',
         excerpt='Cùng là bạc nhưng bạc 999 và bạc 925 khác nhau về độ tinh khiết, độ cứng và mục đích sử dụng. Đây là cách chọn đúng loại cho nhu cầu của bạn.',
         body='''
<p>Khi mua bạc, Quý khách thường gặp hai cách gọi phổ biến: <strong>bạc 999</strong> và <strong>bạc 925</strong>. Con số thể hiện hàm lượng bạc nguyên chất trên 1.000 phần.</p>
<h2>Bạc 999 (bạc nguyên chất)</h2>
<p>Chứa khoảng <strong>99,9% bạc</strong>. Màu trắng sáng, mềm và dễ trầy. Bạc 999 thường được làm thành <strong>bạc miếng, bạc thỏi, đồng bạc</strong> để tích trữ, hoặc các món mỹ nghệ ít va chạm.</p>
<h2>Bạc 925 (bạc Ý / sterling silver)</h2>
<p>Gồm <strong>92,5% bạc</strong> và 7,5% kim loại khác (thường là đồng) giúp bạc cứng hơn, giữ dáng tốt. Đây là chất liệu phổ biến nhất cho <strong>dây chuyền, lắc tay, nhẫn, bông tai</strong> đeo hằng ngày.</p>
<h2>Nên chọn loại nào?</h2>
<ul>
  <li><strong>Tích trữ, đầu tư:</strong> chọn bạc 999 dạng miếng, thỏi — giá bám sát giá bạc thị trường.</li>
  <li><strong>Đeo hằng ngày:</strong> chọn trang sức bạc 925 — bền, nhiều kiểu dáng.</li>
</ul>
<blockquote>Xem giá bạc trang sức tham khảo trong ngày tại trang <a href="/bang-gia/#gia-bac">Bảng giá</a> hoặc tính nhanh bằng <a href="/may-tinh-gia-bac/">máy tính giá bạc</a>.</blockquote>
'''),
    dict(slug='cach-bao-quan-trang-suc-vang-bac-luon-sang-bong', cat='kien-thuc', date='25/09/2026', cover='bao-quan-trang-suc.jpg',
         title='7 cách bảo quản trang sức vàng, bạc luôn sáng bóng như mới',
         excerpt='Vài thói quen nhỏ giúp trang sức giữ được độ sáng và bền đẹp theo năm tháng — từ cách đeo, cách cất đến cách làm sạch tại nhà.',
         body='''
<p>Trang sức vàng, bạc theo thời gian có thể bị xỉn màu do mồ hôi, mỹ phẩm hay hoá chất. Chỉ với vài thói quen đơn giản, món trang sức của bạn sẽ luôn sáng bóng.</p>
<h2>Khi đeo</h2>
<ol>
  <li><strong>Tháo trang sức khi tắm, bơi, làm việc nhà</strong> — xà phòng, nước tẩy, nước biển và nước hồ bơi dễ làm xỉn màu.</li>
  <li><strong>Xịt nước hoa, thoa kem trước rồi mới đeo</strong> trang sức để hạn chế hoá chất bám lên bề mặt.</li>
  <li><strong>Tháo ra khi ngủ, tập thể thao</strong> để tránh móp, đứt dây.</li>
</ol>
<h2>Khi cất giữ</h2>
<ol start="4">
  <li><strong>Cất riêng từng món</strong> trong túi vải hoặc hộp có ngăn, tránh cọ xát gây trầy.</li>
  <li><strong>Để nơi khô ráo</strong>; với bạc, có thể cho thêm gói hút ẩm để hạn chế xỉn đen.</li>
</ol>
<h2>Khi làm sạch</h2>
<ol start="6">
  <li><strong>Ngâm nước ấm pha chút xà phòng dịu nhẹ</strong> 10–15 phút, chải nhẹ bằng bàn chải lông mềm, rửa sạch và lau khô bằng khăn mềm.</li>
  <li><strong>Mang đến cửa hàng để đánh bóng, làm mới</strong> định kỳ — đặc biệt với trang sức đính đá hoặc có chi tiết nhỏ.</li>
</ol>
<blockquote>Hiệu Vàng Ngọc Diệp nhận làm sạch, đánh bóng và gia công sửa chữa trang sức vàng bạc. Liên hệ <a href="tel:0905887044">0905 887 044</a> để được tư vấn.</blockquote>
'''),
    dict(slug='phan-biet-vang-9999-vang-98-vang-610', cat='kien-thuc', date='20/09/2026', cover='phan-biet-tuoi-vang.jpg',
         title='Phân biệt vàng 9999, vàng 98, vàng 96 và vàng 610 — tuổi vàng là gì?',
         excerpt='"Tuổi vàng" cho biết hàm lượng vàng nguyên chất trong sản phẩm. Hiểu đúng giúp bạn chọn mua phù hợp, dù để tích trữ hay làm trang sức.',
         body='''
<p>Khi xem bảng giá, Quý khách sẽ thấy nhiều loại: vàng 9999, 98, 96, nữ trang 98, 610… Tất cả đều nói về <strong>tuổi vàng</strong> — tỉ lệ vàng nguyên chất có trong sản phẩm.</p>
<h2>Các loại vàng phổ biến</h2>
<ul>
  <li><strong>Vàng 9999 (24K):</strong> 99,99% vàng nguyên chất, màu vàng đậm, mềm. Phù hợp <strong>tích trữ</strong>: nhẫn tròn trơn, vàng ép vỉ, đồng vàng.</li>
  <li><strong>Vàng 98, vàng 96:</strong> 98% và 96% vàng, cứng hơn 9999 một chút, thường dùng cho nhẫn, vòng, trang sức cưới truyền thống.</li>
  <li><strong>Vàng 750 (18K):</strong> 75% vàng, độ cứng tốt, giữ chi tiết đẹp — hay dùng cho trang sức đính đá.</li>
  <li><strong>Vàng 610 (vàng tây, ~14,6K):</strong> 61% vàng, cứng, màu sắc đa dạng, giá mềm — phù hợp trang sức thời trang đeo hằng ngày.</li>
</ul>
<h2>Nên chọn loại nào?</h2>
<p>Nếu mục tiêu là <strong>tích luỹ tài sản</strong>, hãy ưu tiên vàng 9999 vì dễ mua bán lại, ít hao hụt. Nếu cần <strong>trang sức đẹp, bền</strong> để đeo hằng ngày, vàng 18K hoặc 610 là lựa chọn hợp lý.</p>
<blockquote>Giá từng loại vàng được cập nhật tại trang <a href="/bang-gia/">Bảng giá</a>. Bạn cũng có thể dùng <a href="/may-tinh-gia-vang/">máy tính giá vàng</a> để ước tính số tiền nhanh chóng.</blockquote>
'''),
    dict(slug='cach-doc-bang-gia-vang-mua-vao-ban-ra', cat='kien-thuc', date='18/09/2026', cover='doc-bang-gia.jpg',
         title='Cách đọc bảng giá vàng: "mua vào", "bán ra" nghĩa là gì?',
         excerpt='Giá mua vào và bán ra trên bảng giá được tính từ phía cửa hàng. Hiểu đúng giúp Quý khách biết mình sẽ trả bao nhiêu khi mua và nhận bao nhiêu khi bán.',
         body='''
<p>Mỗi ngày, bảng giá vàng tại cửa hàng hiển thị hai cột: <strong>Mua vào</strong> và <strong>Bán ra</strong>. Nhiều Quý khách vẫn hay nhầm lẫn hai con số này.</p>
<h2>Hiểu theo góc nhìn của cửa hàng</h2>
<ul>
  <li><strong>Bán ra (Khách hàng mua):</strong> giá cửa hàng bán cho Quý khách. Đây là số tiền Quý khách trả khi mua vàng.</li>
  <li><strong>Mua vào (Khách hàng bán):</strong> giá cửa hàng mua lại từ Quý khách. Đây là số tiền Quý khách nhận được khi bán vàng.</li>
</ul>
<p>Giá bán ra luôn cao hơn giá mua vào một khoản gọi là <strong>chênh lệch mua – bán</strong>, bù cho chi phí vận hành và biến động thị trường.</p>
<h2>Đơn vị tính</h2>
<p>Giá vàng thường niêm yết theo <strong>chỉ</strong> (1 chỉ = 3,75 gram; 10 chỉ = 1 lượng). Giá bạc thường niêm yết theo <strong>lượng</strong> hoặc <strong>kg</strong>.</p>
<h2>Với trang sức</h2>
<p>Khi mua trang sức, tổng số tiền = <strong>giá vàng × trọng lượng + tiền công</strong> chế tác. Khi bán lại, cửa hàng thường tính theo giá mua vào của tuổi vàng tương ứng.</p>
<blockquote>Thử ngay <a href="/may-tinh-gia-vang/">máy tính giá vàng</a> để ước tính số tiền khi mua hoặc bán.</blockquote>
'''),
    dict(slug='kinh-nghiem-chon-trang-suc-cuoi-cho-co-dau', cat='cam-nang', date='15/09/2026', cover='trang-suc-cuoi.jpg',
         title='Kinh nghiệm chọn trang sức cưới cho cô dâu: đủ lễ, đẹp và hợp túi tiền',
         excerpt='Dây cổ cưới, vòng cưới, mặt khoá, nhẫn cưới… nên chuẩn bị những gì và chọn thế nào cho vừa đẹp vừa ý nghĩa? Cùng Ngọc Diệp điểm qua vài kinh nghiệm.',
         body='''
<p>Trang sức cưới không chỉ để làm đẹp mà còn là <strong>của hồi môn</strong>, là lời chúc của hai bên gia đình dành cho đôi uyên ương. Dưới đây là vài kinh nghiệm giúp cô dâu chuẩn bị chu đáo.</p>
<h2>Bộ trang sức cưới thường gồm</h2>
<ul>
  <li><strong>Dây cổ cưới</strong> (dây chuyền nhiều tầng, mặt heo, phượng, mây cát tường) — điểm nhấn của bộ trang sức.</li>
  <li><strong>Vòng tay cưới / vòng ximen</strong> — thường được mẹ chồng trao cho con dâu trong lễ rước dâu.</li>
  <li><strong>Mặt khoá, bông tai, nhẫn cưới</strong> — hoàn thiện bộ trang sức.</li>
</ul>
<h2>Chọn thế nào cho hợp?</h2>
<ol>
  <li><strong>Theo dáng người:</strong> cô dâu cổ cao, vai nhỏ hợp dây cổ nhiều tầng; cổ ngắn nên chọn kiểu thanh, ít tầng.</li>
  <li><strong>Theo trang phục:</strong> áo dài cổ cao hợp dây dài, mặt to; váy cưới cổ khoét hợp dây mảnh, mặt nhỏ.</li>
  <li><strong>Theo ngân sách:</strong> xác định trước tổng số chỉ vàng dự kiến để cửa hàng tư vấn mẫu phù hợp.</li>
  <li><strong>Đặt trước 2–4 tuần</strong> nếu muốn gia công theo mẫu riêng hoặc khắc tên.</li>
</ol>
<blockquote>Xem các mẫu dây cổ cưới, vòng cưới, mặt khoá thật tại mục <a href="/san-pham/?cat=trang-suc-cuoi">Trang Sức Cưới</a>.</blockquote>
'''),
    dict(slug='thong-bao-nghi-le-quoc-khanh-2-9-2026', cat='cua-hang', date='28/08/2026', cover='nghi-le-quoc-khanh-2-9.jpg',
         title='Thông báo nghỉ lễ Quốc khánh 2/9/2026',
         excerpt='Hiệu Vàng Ngọc Diệp nghỉ ngày 2/9/2026 và hoạt động lại bình thường từ ngày 3/9/2026. Kính chúc Quý khách có kỳ nghỉ lễ vui vẻ!',
         body='''
<p>Nhân dịp kỷ niệm Quốc khánh nước Cộng hoà Xã hội Chủ nghĩa Việt Nam, Hiệu Vàng Ngọc Diệp xin trân trọng thông báo lịch nghỉ lễ:</p>
<ul>
  <li><strong>Ngày 2/9/2026:</strong> cửa hàng <strong>nghỉ</strong>.</li>
  <li><strong>Ngày 3/9/2026:</strong> hoạt động lại bình thường.</li>
</ul>
<p>Trong thời gian nghỉ lễ, Quý khách vẫn có thể nhắn tin qua <a href="https://zalo.me/0905887044" target="_blank" rel="noopener noreferrer">Zalo 0905 887 044</a> hoặc fanpage, chúng tôi sẽ phản hồi ngay khi mở cửa trở lại.</p>
<blockquote>Kính chúc Quý khách có kỳ nghỉ lễ vui vẻ! Xin chân thành cảm ơn!</blockquote>
'''),
    dict(slug='thong-bao-lich-nghi-thang-6-2026', cat='cua-hang', date='01/06/2026', cover='lich-nghi-thang-6.jpg',
         title='Thông báo lịch nghỉ ngày 5, 6, 7/6/2026',
         excerpt='Hiệu Vàng Ngọc Diệp nghỉ 3 ngày 5/6, 6/6 và 7/6/2026, mở cửa lại vào thứ Hai ngày 8/6/2026. Hẹn gặp lại Quý khách!',
         body='''
<p>Hiệu Vàng Ngọc Diệp xin thông báo lịch nghỉ của cửa hàng như sau:</p>
<ul>
  <li><strong>Nghỉ:</strong> ngày 5/6, 6/6 và 7/6/2026.</li>
  <li><strong>Mở cửa lại:</strong> thứ Hai, ngày 8/6/2026.</li>
</ul>
<p>Mong Quý khách thông cảm và sắp xếp thời gian giao dịch phù hợp. Mọi nhu cầu tư vấn vui lòng nhắn tin qua <a href="https://zalo.me/0905887044" target="_blank" rel="noopener noreferrer">Zalo 0905 887 044</a>.</p>
<blockquote>Hẹn gặp lại Quý khách! Xin cảm ơn!</blockquote>
'''),
    dict(slug='mua-vang-ngay-via-than-tai-nen-chon-gi', cat='cam-nang', date='05/02/2026', cover='via-than-tai.jpg',
         title='Mua vàng ngày vía Thần Tài: nên chọn loại nào để vừa may mắn vừa giữ giá?',
         excerpt='Ngày mùng 10 tháng Giêng, nhiều người mua vàng để cầu tài lộc. Đâu là lựa chọn vừa ý nghĩa, vừa dễ tích luỹ?',
         body='''
<p>Theo quan niệm dân gian, <strong>ngày vía Thần Tài (mùng 10 tháng Giêng âm lịch)</strong> mua một chút vàng sẽ mang lại may mắn, tài lộc cả năm. Vậy nên mua gì?</p>
<h2>Gợi ý các lựa chọn</h2>
<ul>
  <li><strong>Vàng ép vỉ Thần Tài 999.9:</strong> nhỏ gọn, ý nghĩa, phù hợp làm quà hoặc để dành.</li>
  <li><strong>Nhẫn tròn trơn 24K:</strong> dễ mua bán lại, phù hợp tích luỹ dài hạn.</li>
  <li><strong>Đồng vàng, vàng hoa mai:</strong> đẹp mắt, thích hợp lì xì, tặng người thân.</li>
</ul>
<h2>Lưu ý khi mua</h2>
<ol>
  <li><strong>Mua vừa sức</strong> — ý nghĩa nằm ở sự may mắn, không cần mua nhiều.</li>
  <li><strong>Chọn cửa hàng uy tín</strong>, có tem nhãn, hoá đơn rõ ràng.</li>
  <li><strong>Đi sớm hoặc đặt trước</strong> vì ngày vía Thần Tài thường rất đông khách.</li>
</ol>
<blockquote>Xem các mẫu vàng tích trữ tại mục <a href="/san-pham/?cat=vang-tich-tru">Vàng Tích Trữ</a> và theo dõi giá tại trang <a href="/bang-gia/">Bảng giá</a>.</blockquote>
'''),
]

# Bài Smart content: thân bài thiết kế sẵn (khối tv-) ở scripts/content/tin-tuc/<slug>.html, thay cho body trong POSTS
SMART_DIR = os.path.join(REPO, 'scripts', 'content', 'tin-tuc')  # bản đã duyệt; bản nháp để ở content/_drafts/
for _p in POSTS:
    _f = os.path.join(SMART_DIR, _p['slug'] + '.html')
    if os.path.exists(_f):
        _p['body'] = open(_f, encoding='utf-8').read()
        _p['smart'] = True


def reading_time(body):
    words = len(re.sub(r'<[^>]+>', ' ', body).split())
    return max(1, round(words / 200))


def post_card(p, cls='ncard'):
    return '''          <article class="%(cls)s" data-cat="%(cat)s">
            <a href="/tin-tuc/%(slug)s/" class="ncard__media"><img src="/assets/img/news/%(cover)s" alt="%(alt)s" loading="lazy" width="1200" height="750" /></a>
            <div class="ncard__body">
              <div class="ncard__meta"><span class="ncat ncat--%(cat)s">%(catname)s</span><span class="ncard__date"><svg class="i i-16" stroke-width="2"><use href="#i-calendar"/></svg>%(date)s</span></div>
              <h3 class="ncard__title"><a href="/tin-tuc/%(slug)s/">%(title)s</a></h3>
              <p class="ncard__excerpt">%(excerpt)s</p>
              <a href="/tin-tuc/%(slug)s/" class="ncard__more">Đọc tiếp <svg class="i i-16" stroke-width="2"><use href="#i-arrow-right"/></svg></a>
            </div>
          </article>
''' % dict(p, cls=cls, catname=CATS[p['cat']], alt=html.escape(p['title']))


POST_CTA = '''          <aside class="post-cta">
            <img src="/assets/img/logo-mark.png" alt="" width="408" height="288" />
            <div class="post-cta__body">
              <b>Cần tư vấn thêm?</b>
              <p>Đội ngũ Hiệu Vàng Ngọc Diệp luôn sẵn sàng hỗ trợ Quý khách — 94-96 Lý Thái Tổ, Thanh Khê, Đà Nẵng.</p>
            </div>
            <div class="post-cta__actions">
              <a href="tel:0905887044" class="btn-gold"><svg class="i i-16" stroke-width="2"><use href="#i-phone"/></svg>&nbsp;0905 887 044</a>
              <button type="button" class="btn-outline js-open-chat">Nhắn tin tư vấn</button>
            </div>
          </aside>
'''


def build_news():
    feat, rest = POSTS[0], POSTS[1:]
    chips = '<button type="button" class="chip is-on" data-cat="" aria-pressed="true">Tất cả</button>' + ''.join(
        '<button type="button" class="chip" data-cat="%s" aria-pressed="false">%s</button>' % (k, v)
        for k, v in CATS.items() if any(x['cat'] == k for x in POSTS))
    main = '''    <main class="news-page">
%s      <div class="container news-body">
        <div class="chips chips--scroll news-chips" id="news-chips" role="toolbar" aria-label="Chuyên mục">%s</div>
        <div class="news-list" id="news-list">
%s%s        </div>
        <p class="news-empty" id="news-empty" hidden>Chưa có bài viết trong chuyên mục này.</p>
      </div>
    </main>
''' % (hero([('Tin tức', None)], 'Tin Tức <span class="gold-text">&amp; Cẩm Nang</span>',
             'Thông báo từ cửa hàng, kiến thức vàng bạc và kinh nghiệm chọn trang sức từ Hiệu Vàng Ngọc Diệp.'),
       chips, post_card(feat, 'ncard ncard--feat'), ''.join(post_card(p) for p in rest))
    page('tin-tuc/index.html', 'Tin Tức | Hiệu Vàng Ngọc Diệp',
         'Thông báo, kiến thức vàng bạc và cẩm nang chọn trang sức từ Hiệu Vàng Ngọc Diệp – 94-96 Lý Thái Tổ, Đà Nẵng.',
         main, active='/tin-tuc/', page_id='news')

    for p in POSTS:
        related = [x for x in POSTS if x is not p and x['cat'] == p['cat']] + [x for x in POSTS if x is not p and x['cat'] != p['cat']]
        main = '''    <main class="post-page">
      <article class="post">
        <header class="post__head container">
          <nav class="crumb" aria-label="Đường dẫn"><a href="/">Trang chủ</a><span aria-hidden="true">/</span><a href="/tin-tuc/">Tin tức</a><span aria-hidden="true">/</span><span>%(catname)s</span></nav>
          <span class="ncat ncat--%(cat)s">%(catname)s</span>
          <h1 class="post__title">%(title)s</h1>
          <p class="post__lead">%(excerpt)s</p>
          <div class="post__meta">
            <span class="post__author"><img src="/assets/img/logo-mark.png" alt="" width="408" height="288" />Hiệu Vàng Ngọc Diệp</span>
            <span><svg class="i i-16" stroke-width="2"><use href="#i-calendar"/></svg>%(date)s</span>
            <span><svg class="i i-16" stroke-width="2"><use href="#i-clock"/></svg>%(rt)s phút đọc</span>
          </div>
        </header>
        <figure class="post__cover container"><img src="/assets/img/news/%(cover)s" alt="%(alt)s" width="1200" height="750" /></figure>
        <div class="post__content">
%(body)s
          <div class="post__share">
            <span>Chia sẻ bài viết</span>
            <a class="share-btn js-share-fb" href="https://www.facebook.com/sharer/sharer.php" target="_blank" rel="noopener noreferrer" aria-label="Chia sẻ lên Facebook"><svg class="i i-18" stroke-width="2"><use href="#i-facebook"/></svg></a>
            <button type="button" class="share-btn js-copy-link" aria-label="Sao chép liên kết"><svg class="i i-18" stroke-width="2"><use href="#i-link"/></svg></button>
          </div>
%(cta)s        </div>
      </article>
      <section class="post-related">
        <div class="container">
          <div class="post-related__head"><h2 class="display-title"><span>Bài Viết <span class="gold-text">Liên Quan</span></span></h2><a href="/tin-tuc/" class="see-all">Xem tất cả <svg class="i i-16" stroke-width="2"><use href="#i-arrow-right"/></svg></a></div>
          <div class="news-grid">
%(related)s          </div>
        </div>
      </section>
    </main>
''' % dict(p, catname=CATS[p['cat']], alt=html.escape(p['title']), rt=reading_time(p['body']),
           body='\n'.join('          ' + l if l.strip() else '' for l in p['body'].strip().split('\n')),
           related=''.join(post_card(x) for x in related[:3]),
           cta='' if p.get('smart') else POST_CTA)
        page('tin-tuc/%s/index.html' % p['slug'], '%s | Hiệu Vàng Ngọc Diệp' % p['title'], p['excerpt'], main,
             active='/tin-tuc/', og_image='/assets/img/news/' + p['cover'], page_id='post')


def build_prices():
    main = '''    <main class="price-page">
%s%s
%s
%s    </main>
''' % (hero([('Bảng giá', None)], 'Bảng Giá <span class="gold-text">Vàng</span> &amp; <span class="silver-text">Bạc</span>',
             'Giá vàng, bạc tham khảo cập nhật mỗi khi tải trang. Giá giao dịch thực tế theo bảng niêm yết tại cửa hàng.', 'shop-hero--compact'),
       GOLD, SILVER, TOOLS)
    page('bang-gia/index.html', 'Bảng Giá Vàng & Bạc Hôm Nay | Hiệu Vàng Ngọc Diệp',
         'Bảng giá vàng 9999, 98, 96, nữ trang 98, 610 và giá bạc trang sức hôm nay tại Hiệu Vàng Ngọc Diệp – Đà Nẵng.',
         main, active='/bang-gia/', page_id='prices')

    main = '''    <main class="price-page">
%s%s
%s    </main>
''' % (hero([('Bảng giá', '/bang-gia/'), ('Máy tính giá vàng', None)], 'Máy Tính Giá <span class="gold-text">Vàng</span>',
             'Xem bảng giá vàng hôm nay và tính nhanh số tiền khi mua, bán vàng.', 'shop-hero--compact'),
       GOLD, calculator('gold'))
    page('may-tinh-gia-vang/index.html', 'Máy Tính Giá Vàng | Hiệu Vàng Ngọc Diệp',
         'Tính nhanh giá trị mua vào, bán ra vàng 9999, 98, 96, 610 theo bảng giá hiện tại tại Hiệu Vàng Ngọc Diệp.',
         main, page_id='calc')

    main = '''    <main class="price-page">
%s%s
%s    </main>
''' % (hero([('Bảng giá', '/bang-gia/'), ('Máy tính giá bạc', None)], 'Máy Tính Giá <span class="silver-text">Bạc</span>',
             'Xem giá bạc trang sức hôm nay và tính nhanh số tiền khi mua, bán trang sức bạc.', 'shop-hero--compact'),
       SILVER, calculator('silver'))
    page('may-tinh-gia-bac/index.html', 'Máy Tính Giá Bạc | Hiệu Vàng Ngọc Diệp',
         'Tính nhanh giá trị mua vào, bán ra trang sức bạc 925, bạc ta theo bảng giá hiện tại tại Hiệu Vàng Ngọc Diệp.',
         main, page_id='calc')


# ---------------------------------------------------------------- liên hệ
MAP_Q = '94-96 Lý Thái Tổ, Thanh Khê, Đà Nẵng'


def build_contact():
    from urllib.parse import quote_plus
    cards = HOME[HOME.index('<div class="contact-grid">'): HOME.index('<div class="footer__bottom">')].rstrip()
    cards = cards[:cards.rindex('</div>') + len('</div>')]
    cards = re.sub(r'<br />\s*<a [^>]*data-contact="hotline2"[^>]*>.*?</a>', '', cards)  # số phụ chỉ hiện ở footer trang chủ
    main = '''    <main class="contact-page">
%(hero)s      <div class="container contact-body">
        <div class="contact-quick">
          <a href="#" data-contact-link="hotline" class="cq"><span class="cq__icon"><svg class="i i-20" stroke-width="2"><use href="#i-phone-call"/></svg></span><span><b>Gọi ngay</b><small data-contact="hotline">0905 887 044</small></span></a>
          <a href="#" data-contact-link="zalo" class="cq"><span class="cq__icon cq__icon--zalo"><svg width="28" height="28" aria-hidden="true"><use href="#i-zalo"/></svg></span><span><b>Nhắn Zalo</b><small>Phản hồi nhanh trong giờ mở cửa</small></span></a>
          <a href="#" data-contact-link="address" class="cq"><span class="cq__icon"><svg class="i i-20" stroke-width="2"><use href="#i-map-pin"/></svg></span><span><b>Chỉ đường</b><small>Mở Google Maps</small></span></a>
          <a href="#" data-contact-link="facebook" class="cq"><span class="cq__icon"><svg class="i i-20" stroke-width="2"><use href="#i-facebook"/></svg></span><span><b>Fanpage</b><small>Cập nhật mẫu mới mỗi ngày</small></span></a>
        </div>

        <div class="contact-main">
          <section class="contact-info" aria-labelledby="ct-info">
            <h2 class="contact-h" id="ct-info">Thông Tin <span class="gold-text">Cửa Hàng</span></h2>
            <p class="contact-lead">Hiệu Vàng Ngọc Diệp — Since 1990. Chuyên mua bán vàng 24K – 18K, gia công trang sức vàng bạc. Rất hân hạnh được đón tiếp Quý khách.</p>
            %(cards)s
          </section>

          <section class="contact-form-card" aria-labelledby="ct-form">
            <h2 class="contact-h" id="ct-form">Gửi Yêu Cầu <span class="gold-text">Tư Vấn</span></h2>
            <p class="contact-lead">Để lại thông tin, nhân viên Ngọc Diệp sẽ gọi lại cho Quý khách trong thời gian sớm nhất.</p>
            <form class="cform" id="contact-form" novalidate>
              <div class="cform__row">
                <div class="calc-field"><label for="cf-name">Họ và tên *</label><input id="cf-name" type="text" placeholder="Nguyễn Văn A" autocomplete="name" required /></div>
                <div class="calc-field"><label for="cf-phone">Số điện thoại *</label><input id="cf-phone" type="tel" inputmode="tel" placeholder="09xxxxxxxx" autocomplete="tel" required /></div>
              </div>
              <div class="calc-field">
                <label for="cf-need">Nhu cầu</label>
                <div class="calc-select"><select id="cf-need">
                  <option>Mua vàng / trang sức</option><option>Bán lại vàng</option><option>Gia công trang sức theo yêu cầu</option>
                  <option>Tư vấn trang sức cưới</option><option>Quà tặng vàng phong thuỷ</option><option>Khác</option>
                </select><svg class="i i-16" stroke-width="2"><use href="#i-chevron-down"/></svg></div>
              </div>
              <div class="calc-field"><label for="cf-msg">Nội dung</label><textarea id="cf-msg" rows="4" placeholder="Mẫu trang sức, trọng lượng, thời gian mong muốn…"></textarea></div>
              <p class="cform__err" id="cf-err" hidden></p>
              <button type="submit" class="btn-gold cform__submit"><svg class="i i-16" stroke-width="2"><use href="#i-send"/></svg>&nbsp;Gửi yêu cầu</button>
              <p class="cform__note">Thông tin của Quý khách chỉ dùng để liên hệ tư vấn, không chia sẻ cho bên thứ ba.</p>
            </form>
            <div class="cform-done" id="contact-done" hidden>
              <span class="cform-done__icon"><svg class="i i-20" stroke-width="2.5"><use href="#i-check"/></svg></span>
              <b>Đã gửi yêu cầu!</b>
              <p>Cảm ơn <span id="cf-done-name"></span>. Nhân viên Hiệu Vàng Ngọc Diệp sẽ liên hệ lại qua số <span id="cf-done-phone"></span> trong thời gian sớm nhất.</p>
              <button type="button" class="btn-outline" id="cf-again">Gửi yêu cầu khác</button>
            </div>
          </section>
        </div>

        <section class="contact-map" aria-label="Bản đồ đường đi">
          <iframe title="Bản đồ Hiệu Vàng Ngọc Diệp – %(mapq)s" src="https://www.google.com/maps?q=%(mapenc)s&amp;output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
        </section>
      </div>
    </main>
''' % dict(hero=hero([('Liên hệ', None)], 'Liên Hệ <span class="gold-text">Ngọc Diệp</span>',
                        '94-96 Lý Thái Tổ, phường Thanh Khê, TP. Đà Nẵng · Mở cửa 7h00 – 21h00 tất cả các ngày trong tuần.', 'shop-hero--compact'),
              cards=cards, mapq=MAP_Q, mapenc=quote_plus('Hiệu Vàng Ngọc Diệp, ' + MAP_Q))
    page('lien-he/index.html', 'Liên Hệ | Hiệu Vàng Ngọc Diệp',
         'Liên hệ Hiệu Vàng Ngọc Diệp – 94-96 Lý Thái Tổ, Thanh Khê, Đà Nẵng. Hotline / Zalo 0905 887 044.',
         main, active='/lien-he/', page_id='contact')


PRIVACY_UPDATED = '07/10/2026'
PRIVACY = """
<p>Hiệu Vàng Ngọc Diệp (Công Ty TNHH MTV Hiệu Vàng Ngọc Diệp) tôn trọng và cam kết bảo vệ thông tin cá nhân của Quý khách. Chính sách này giải thích chúng tôi thu thập thông tin gì, dùng vào việc gì và Quý khách có những quyền gì khi truy cập website hoặc liên hệ với cửa hàng.</p>
<h2>1. Thông tin chúng tôi thu thập</h2>
<p>Website <strong>không yêu cầu đăng ký tài khoản</strong> và <strong>không thanh toán trực tuyến</strong>. Chúng tôi chỉ nhận những thông tin do Quý khách chủ động cung cấp khi:</p>
<ul>
<li>Gửi yêu cầu tư vấn qua form Liên hệ: họ tên, số điện thoại, nhu cầu và nội dung cần tư vấn.</li>
<li>Trò chuyện qua khung Live Chat: họ tên, số điện thoại (nếu có), nội dung tin nhắn và sản phẩm Quý khách quan tâm.</li>
<li>Gọi điện, nhắn Zalo, nhắn tin Fanpage hoặc gửi email cho cửa hàng.</li>
</ul>
<p>Chúng tôi <strong>không</strong> thu thập số CCCD, thông tin thẻ ngân hàng hay mật khẩu của Quý khách qua website.</p>
<h2>2. Mục đích sử dụng thông tin</h2>
<ul>
<li>Liên hệ lại để tư vấn sản phẩm, báo giá, đặt làm hoặc gia công trang sức theo yêu cầu.</li>
<li>Xác nhận lịch hẹn, thông báo khi sản phẩm sẵn sàng tại cửa hàng.</li>
<li>Giải đáp thắc mắc, tiếp nhận góp ý để nâng cao chất lượng phục vụ.</li>
</ul>
<p>Chúng tôi không dùng thông tin của Quý khách để gửi quảng cáo hàng loạt khi chưa được Quý khách đồng ý.</p>
<h2>3. Chia sẻ thông tin</h2>
<p>Hiệu Vàng Ngọc Diệp <strong>không bán, không cho thuê và không trao đổi</strong> thông tin cá nhân của Quý khách cho bên thứ ba. Thông tin chỉ được cung cấp khi có yêu cầu của cơ quan nhà nước có thẩm quyền theo quy định của pháp luật.</p>
<h2>4. Lưu trữ và bảo mật</h2>
<ul>
<li>Thông tin được lưu giữ trong thời gian cần thiết để phục vụ yêu cầu của Quý khách hoặc theo thời hạn pháp luật quy định.</li>
<li>Chỉ nhân viên phụ trách tư vấn, chăm sóc khách hàng mới được tiếp cận thông tin.</li>
<li>Website sử dụng kết nối mã hoá HTTPS để bảo vệ dữ liệu khi truyền đi.</li>
</ul>
<h2>5. Cookie và dữ liệu trên trình duyệt</h2>
<p>Website không dùng cookie quảng cáo. Trình duyệt của Quý khách chỉ lưu lựa chọn giao diện sáng / tối để lần sau mở lại đúng chế độ Quý khách đã chọn. Quý khách có thể xoá dữ liệu này bất cứ lúc nào trong phần cài đặt trình duyệt.</p>
<h2>6. Dịch vụ bên thứ ba</h2>
<p>Một số tiện ích trên website do bên thứ ba cung cấp và có chính sách bảo mật riêng: bản đồ Google Maps, biểu đồ giá vàng TradingView, nguồn giá vàng / bạc thế giới và tỷ giá ngoại tệ dùng để tham khảo, cùng các liên kết tới Facebook và Zalo. Khi Quý khách sử dụng các tiện ích này, nhà cung cấp có thể ghi nhận thông tin kỹ thuật như địa chỉ IP, loại trình duyệt theo chính sách của họ.</p>
<h2>7. Quyền của Quý khách</h2>
<p>Quý khách có quyền yêu cầu xem, chỉnh sửa hoặc xoá thông tin cá nhân đã cung cấp cho cửa hàng, cũng như rút lại sự đồng ý cho việc sử dụng thông tin, phù hợp với quy định pháp luật hiện hành về bảo vệ dữ liệu cá nhân. Vui lòng liên hệ theo thông tin bên dưới, chúng tôi sẽ phản hồi trong thời gian sớm nhất.</p>
<h2>8. Thay đổi chính sách</h2>
<p>Chính sách có thể được cập nhật để phù hợp với hoạt động của cửa hàng và quy định pháp luật. Phiên bản mới sẽ được đăng tại trang này, kèm ngày cập nhật.</p>
<h2>9. Liên hệ</h2>
<ul>
<li>Địa chỉ: <a href="#" data-contact="address">94-96 Lý Thái Tổ, phường Thanh Khê, TP. Đà Nẵng</a></li>
<li>Hotline / Zalo: <a href="#" data-contact="hotline">0905 887 044</a></li>
<li>Hotline: <a href="#" data-contact="hotline2">0905 886 011</a></li>
<li>Email: <a href="#" data-contact="email">Đang cập nhật</a></li>
</ul>
"""


def build_privacy():
    main = """    <main class="post-page">
      <article class="post">
        <header class="post__head container">
          <nav class="crumb" aria-label="Đường dẫn"><a href="/">Trang chủ</a><span aria-hidden="true">/</span><span>Chính sách bảo mật</span></nav>
          <h1 class="post__title">Chính Sách <span class="gold-text">Bảo Mật</span></h1>
          <p class="post__lead">Cách Hiệu Vàng Ngọc Diệp thu thập, sử dụng và bảo vệ thông tin cá nhân của Quý khách.</p>
          <div class="post__meta">
            <span><svg class="i i-16" stroke-width="2"><use href="#i-calendar"/></svg>Cập nhật: %s</span>
          </div>
        </header>
        <div class="post__content">
%s
        </div>
      </article>
    </main>
""" % (PRIVACY_UPDATED, '\n'.join('          ' + l if l.strip() else '' for l in PRIVACY.strip().split('\n')))
    page('chinh-sach-bao-mat/index.html', 'Chính Sách Bảo Mật | Hiệu Vàng Ngọc Diệp',
         'Chính sách bảo mật thông tin khách hàng của Hiệu Vàng Ngọc Diệp – 94-96 Lý Thái Tổ, Thanh Khê, Đà Nẵng.',
         main, page_id='privacy')


def build_404():
    main = """    <main class="post-page">
      <article class="post">
        <header class="post__head container">
          <h1 class="post__title">Không tìm thấy <span class="gold-text">trang</span></h1>
          <p class="post__lead">Trang Quý khách tìm có thể đã được đổi địa chỉ hoặc không còn tồn tại.</p>
          <div class="notfound__actions">
            <a href="/" class="btn-gold">Về trang chủ</a>
            <a href="/bang-gia/" class="btn-outline">Xem bảng giá vàng</a>
            <a href="/san-pham/" class="btn-outline">Xem sản phẩm</a>
          </div>
        </header>
      </article>
    </main>
"""
    page('404.html', 'Không tìm thấy trang | Hiệu Vàng Ngọc Diệp', 'Trang không tồn tại. Quay về trang chủ Hiệu Vàng Ngọc Diệp Đà Nẵng.', main, page_id='404')


if __name__ == '__main__':
    print('Dựng trang:')
    build_prices()
    build_contact()
    build_news()
    build_privacy()
    build_404()
