#!/usr/bin/env python3
"""In sẵn nội dung vào HTML (site tĩnh) — JS không còn dựng nội dung, chỉ lo tương tác + cập nhật giá vàng/bạc.

Dữ liệu:
  scripts/data/site.json     thông tin liên hệ (CONTACT), danh mục sản phẩm (PRODUCTS), thứ tự menu (MENU_ORDER)
  scripts/data/catalog.json  toàn bộ sản phẩm
  assets/js/main.js          giá vàng/bạc mặc định (PRICES, SILVER_PRICES) — JS tự cập nhật giá mới khi mở trang

Sửa dữ liệu xong chạy:  python3 scripts/bake_static.py
(Nếu chạy scripts/build_pages.py thì chạy lại file này sau đó.)
Cũng sinh: canonical/og/twitter/JSON-LD từng trang, dòng credit cuối trang, html/sitemap.xml, html/robots.txt.
"""
import html
import json
import os
import re
import subprocess
import unicodedata

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(REPO, 'html')          # thư mục web (được deploy)
DATA = os.path.join(REPO, 'scripts', 'data')
SITE = json.load(open(os.path.join(DATA, 'site.json'), encoding='utf-8'))
CATALOG = json.load(open(os.path.join(DATA, 'catalog.json'), encoding='utf-8'))
CONTACT, PRODUCTS = SITE['CONTACT'], SITE['PRODUCTS']
MENU = [PRODUCTS[k] for k in SITE['MENU_ORDER']]
CAT_BY_SLUG = {c['slug']: c for c in PRODUCTS}
IMG = '/assets/img/catalog/'

# Giá mặc định lấy từ main.js (một nguồn duy nhất)
_js = open(os.path.join(ROOT, 'assets', 'js', 'main.js'), encoding='utf-8').read()
_data = _js[_js.index('/* ---------------- DATA'):_js.index('/* ---------------- HELPERS')]
PRICE = json.loads(subprocess.check_output(['node', '-e', '''
const vm = require('vm'), ctx = {}; vm.createContext(ctx);
vm.runInContext(require('fs').readFileSync(0, 'utf8') + ';this.o = {PRICES, SILVER_PRICES, PRICES_UPDATED_AT, SILVER_UPDATED_AT}', ctx);
process.stdout.write(JSON.stringify(ctx.o));
'''], input=_data.encode()))

e = lambda s: html.escape(str(s), quote=True)


def icon(name, cls='', sw=2):
    return '<svg class="i %s" stroke-width="%s"><use href="#i-%s"/></svg>' % (cls, sw, name)


def fmt(n):
    return '{:,}'.format(n).replace(',', '.')


def shop_url(**params):
    from urllib.parse import quote
    q = ['%s=%s' % (k, quote(v)) for k, v in params.items() if v]
    return '/san-pham/' + ('?' + '&'.join(q) if q else '')


def fold(s):
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s.replace('đ', 'd').replace('Đ', 'D').lower()


# ---------------------------------------------------------------- thay nội dung theo id
def fill(src, el_id, inner):
    m = re.search(r'<([a-z0-9]+)\b[^>]*\bid="%s"[^>]*>' % re.escape(el_id), src)
    if not m:
        return src
    tag, start = m.group(1), m.end()
    depth, pos = 1, start
    pat = re.compile(r'<(/?)%s\b[^>]*>' % tag)
    while depth:
        t = pat.search(src, pos)
        depth += -1 if t.group(1) else 1
        pos = t.end()
    return src[:start] + inner + src[t.start():]


def set_attr(tag, name, value):
    """Đặt / thay thuộc tính trong 1 thẻ mở."""
    if value is None:
        return re.sub(r'\s%s="[^"]*"' % name, '', tag)
    if re.search(r'\s%s="' % name, tag):
        return re.sub(r'(\s%s=")[^"]*"' % name, lambda m: m.group(1) + e(value) + '"', tag)
    return re.sub(r'\s*(/?)>$', lambda m: ' %s="%s"%s>' % (name, e(value), m.group(1) and ' /' or ''), tag, count=1)


# ---------------------------------------------------------------- liên hệ
def digits(v):
    return re.sub(r'\D', '', v)


