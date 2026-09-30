"""Formatting-only fix: inline bullets -> <ul>, run-together headings -> new <p>.
Words are never changed; only bullet markers, the semicolons that ended a bullet,
and whitespace move. verify_same() proves it.
"""
import json, re, sys, html as htmlmod

HEAD_WORDS = (r'directions?|instructions?|how to use|how to apply|ingredients?|'
              r'active ingredients?|warnings?|cautions?|precautions?|dosage|usage|storage|'
              r'key benefits?|benefits?|product features?|key features?|features and benefits|'
              r'features?|suitable for|indications?|side effects?|contains|note')
# A heading only counts when it follows a finished sentence or a bullet, and
# something comes after it in the same block.
head_re = re.compile(r'(?<=[.!?;•])\s+((?i:%s))\s*:\s*' % HEAD_WORDS)

BLOCK_TAGS = r'</?(?:p|div|br|h[1-6]|ul|ol|li|dl|dt|dd)\b[^>]*>'


def blocks(h):
    return [b.strip() for b in re.split(BLOCK_TAGS, h) if b.strip()]


def words(h):
    """Every word in the rendered text, bullet markers and bullet-final ';' aside."""
    t = re.sub(BLOCK_TAGS, ' ', h)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = htmlmod.unescape(t)
    t = t.replace('•', ' ').replace(';', ' ')   # ';' only ever ended a bullet here
    return re.sub(r'\s+', ' ', t).strip().split()


def split_heading(text):
    """One block of text -> list of paragraph strings, headings starting their own."""
    parts, last = [], 0
    for m in head_re.finditer(text):
        parts.append(text[last:m.start()].strip())
        last = m.start(1)
    parts.append(text[last:].strip())
    return [p for p in parts if p]


def fix_block(text):
    """One block -> HTML. Headings start a paragraph; bullets become a <ul>."""
    out = []
    for para in split_heading(text):
        if '\u2022' not in para:
            out.append('<p>%s</p>' % para)
            continue
        lead, *items = para.split('\u2022')
        if lead.strip():
            out.append('<p>%s</p>' % lead.strip())
        lis = []
        for it in items:
            it = it.strip().rstrip(';').strip()
            if it:
                lis.append('<li>%s</li>' % it)
        if lis:
            out.append('<ul>%s</ul>' % ''.join(lis))
    return ''.join(out)


P_RE = re.compile(r'<p\b[^>]*>(.*?)</p>', re.S | re.I)


def needs(inner):
    """True if this paragraph's own text has an inline bullet or run-in heading."""
    for seg in re.split(r'<br\b[^>]*>', inner):
        txt = seg.strip()
        if any(m.start() > 0 for m in re.finditer('\u2022', txt)):
            return True
        if head_re.search(txt):
            return True
    return False


def fix(h):
    """Rewrite only the paragraphs that need it; everything else stays byte-identical."""
    def one(m):
        inner = m.group(1)
        if not needs(inner):
            return m.group(0)
        out = []
        for seg in re.split(r'<br\b[^>]*>', inner):
            seg = seg.strip()
            if seg:
                out.append(fix_block(seg))
        return ''.join(out)
    return P_RE.sub(one, h)


def verify_same(before, after):
    return words(before) == words(after)


if __name__ == '__main__':
    # self-check
    src = ('<p>Intro text here. • One; • Two; • Three. '
           'DIRECTIONS: Do the thing.</p>')
    got = fix(src)
    assert got == ('<p>Intro text here.</p><ul><li>One</li><li>Two</li>'
                   '<li>Three.</li></ul><p>DIRECTIONS: Do the thing.</p>'), got
    src2 = '<p>A sentence here. Product Features: more words follow.</p>'
    assert fix(src2) == '<p>A sentence here.</p><p>Product Features: more words follow.</p>', fix(src2)
    assert verify_same(src, fix(src)) and verify_same(src2, fix(src2))
    # a heading mid-sentence must NOT split
    src3 = '<p>Vitamin b complex contains: thiamine and riboflavin.</p>'
    assert fix(src3) == src3, fix(src3)
    print('self-check ok')

    rows = []
    for line in open(sys.argv[1]):
        p = json.loads(line)
        h = p['descriptionHtml'] or ''
        if not h.strip():
            continue
        new = fix(h)
        if new != h:
            assert verify_same(h, new), p['handle']
            rows.append(dict(id=p['id'], handle=p['handle'], title=p['title'],
                             medicine='pharmacist-review' in p['tags'],
                             before=h, after=new))
    json.dump(rows, open(sys.argv[2], 'w'), indent=1)
    print('changed', len(rows))
