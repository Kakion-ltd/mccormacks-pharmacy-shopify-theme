import re, html as H

ACC = re.compile(r'<dt>(.*?)(?:<i\b.*?)?</dt>\s*<dd[^>]*>(.*?)</dd>', re.S | re.I)


def sections(page):
    """The old site's accordion: {'Product Information': text, 'How To Use': ...}."""
    out = {}
    m = re.search(r'<dl class="mz_accordion">(.*?)</dl>', page, re.S | re.I)
    if not m:
        return out
    for dt, dd in ACC.findall(m.group(1)):
        name = H.unescape(re.sub(r'<[^>]+>', '', dt)).strip()
        body = re.sub(r'<(script|style)\b.*?</\1>', ' ', dd, flags=re.S | re.I)
        body = re.sub(r'<br\s*/?>|</p>|</div>', '\n', body, flags=re.I)
        body = H.unescape(re.sub(r'<[^>]+>', '', body))
        body = '\n'.join(l.strip() for l in body.split('\n'))
        body = re.sub(r'\n{3,}', '\n\n', body).strip()
        if body:
            out[name] = body
    return out


if __name__ == '__main__':
    s = sections(open('probe.html', encoding='utf-8', errors='replace').read())
    for k, v in s.items():
        print('###', k, f'({len(v)} chars)')
        print(v)
        print()