HREF = {
    'address': lambda v: 'https://www.google.com/maps/search/?api=1&query=' + __import__('urllib.parse').parse.quote(v, safe=''),
    'hotline': lambda v: 'tel:' + digits(v),
    'hotline2': lambda v: 'tel:' + digits(v),
    'zalo': lambda v: 'https://zalo.me/' + digits(v),
    'email': lambda v: 'mailto:' + v,
    'facebook': lambda v: v,
}


def link_attrs(tag, key):
    v = (CONTACT.get(key) or '').strip()
    if not v or key not in HREF:
        return tag
    tag = set_attr(tag, 'href', HREF[key](v))
    if key in ('address', 'zalo', 'facebook'):
        tag = set_attr(set_attr(tag, 'target', '_blank'), 'rel', 'noopener noreferrer')
    return tag


def bake_contact(src):
    def text(m):
        tag, name, body = m.group(1), m.group(2), m.group(3)
        key = re.search(r'data-contact="([^"]+)"', tag).group(1)
        v = (CONTACT.get(key) or '').strip()
        if v:
            pre = re.search(r'data-contact-prefix="([^"]*)"', tag)
            body = e((html.unescape(pre.group(1)) if pre else '') + v)
            tag = set_attr(tag, 'hidden', None).replace(' hidden>', '>')
        elif 'data-contact-optional' in tag:
            body = ''
            if ' hidden' not in tag:
                tag = tag[:-1] + ' hidden>'
        if name == 'a':
            tag = link_attrs(tag, key)
        return tag + body + '</%s>' % name
    src = re.sub(r'(<(a|span|p|div|small|b)\b[^>]*\bdata-contact="[^"]+"[^>]*>)(.*?)</\2>', text, src, flags=re.S)
    src = re.sub(r'<a\b[^>]*\bdata-contact-link="([^"]+)"[^>]*>', lambda m: link_attrs(m.group(0), m.group(1)), src)
    return src


# ---------------------------------------------------------------- menu
def mega():
    return ''.join(
        '<div class="mega__col">'
        '<a href="%(u)s" class="mega__thumb"><img src="%(img)s" alt="%(t)s" loading="lazy" /></a>'
        '<a href="%(u)s" class="mega__title">%(t)s</a>'
        '<p class="mega__desc">%(d)s</p>'
        '<ul class="mega__list">%(list)s</ul>'
        '<a href="%(u)s" class="mega__all">Xem tất cả%(arrow)s</a></div>' % {
            'u': e(shop_url(cat=p['slug'])), 'img': IMG + p['img'], 't': e(p['title']), 'd': e(p['desc']),
            'list': ''.join('<li><a href="%s">%s</a></li>' % (e(shop_url(cat=p['slug'], sub=c)), e(c)) for c in p['children']),
            'arrow': icon('arrow-right')}
        for p in MENU)


def drawer_products():
    return ''.join(
        '<div><div class="sub-row"><a href="%s" class="sub-row__lbl">%s</a>'
        '<button type="button" class="sub-row__tg js-sub3" aria-label="Mở/đóng submenu %s" aria-expanded="false">%s</button></div>'
        '<div class="sub" hidden><div class="sub__list sub__list--l3">%s</div></div></div>' % (
            e(shop_url(cat=p['slug'])), e(p['title']), e(p['title']), icon('chevron-down', 'chev'),
            ''.join('<a href="%s" class="sub-leaf">%s</a>' % (e(shop_url(cat=p['slug'], sub=c)), e(c)) for c in p['children']))
        for p in MENU)


# ---------------------------------------------------------------- trang chủ: danh mục
def cat_card(p):
    return ('<a href="%s" class="pcard">'
            '<div class="pcard__media"><img src="%s" alt="%s" loading="lazy" /><div class="pcard__shade"></div></div>'
            '<div class="pcard__body"><h3 class="pcard__title">%s</h3><p class="pcard__desc">%s</p>'
            '<span class="pcard__more">Xem thêm%s</span></div></a>') % (
        e(shop_url(cat=p['slug'])), IMG + p['img'], e(p['title']), e(p['title']), e(p['desc']), icon('arrow-right'))


