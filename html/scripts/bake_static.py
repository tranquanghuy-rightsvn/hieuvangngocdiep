#!/usr/bin/env python3
"""In sẵn nội dung vào HTML (site tĩnh) — JS không còn dựng nội dung, chỉ lo tương tác + cập nhật giá vàng/bạc.

Dữ liệu:
  scripts/data/site.json     thông tin liên hệ (CONTACT), danh mục sản phẩm (PRODUCTS), thứ tự menu (MENU_ORDER)
  scripts/data/catalog.json  toàn bộ sản phẩm
  assets/js/main.js          giá vàng/bạc mặc định (PRICES, SILVER_PRICES) — JS tự cập nhật giá mới khi mở trang

Sửa dữ liệu xong chạy:  python3 scripts/bake_static.py
(Nếu chạy scripts/build_pages.py thì chạy lại file này sau đó.)
"""
import html
import json
import os
import re
import subprocess
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'scripts', 'data')
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
    split = 3 if len(PRODUCTS) == 5 else len(PRODUCTS)
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


def main():
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ('.git', 'docs', 'scripts', 'assets', 'node_modules', '.vercel')]
        if 'index.html' not in files:
            continue
        path = os.path.join(dirpath, 'index.html')
        src = old = open(path, encoding='utf-8').read()
        src = bake_shared(src)
        src = fill(src, 'mega-products', mega())
        src = fill(src, 'nav-products', drawer_products())
        src = bake_home_cats(src)
        src = bake_featured(src)
        src = bake_shop(src)
        src = bake_prices(src)
        src = bake_contact(src)
        if src != old:
            open(path, 'w', encoding='utf-8').write(src)
            print('  ✓', os.path.relpath(path, ROOT))


if __name__ == '__main__':
    main()
