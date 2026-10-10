#!/usr/bin/env python3
"""Dựng các trang: /bang-gia/, /may-tinh-gia-vang/, /may-tinh-gia-bac/, /lien-he/, /tin-tuc/ và từng bài /tin-tuc/<slug>/.

Khung trang (head, header, menu, chat, nút nổi, drawer) lấy từ san-pham/index.html để mọi trang đồng bộ.
Khối bảng giá vàng / bạc lấy từ index.html (trang chủ).

Chạy lại sau khi sửa nội dung:  python3 scripts/build_pages.py && python3 scripts/bake_static.py
Tin tức: quản lý qua CMS (scripts/data/posts.json + scripts/data/tin-tuc/) — xem GAS.md mục IV.
"""
import html
import json
import os
import re
import shutil

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
# Dữ liệu do CMS ghi (xem GAS.md mục IV) — KHÔNG sửa tay:
#   scripts/data/posts.json            danh sách bài (không có body)
#   scripts/data/tin-tuc/<slug>.json   bản ghi đầy đủ 1 bài (có body, trừ bài smart)
# Chuyên mục: NEWS_CATS trong scripts/data/site.json (CMS đọc cùng nguồn này).
DATA = os.path.join(REPO, 'scripts', 'data')
_load = lambda *p: json.load(open(os.path.join(DATA, *p), encoding='utf-8'))
CATS = {c['slug']: c['title'] for c in _load('site.json')['NEWS_CATS']}


def _date_key(p):
    d, m, y = p['date'].split('/')
    return (y, m, d)


POSTS = sorted((_load('tin-tuc', x['slug'] + '.json') for x in _load('posts.json')), key=_date_key, reverse=True)

# Bài Smart content: thân bài thiết kế sẵn (khối tv-) ở scripts/content/tin-tuc/<slug>.html
SMART_DIR = os.path.join(REPO, 'scripts', 'content', 'tin-tuc')  # bản đã duyệt; bản nháp để ở content/_drafts/
for _p in POSTS:
    if _p.get('smart'):
        _p['body'] = open(os.path.join(SMART_DIR, _p['slug'] + '.html'), encoding='utf-8').read()


def text_fields(p):
    # Tiêu đề/mô tả do CMS nhập -> escape khi chèn vào HTML (giữ nguyên dấu nháy để trang cũ không đổi byte)
    return {k: html.escape(p[k], quote=False) for k in ('title', 'excerpt')}


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
''' % dict(p, cls=cls, catname=CATS[p['cat']], alt=html.escape(p['title']), **text_fields(p))


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
''' % dict(p, catname=CATS[p['cat']], alt=html.escape(p['title']), rt=reading_time(p['body']), **text_fields(p),
           body='\n'.join('          ' + l if l.strip() else '' for l in p['body'].strip().split('\n')),
           related=''.join(post_card(x) for x in related[:3]),
           cta='' if p.get('smart') else POST_CTA)
        page('tin-tuc/%s/index.html' % p['slug'], '%s | Hiệu Vàng Ngọc Diệp' % p['title'], p['excerpt'], main,
             active='/tin-tuc/', og_image='/assets/img/news/' + p['cover'], page_id='post')

    # Bài đã xoá qua CMS: gỡ thư mục html/tin-tuc/<slug>/ không còn trong posts.json (mọi thư mục con
    # của tin-tuc/ đều do hàm này sinh ra, nên an toàn để xoá).
    keep = {p['slug'] for p in POSTS}
    news_dir = os.path.join(ROOT, 'tin-tuc')
    for d in sorted(os.listdir(news_dir)):
        if os.path.isdir(os.path.join(news_dir, d)) and d not in keep:
            shutil.rmtree(os.path.join(news_dir, d))
            print('  ✗ tin-tuc/%s/ (bài đã xoá)' % d)


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
              <div class="hp-field" aria-hidden="true"><label for="cf-hp">Để trống ô này</label><input id="cf-hp" name="_hp" type="text" tabindex="-1" autocomplete="off" /></div>
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