def bake_home_cats(src):
    # hàng 3 cột trước, phần lẻ dồn xuống hàng 2 cột (5 → 3+2, 7 → 3+2+2)
    n = len(PRODUCTS)
    split = n - {0: 0, 1: 4, 2: 2}[n % 3] if n > 4 else n
    src = fill(src, 'pgrid-3', ''.join('<div>%s</div>' % cat_card(p) for p in PRODUCTS[:split]))
    src = fill(src, 'pgrid-2', ''.join('<div>%s</div>' % cat_card(p) for p in PRODUCTS[split:]))
    src = re.sub(r'(<div[^>]*id="pgrid-2")( hidden)?', r'\1' + (' hidden' if split == len(PRODUCTS) else ''), src)
    slides = ''.join(re.sub(r'^<a ', '<a data-slide="%d"%s ' % (i, '' if i == 0 else ' hidden'), cat_card(p)) for i, p in enumerate(PRODUCTS))
    src = fill(src, 'pcarousel-slide', slides)
    src = fill(src, 'pcarousel-dots', ''.join(
        '<button type="button" class="pcarousel__dot%s" data-i="%d" aria-label="Danh mục %d"></button>' % (' is-on' if i == 0 else '', i, i + 1)
        for i in range(len(PRODUCTS))))
    src = fill(src, 'pcarousel-thumbs', ''.join(
        '<button type="button" class="pcarousel__thumb%s" data-i="%d" aria-label="%s"><img src="%s" alt="%s" loading="lazy" decoding="async" /></button>' % (
            ' is-on' if i == 0 else '', i, e(p['title']), IMG + p['img'], e(p['title']))
        for i, p in enumerate(PRODUCTS)))
    return src


# ---------------------------------------------------------------- thẻ sản phẩm
def prod_card(p, idx, attrs='', hidden=False, delay=0):
    gold = p.get('gold') or ''
    badge = ('<span class="badge-gold%s">%s</span>' % (' badge-gold--24k' if re.search(r'999|24K', gold) else '', e(gold.replace('Vàng ', '')))) if gold else ''
    cat = CAT_BY_SLUG[p['cat']]
    q = fold(' '.join([p['name'], p['id'], p['sub'], p['desc'], cat['title'], gold]))
    data = ('data-id="%s" data-idx="%d" data-cat="%s" data-cat-title="%s" data-cat-desc="%s" data-sub="%s" data-name="%s" data-gold="%s" data-weight="%s" data-desc="%s" data-q="%s"%s%s%s' % (
        e(p['id']), idx, e(p['cat']), e(cat['title']), e(cat['desc']), e(p['sub']), e(p['name']), e(gold), e(p.get('weight') or ''), e(p['desc']), e(q),
        ' data-featured' if p.get('featured') else '', ' data-new' if p.get('isNew') else '', attrs))
    return ('<article class="prod" %s%s style="animation-delay:%dms">'
            '<button type="button" class="prod__media js-qv" data-id="%s" aria-label="Xem nhanh %s">'
            '<img src="%s%s.jpg" alt="%s" loading="lazy" decoding="async" width="800" height="800" />'
            '<span class="prod__badges">%s%s</span>'
            '<span class="prod__quick">%sXem nhanh</span>'
            '</button>'
            '<div class="prod__body">'
            '<p class="prod__meta">%s · %s%s</p>'
            '<h3 class="prod__name"><button type="button" class="js-qv" data-id="%s">%s</button></h3>'
            '<button type="button" class="prod__more js-qv" data-id="%s" tabindex="-1">Xem chi tiết%s</button>'
            '</div></article>') % (
        data, ' hidden' if hidden else '', min(delay, 12) * 45,
        e(p['id']), e(p['name']), IMG, p['img'], e(p['name']),
        badge, '<span class="badge-new">Mới</span>' if p.get('isNew') else '', icon('eye', 'i-16'),
        e(p['id']), e(p['sub']), ' · ' + e(p['weight']) if p.get('weight') else '',
        e(p['id']), e(p['name']), e(p['id']), icon('arrow-right', 'i-16'))


def bake_featured(src):
    cats = [{'slug': '', 'title': 'Nổi bật'}] + MENU
    src = fill(src, 'feat-chips', ''.join(
        '<button type="button" class="chip%s" data-cat="%s" aria-pressed="%s">%s</button>' % (
            '' if i else ' is-on', c['slug'], 'false' if i else 'true', e(c['title'])) for i, c in enumerate(cats)))
    feat = [p['id'] for p in CATALOG if p.get('featured')][:8]
    top = set()
    for c in MENU:
        top.update(p['id'] for p in [x for x in CATALOG if x['cat'] == c['slug']][:8])
    cards, shown = [], 0
    for i, p in enumerate(CATALOG):
        if p['id'] not in top and p['id'] not in feat:
            continue
        attrs = (' data-pick' if p['id'] in feat else '') + (' data-top' if p['id'] in top else '')
        is_feat = p['id'] in feat
        cards.append(prod_card(p, i, attrs, hidden=not is_feat, delay=shown))
        shown += is_feat
    return fill(src, 'feat-grid', ''.join(cards))


# ---------------------------------------------------------------- trang sản phẩm
def bake_shop(src):
    cats = [{'slug': '', 'title': 'Tất cả'}] + MENU
    src = fill(src, 'shop-cats', ''.join(
        '<button type="button" class="chip%s" data-cat="%s" aria-pressed="%s">%s<span class="chip__n">%d</span></button>' % (
            '' if c['slug'] else ' is-on', c['slug'], 'false' if c['slug'] else 'true', e(c['title']),
            sum(1 for p in CATALOG if not c['slug'] or p['cat'] == c['slug'])) for c in cats))
    subs = '<button type="button" class="chip chip--sm is-on" data-sub="">Tất cả</button>' + ''.join(
        '<button type="button" class="chip chip--sm" data-parent="%s" data-sub="%s" hidden>%s</button>' % (c['slug'], e(s), e(s))
        for c in MENU for s in c['children'])
    src = fill(src, 'shop-subs', subs)
    order = sorted(range(len(CATALOG)), key=lambda i: (0 if CATALOG[i].get('featured') else 1, i))
    src = fill(src, 'shop-grid', ''.join(prod_card(CATALOG[i], i, delay=n) for n, i in enumerate(order)))
    src = fill(src, 'shop-count', '%d sản phẩm' % len(CATALOG))
    return src


# ---------------------------------------------------------------- giá vàng / bạc (giá mặc định, JS cập nhật giá mới)
def price_rows(rows, sell_cls):
    d = ''.join(
        '<tr class="prow reveal" data-id="%s"><td><div class="prow__name"><span class="badge"><span>Hiệu Vàng</span><span>Ngọc Diệp</span></span>'
        '<span class="prow__label">%s</span></div></td><td class="prow__price" data-buy>%s</td><td class="prow__price %s" data-sell>%s</td></tr>' % (
            p['id'], e(p['name']), fmt(p['buy']), sell_cls, fmt(p['sell'])) for p in rows)
    m = ''.join(
        '<tr class="prow--m reveal" data-id="%s"><td>%s</td><td data-buy>%s</td><td class="%s" data-sell>%s</td></tr>' % (
            p['id'], e(p['name']), fmt(p['buy']), sell_cls, fmt(p['sell'])) for p in rows)
    return d, m


def bake_prices(src):
    gd, gm = price_rows(PRICE['PRICES'], 'gold-text')
    sd, sm = price_rows(PRICE['SILVER_PRICES'], 'silver-text')
    for i, v in (('ptable-d', gd), ('ptable-m', gm), ('stable-d', sd), ('stable-m', sm)):
        src = fill(src, i, v)
    src = fill(src, 'updated-at', PRICE['PRICES_UPDATED_AT'])
    src = fill(src, 'silver-updated-at', PRICE['SILVER_UPDATED_AT'])
    item = lambda pid, name, val, cls='': '<span class="ticker__item"><span class="ticker__name%s">%s</span><span class="ticker__val" data-id="%s">%s</span></span>' % (cls, e(name), pid, fmt(val))
    s0 = PRICE['SILVER_PRICES'][0]
    one = ''.join(item(p['id'], p['name'], p['sell']) for p in PRICE['PRICES']) + item(s0['id'], 'Bạc trang sức 925', s0['sell'], ' ticker__name--silver')
    src = fill(src, 'ticker', one + one.replace('<span class="ticker__item">', '<span class="ticker__item" aria-hidden="true">'))
    if 'id="calc-type"' in src:
        rows = PRICE['SILVER_PRICES'] if 'data-calc="silver"' in src else PRICE['PRICES']
        src = fill(src, 'calc-type', ''.join('<option value="%s">%s</option>' % (p['id'], e(p['name'])) for p in rows))
    return src


# ---------------------------------------------------------------- khối tĩnh dùng chung (xem nhanh, chat)
QUICKVIEW = '''  <!-- ============ XEM NHANH SẢN PHẨM ============ -->
  <div class="qv" id="qv" hidden>
    <div class="qv__overlay js-qv-close"></div>
    <div class="qv__panel" role="dialog" aria-modal="true" aria-labelledby="qv-title" tabindex="-1">
      <button type="button" class="qv__x js-qv-close" aria-label="Đóng">%(x)s</button>
      <div class="qv__media"><img id="qv-img" src="data:," alt="" />
        <button type="button" class="qv__nav qv__nav--prev" data-step="-1" aria-label="Sản phẩm trước">%(chev)s</button>
        <button type="button" class="qv__nav qv__nav--next" data-step="1" aria-label="Sản phẩm tiếp theo">%(chev)s</button>
      </div>
      <div class="qv__info">
        <p class="qv__crumb"><a href="/san-pham/" id="qv-cat"></a> · <a href="/san-pham/" id="qv-sub"></a></p>
        <h2 class="qv__title" id="qv-title"></h2>
        <p class="qv__sku" id="qv-sku"></p>
        <dl class="qv__specs">
          <div><dt>Loại vàng</dt><dd id="qv-gold"></dd></div>
          <div><dt>Trọng lượng</dt><dd id="qv-weight"></dd></div>
          <div><dt>Danh mục</dt><dd id="qv-subname"></dd></div>
          <div><dt>Mã sản phẩm</dt><dd id="qv-id"></dd></div>
        </dl>
        <p class="qv__desc" id="qv-desc"></p>
        <div class="qv__actions">
          <button type="button" class="btn-gold qv__cta js-qv-chat">%(msg)sTư vấn ngay</button>
          <a href="#" class="qv__ghost" data-contact-link="hotline">%(phone)sGọi đặt hàng</a>
        </div>
        <p class="qv__note">Mẫu có sẵn tại cửa hàng 94-96 Lý Thái Tổ, Đà Nẵng. Nhận gia công theo yêu cầu về kiểu dáng, trọng lượng — vui lòng liên hệ để được tư vấn.</p>
      </div>
    </div>
  </div>

''' % {'x': icon('x', 'i-20'), 'chev': icon('chevron-down', 'i-20'), 'msg': icon('message-circle', 'i-18'), 'phone': icon('phone', 'i-18')}

CHAT_EXTRA = '''
      <div class="chat__product" id="chat-product" hidden><img src="data:," alt="" /><div><b></b><span></span></div></div>
      <div class="chat__msgs" id="chat-msgs" hidden>
        <div class="chat__msg chat__msg--me" id="chat-ask" hidden></div>
        <div class="chat__msg chat__msg--them" id="chat-hello"></div>
      </div>'''
CHAT_COMPOSE = '''
    <form class="chat__compose" id="chat-compose" hidden><input type="text" class="chat__input" placeholder="Nhập tin nhắn..." aria-label="Tin nhắn" /><button type="submit" aria-label="Gửi">%s</button></form>''' % icon('send', 'i-16')


def bake_shared(src):
    if 'id="chat-msgs"' not in src:
        src = src.replace('Quý khách có thể trao đổi với nhân viên tư vấn ngay tại đây.</div>',
                          'Quý khách có thể trao đổi với nhân viên tư vấn ngay tại đây.</div>' + CHAT_EXTRA, 1)
        i = src.index('id="chat-body"')
        j = src.index('</form>\n    </div>', i) + len('</form>\n    </div>')
        src = src[:j] + CHAT_COMPOSE + src[j:]
    if 'data-grid' in src and 'id="qv"' not in src:
        src = src.replace('  <!-- ============ LIVE CHAT PANEL', QUICKVIEW + '  <!-- ============ LIVE CHAT PANEL', 1)
    # catalog.js không còn dùng
    src = src.replace('  <script src="/assets/js/catalog.js" defer></script>\n', '')
    return src


# ---------------------------------------------------------------- SEO: canonical, meta, JSON-LD, sitemap, robots
SITE_URL = 'https://hieuvangngocdiep.vn'
STORE_ID = SITE_URL + '/#store'
SITE_ID = SITE_URL + '/#website'
PAGE_TYPE = {'': 'WebPage', 'gioi-thieu/': 'AboutPage', 'lien-he/': 'ContactPage', 'san-pham/': 'CollectionPage', 'tin-tuc/': 'CollectionPage'}
CREDIT = '<span class="site-credit"> · Website creator by <a href="https://web100.vn" target="_blank" rel="noopener">web100.vn</a></span>'
RATES = '<span class="site-credit"> · Tỷ giá: <a href="https://www.exchangerate-api.com" target="_blank" rel="noopener">Rates By Exchange Rate API</a></span>'


def img_size(rel):
    out = subprocess.check_output(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', os.path.join(ROOT, rel.lstrip('/'))]).decode()
    return re.search(r'pixelWidth: (\d+)', out).group(1), re.search(r'pixelHeight: (\d+)', out).group(1)


def meta_get(src, attr, name):
    m = re.search(r'<meta %s="%s" content="([^"]*)"' % (attr, re.escape(name)), src)
    return html.unescape(m.group(1)) if m else ''


def meta_set(head, attr, name, value, after=None):
    tag = '<meta %s="%s" content="%s" />' % (attr, name, e(value))
    pat = r'<meta %s="%s" content="[^"]*" />' % (attr, re.escape(name))
    if re.search(pat, head):
        return re.sub(pat, lambda m: tag, head, count=1)
    anchor = after or '<meta name="theme-color"'
    i = head.index(anchor)
    j = head.index('\n', i) + 1
    return head[:j] + '  ' + tag + '\n' + head[j:]


def text_of(fragment):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', fragment))).strip()


def iso_date(dmy):
    d, m, y = dmy.split('/')
    return '%s-%s-%sT08:00:00+07:00' % (y, m, d)


def store_node():
    c = CONTACT
    return {
        '@type': 'JewelryStore', '@id': STORE_ID,
        'name': 'Hiệu Vàng Ngọc Diệp', 'legalName': 'Công Ty TNHH MTV Hiệu Vàng Ngọc Diệp',
        'alternateName': 'Ngọc Diệp Jewelry', 'url': SITE_URL + '/',
        'logo': {'@type': 'ImageObject', 'url': SITE_URL + '/assets/img/logo.png'},
        'image': SITE_URL + '/assets/img/og-image.jpg',
        'description': 'Hiệu vàng tại Đà Nẵng từ năm 1990: mua bán vàng 24K, 18K, trang sức cưới, quà tặng vàng và gia công trang sức vàng bạc theo yêu cầu.',
        'telephone': '+84' + digits(c['hotline'])[1:], 'email': c['email'],
        'address': {'@type': 'PostalAddress', 'streetAddress': '94-96 Lý Thái Tổ', 'addressLocality': 'Phường Thanh Khê',
                    'addressRegion': 'TP. Đà Nẵng', 'addressCountry': 'VN'},
        'hasMap': HREF['address'](c['address']),
        'openingHoursSpecification': {'@type': 'OpeningHoursSpecification', 'opens': '07:00', 'closes': '21:00',
                                      'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']},
        'foundingDate': '1990', 'areaServed': 'Đà Nẵng', 'currenciesAccepted': 'VND',
        'sameAs': [c['facebook']],
    }


def crumbs_of(src, url, title):
    nav = re.search(r'<nav class="crumb"[^>]*>(.*?)</nav>', src, re.S)
    items = []
    if nav:
        for m in re.finditer(r'<a href="([^"]+)"[^>]*>(.*?)</a>|<span>([^<]+)</span>', nav.group(1)):
            if m.group(1):
                items.append((text_of(m.group(2)), SITE_URL + m.group(1)))
            else:
                items.append((text_of(m.group(3)), None))
    else:
        items = [('Trang chủ', SITE_URL + '/'), (title, None)]
    h1 = re.search(r'<h1 class="post__title">(.*?)</h1>', src, re.S)
    if 'data-page="post"' in src and h1:  # bài viết: Trang chủ > Tin tức > tên bài (bỏ nhãn chuyên mục)
        items = [x for x in items if x[1]] + [(text_of(h1.group(1)), None)]
    out = []
    for i, (name, href) in enumerate(items, 1):
        if href == url:  # mục cuối trùng trang đang xem
            href = None
        node = {'@type': 'ListItem', 'position': i, 'name': name}
        node['item'] = href or url
        out.append(node)
    return {'@type': 'BreadcrumbList', '@id': url + '#breadcrumb', 'itemListElement': out}


def faq_node(src, url):
    qs = []
    for m in re.finditer(r'<details class="tv-faq-item">\s*<summary>.*?<h3>(.*?)</h3>.*?</summary>\s*<div class="tv-faq-a">(.*?)</div>\s*</details>', src, re.S):
        qs.append({'@type': 'Question', 'name': text_of(m.group(1)), 'acceptedAnswer': {'@type': 'Answer', 'text': text_of(m.group(2))}})
    return {'@type': 'FAQPage', '@id': url + '#faq', 'mainEntity': qs} if qs else None


def bake_seo(src, rel):
    """rel: đường dẫn trang ('' = trang chủ, 'tin-tuc/abc/', '404.html')."""
    is404 = rel == '404.html'
    url = SITE_URL + '/' + ('' if is404 else rel)
    hi = src.index('</head>')
    head, body = src[:hi], src[hi:]
    head = head.replace('  <!-- Ảnh xem trước khi chia sẻ link (Zalo/Facebook). Khi có tên miền, đổi og:image/og:url sang URL tuyệt đối -->\n', '')
    title = html.unescape(re.search(r'<title>(.*?)</title>', head, re.S).group(1))
    desc = meta_get(head, 'name', 'description')
    is_post = 'data-page="post"' in body
    # ảnh chia sẻ
    og = meta_get(head, 'property', 'og:image').replace(SITE_URL, '')
    w, h = img_size(og)
    head = meta_set(head, 'name', 'robots', 'noindex, follow' if is404 else 'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1')
    if not is404:
        link = '<link rel="canonical" href="%s" />' % url
        if '<link rel="canonical"' in head:
            head = re.sub(r'<link rel="canonical" href="[^"]*" />', link, head)
        else:
            i = head.index('<meta name="description"'); j = head.index('\n', i) + 1
            head = head[:j] + '  ' + link + '\n' + head[j:]
        head = meta_set(head, 'property', 'og:url', url, after='<meta property="og:type"')
    else:  # trang 404: không canonical / og:url (phần đầu trang có thể copy từ trang khác)
        head = re.sub(r'\s*<link rel="canonical" href="[^"]*" />', '', head)
        head = re.sub(r'\s*<meta property="og:url" content="[^"]*" />', '', head)
    head = meta_set(head, 'property', 'og:type', 'article' if is_post else 'website')
    head = meta_set(head, 'property', 'og:image', SITE_URL + og)
    head = meta_set(head, 'property', 'og:image:width', w)
    head = meta_set(head, 'property', 'og:image:height', h)
    head = meta_set(head, 'property', 'og:image:alt', meta_get(head, 'property', 'og:title') or title, after='<meta property="og:image:height"')
    head = meta_set(head, 'name', 'twitter:title', meta_get(head, 'property', 'og:title') or title, after='<meta name="twitter:card"')
    head = meta_set(head, 'name', 'twitter:description', meta_get(head, 'property', 'og:description') or desc, after='<meta name="twitter:title"')
    head = meta_set(head, 'name', 'twitter:image', SITE_URL + og, after='<meta name="twitter:description"')
    # JSON-LD
    graph = [store_node(), {'@type': 'WebSite', '@id': SITE_ID, 'url': SITE_URL + '/', 'name': 'Hiệu Vàng Ngọc Diệp',
                            'inLanguage': 'vi-VN', 'publisher': {'@id': STORE_ID}}]
    if not is404:
        page = {'@type': PAGE_TYPE.get(rel, 'WebPage'), '@id': url + '#webpage', 'url': url, 'name': title, 'description': desc,
                'inLanguage': 'vi-VN', 'isPartOf': {'@id': SITE_ID}, 'primaryImageOfPage': SITE_URL + og}
        if rel:
            graph.append(crumbs_of(body, url, title.split(' | ')[0]))
            page['breadcrumb'] = {'@id': url + '#breadcrumb'}
        else:
            page['about'] = {'@id': STORE_ID}
        graph.append(page)
        if is_post:
            h1 = text_of(re.search(r'<h1 class="post__title">(.*?)</h1>', body, re.S).group(1))
            date = iso_date(re.search(r'#i-calendar"/></svg>(\d\d/\d\d/\d{4})', body).group(1))
            article = {'@type': 'BlogPosting', '@id': url + '#article', 'headline': h1, 'description': desc,
                       'image': {'@type': 'ImageObject', 'url': SITE_URL + og, 'width': int(w), 'height': int(h)},
                       'datePublished': date, 'dateModified': date, 'inLanguage': 'vi-VN',
                       'author': {'@id': STORE_ID}, 'publisher': {'@id': STORE_ID},
                       'mainEntityOfPage': {'@id': url + '#webpage'}, 'isPartOf': {'@id': SITE_ID}}
            graph.append(article)
            head = meta_set(head, 'property', 'article:published_time', date, after='<meta property="og:image:alt"')
            faq = faq_node(body, url)
            if faq:
                graph.append(faq)
    ld = '<script type="application/ld+json" id="seo-jsonld">%s</script>' % json.dumps(
        {'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    if 'id="seo-jsonld"' in head:
        head = re.sub(r'<script type="application/ld\+json" id="seo-jsonld">.*?</script>', lambda m: ld, head, flags=re.S)
    else:
        head = head.rstrip() + '\n  ' + ld + '\n'
    # dòng credit cuối trang (+ ghi nguồn tỷ giá ở trang có bảng giá — điều khoản của exchangerate-api)
    extra = CREDIT + (RATES if ('id="ptable-d"' in body or 'id="stable-d"' in body) else '')
    def foot(m):
        inner = re.sub(r'<span class="site-credit">.*?</a></span>', '', m.group(2))
        return m.group(1) + inner + extra + '</div>'
    body = re.sub(r'(<div class="(?:footer__copy|afooter__inner)">)(.*?)</div>', foot, body, count=1, flags=re.S)
    return head + body


def write_sitemap(pages):
    import datetime
    today = datetime.date.today().isoformat()
    rows = []
    for rel, src in sorted(pages.items(), key=lambda x: (x[0].count('/'), x[0])):
        if rel == '404.html':
            continue
        m = re.search(r'"dateModified":"(\d{4}-\d\d-\d\d)', src)
        pri = '1.0' if rel == '' else '0.9' if rel in ('bang-gia/', 'san-pham/') else '0.7' if rel.startswith('tin-tuc/') and rel != 'tin-tuc/' else '0.8'
        rows.append('  <url><loc>%s/%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>' % (SITE_URL, rel, m.group(1) if m else today, pri))
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % '\n'.join(rows)
    old = os.path.join(ROOT, 'sitemap.xml')
    if os.path.exists(old):  # giữ lastmod cũ nếu trang không đổi -> không đổi file khi chạy lại
        prev = dict(re.findall(r'<loc>([^<]+)</loc><lastmod>([^<]+)</lastmod>', open(old, encoding='utf-8').read()))
        xml = re.sub(r'<loc>([^<]+)</loc><lastmod>%s</lastmod>' % today,
                     lambda m: '<loc>%s</loc><lastmod>%s</lastmod>' % (m.group(1), prev.get(m.group(1), today)), xml)
    open(old, 'w', encoding='utf-8').write(xml)
    open(os.path.join(ROOT, 'robots.txt'), 'w', encoding='utf-8').write(
        'User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % SITE_URL)


def main():
    pages = {}
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ('.git', 'assets', 'node_modules', '.vercel')]
        for name in files:
            if name != 'index.html' and not (name == '404.html' and dirpath == ROOT):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, ROOT).replace('\\', '/')
            rel = '404.html' if rel == '404.html' else ('' if rel == 'index.html' else rel[:-len('index.html')])
            src = old = open(path, encoding='utf-8').read()
            src = bake_shared(src)
            src = fill(src, 'mega-products', mega())
            src = fill(src, 'nav-products', drawer_products())
            src = bake_home_cats(src)
            src = bake_featured(src)
            src = bake_shop(src)
            src = bake_prices(src)
            src = bake_contact(src)
            src = bake_seo(src, rel)
            pages[rel] = src
            if src != old:
                open(path, 'w', encoding='utf-8').write(src)
                print('  ✓', os.path.relpath(path, ROOT))
    write_sitemap(pages)


if __name__ == '__main__':
    main()
