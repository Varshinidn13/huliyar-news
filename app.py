from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
import sqlite3, os, uuid, re
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'huliyar_secret_2026_xK9p'
app.jinja_env.globals['enumerate'] = enumerate

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(BASE_DIR, 'news.db')
UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
ALLOWED    = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

EDITOR_PHONE    = '9448760070'
EDITOR_PASSWORD = 'varsh123'
CATEGORIES = ['ಸ್ಥಳೀಯ','ರಾಜಕೀಯ','ರೈತ ಸುದ್ದಿ','ಶಿಕ್ಷಣ','ಕ್ರೀಡೆ','ಧಾರ್ಮಿಕ','ವಾಣಿಜ್ಯ','ತಾಲ್ಲೂಕಿನ ಸುದ್ದಿ','ಅಪರಾಧ']
SITE_URL  = 'https://huliyarbabunews.pythonanywhere.com'
SITE_NAME = 'ಹುಳಿಯಾರು ಸುದ್ದಿ ಸಮಾಚಾರ'

def allowed_file(f):
    return '.' in f and f.rsplit('.',1)[1].lower() in ALLOWED

class MetadataService:
    @staticmethod
    def now():
        return datetime.now().strftime('%d-%m-%Y %I:%M %p')

metadata_service = MetadataService()

def normalize_image_path(value):
    """Keep image references stable and relative to the app/workspace root."""
    if not value:
        return None
    value = value.replace('\\', '/').strip()
    if value.startswith(('http://', 'https://', 'data:')):
        return value
    value = re.sub(r'^(\./|/)+', '', value)
    value = re.sub(r'^(\.\./)+', '', value)
    if value.startswith('static/uploads/'):
        return value
    return 'static/uploads/' + os.path.basename(value)

def media_static_filename(value):
    value = normalize_image_path(value)
    if not value:
        return ''
    return value[len('static/'):] if value.startswith('static/') else value

def media_url(value):
    if not value:
        return ''
    if value.startswith(('http://', 'https://', 'data:')):
        return value
    return url_for('static', filename=media_static_filename(value))

def public_media_url(value):
    if not value:
        return SITE_URL + '/static/logo.png'
    if value.startswith(('http://', 'https://', 'data:')):
        return value
    return SITE_URL + '/' + normalize_image_path(value)

def upload_abs_path(value):
    value = normalize_image_path(value)
    if not value or not value.startswith('static/uploads/'):
        return None
    return os.path.join(BASE_DIR, *value.split('/'))

def strip_jpeg_metadata(path):
    try:
        with open(path, 'rb') as f:
            data = f.read()
        if len(data) < 4 or data[:2] != b'\xff\xd8':
            return
        chunks = [data[:2]]
        offset = 2
        while offset + 4 <= len(data):
            if data[offset] != 0xff:
                chunks.append(data[offset:])
                break
            marker = data[offset + 1]
            if marker == 0xda:
                chunks.append(data[offset:])
                break
            size = int.from_bytes(data[offset + 2:offset + 4], 'big')
            end = offset + 2 + size
            if size < 2 or end > len(data):
                return
            is_metadata = (0xe0 <= marker <= 0xef) or marker == 0xfe
            if not is_metadata:
                chunks.append(data[offset:end])
            offset = end
        optimized = b''.join(chunks)
        if len(optimized) < len(data):
            with open(path, 'wb') as f:
                f.write(optimized)
    except OSError:
        return

def save_uploaded_image(file_storage):
    ext = file_storage.filename.rsplit('.',1)[1].lower()
    fname = uuid.uuid4().hex + '.' + ext
    abs_path = os.path.join(UPLOAD_DIR, fname)
    file_storage.save(abs_path)
    if os.path.getsize(abs_path) > 500 * 1024:
        strip_jpeg_metadata(abs_path)
    return normalize_image_path(fname)

app.jinja_env.globals['media_url'] = media_url

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS news (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        title         TEXT NOT NULL,
        category      TEXT NOT NULL,
        image         TEXT,
        views         INTEGER DEFAULT 0,
        created_at    TEXT NOT NULL,
        updated_at    TEXT,
        breaking_news INTEGER DEFAULT 0
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS content_blocks (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        news_id  INTEGER NOT NULL,
        position INTEGER NOT NULL,
        type     TEXT NOT NULL,
        content  TEXT
    )''')
    conn.commit()
    # migrate old content column
    cols = [r[1] for r in conn.execute("PRAGMA table_info(news)").fetchall()]
    if 'updated_at' not in cols:
        conn.execute('ALTER TABLE news ADD COLUMN updated_at TEXT')
        conn.execute('UPDATE news SET updated_at=created_at WHERE updated_at IS NULL')
        conn.commit()
    if 'content' in cols:
        rows = conn.execute('SELECT id,content FROM news WHERE content IS NOT NULL').fetchall()
        for r in rows:
            ex = conn.execute('SELECT id FROM content_blocks WHERE news_id=?',(r['id'],)).fetchone()
            if not ex:
                conn.execute('INSERT INTO content_blocks (news_id,position,type,content) VALUES (?,0,?,?)',
                             (r['id'],'text',r['content']))
        conn.commit()
    # seed
    if conn.execute('SELECT COUNT(*) FROM news').fetchone()[0] == 0:
        seeds = [
            ('ಅಶಕ್ತರಿಗೆ ಆಸರೆಯಾದ ಧರ್ಮಸ್ಥಳ ಯೋಜನೆ: ವೀಲ್ ಚೇರ್ ವಿತರಣೆ','ಸ್ಥಳೀಯ',None,139,'31-03-2026 09:12 AM',0,'ಧರ್ಮಸ್ಥಳ ಯೋಜನೆಯಡಿ ಅಶಕ್ತ ಫಲಾನುಭವಿಗಳಿಗೆ ವೀಲ್ ಚೇರ್ ವಿತರಿಸಲಾಯಿತು.'),
            ('ಗಾಂಧಿ ಪೇಟೆಯಲ್ಲಿ ಮನೆ ಕಳ್ಳತನ','ಅಪರಾಧ',None,357,'25-03-2026 06:56 PM',1,'ಗಾಂಧಿ ಪೇಟೆಯಲ್ಲಿ ಕಳ್ಳತನ ಪ್ರಕರಣ. ಪೊಲೀಸರು ತನಿಖೆ ಆರಂಭಿಸಿದ್ದಾರೆ.'),
            ('26 ವರ್ಷಗಳ ಬಳಿಕ ತರಬೇನಹಳ್ಳಿ ಹಾಲು ಉತ್ಪಾದಕರ ಸಂಘಕ್ಕೆ ಚುನಾವಣೆ','ರೈತ ಸುದ್ದಿ',None,274,'21-03-2026 04:49 PM',0,'26 ವರ್ಷಗಳ ನಂತರ ಚುನಾವಣೆ ನಡೆದು ಹೊಸ ಆಡಳಿತ ಮಂಡಳಿ ಆಯ್ಕೆ ಆಗಿದೆ.'),
            ('ಶ್ರೀ ದುರ್ಗಾಪರಮೇಶ್ವರಿ ಅಮ್ಮನವರ 54ನೇ ಜಾತ್ರಾ ಮಹೋತ್ಸವ','ಧಾರ್ಮಿಕ',None,168,'24-03-2026 10:24 AM',0,'ಹುಳಿಯಾರಿನಲ್ಲಿ ಜಾತ್ರಾ ಮಹೋತ್ಸವ ಭವ್ಯವಾಗಿ ಜರುಗಿತು.'),
            ('ನಕಲಿ ಚಿನ್ನ ಮಾರಾಟ ಜಾಲ ಬಹಿರಂಗ: ಮೂವರು ಬಂಧನ','ಅಪರಾಧ',None,412,'05-04-2026 11:30 AM',1,'ನಕಲಿ ಚಿನ್ನ ಮಾರಾಟ ಜಾಲ ಬಹಿರಂಗ. ಪೊಲೀಸರು ಮೂವರನ್ನು ಬಂಧಿಸಿದ್ದಾರೆ.'),
        ]
        for s in seeds:
            conn.execute('INSERT INTO news (title,category,image,views,created_at,updated_at,breaking_news) VALUES (?,?,?,?,?,?,?)',
                         (s[0], s[1], normalize_image_path(s[2]) if s[2] else None, s[3], s[4], s[4], s[5]))
            nid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            conn.execute('INSERT INTO content_blocks (news_id,position,type,content) VALUES (?,0,?,?)',(nid,'text',s[6]))
        conn.commit()
    conn.close()

def save_blocks(conn, nid, form, files):
    """Save content blocks from editor form for a given news id."""
    position = 0
    indexes = set()
    for key in list(form.keys()) + list(files.keys()):
        m = re.match(r'^(?:content|block_image|existing_block_image)_(\d+)$', key)
        if m:
            indexes.add(int(m.group(1)))
    used_images = set()
    for idx in sorted(indexes):
        text_key  = 'content_{}'.format(idx)
        image_key = 'block_image_{}'.format(idx)
        existing_key = 'existing_block_image_{}'.format(idx)
        txt = form.get(text_key,'').strip()
        if txt:
            conn.execute('INSERT INTO content_blocks (news_id,position,type,content) VALUES (?,?,?,?)',
                         (nid, position, 'text', txt))
            position += 1
        img_path = None
        imgf = files.get(image_key)
        if imgf and imgf.filename and allowed_file(imgf.filename):
            img_path = save_uploaded_image(imgf)
        elif form.get(existing_key):
            img_path = normalize_image_path(form.get(existing_key))
        if img_path:
            used_images.add(img_path)
            conn.execute('INSERT INTO content_blocks (news_id,position,type,content) VALUES (?,?,?,?)',
                         (nid, position, 'image', img_path))
            position += 1
    return used_images

# ── ROUTES ──────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    conn = get_db()
    news     = conn.execute('SELECT * FROM news ORDER BY id DESC').fetchall()
    trending = conn.execute('SELECT * FROM news ORDER BY views DESC LIMIT 10').fetchall()
    breaking = conn.execute('SELECT * FROM news WHERE breaking_news=1 ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', news=news, trending=trending, breaking=breaking,
                           categories=CATEGORIES, active_cat=None,
                           site_url=SITE_URL, site_name=SITE_NAME)

@app.route('/category/<cat>')
def category(cat):
    conn = get_db()
    news     = conn.execute('SELECT * FROM news WHERE category=? ORDER BY id DESC',(cat,)).fetchall()
    trending = conn.execute('SELECT * FROM news ORDER BY views DESC LIMIT 10').fetchall()
    breaking = conn.execute('SELECT * FROM news WHERE breaking_news=1 ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', news=news, trending=trending, breaking=breaking,
                           categories=CATEGORIES, active_cat=cat,
                           site_url=SITE_URL, site_name=SITE_NAME)

@app.route('/news/<int:nid>')
def news_detail(nid):
    conn = get_db()
    conn.execute('UPDATE news SET views=views+1 WHERE id=?',(nid,))
    conn.commit()
    article = conn.execute('SELECT * FROM news WHERE id=?',(nid,)).fetchone()
    if not article:
        conn.close(); abort(404)
    blocks  = conn.execute('SELECT * FROM content_blocks WHERE news_id=? ORDER BY position',(nid,)).fetchall()
    recent  = conn.execute('SELECT * FROM news ORDER BY id DESC LIMIT 7').fetchall()
    conn.close()
    og_image = public_media_url(article['image'])
    return render_template('news_detail.html', article=article, blocks=blocks, recent=recent,
                           categories=CATEGORIES, og_image=og_image,
                           site_url=SITE_URL, site_name=SITE_NAME)

# ── EDITOR ──────────────────────────────────────────────────────────────────

@app.route('/editor/login', methods=['GET','POST'])
def editor_login():
    if request.method == 'POST':
        if (request.form.get('phone','').strip() == EDITOR_PHONE and
                request.form.get('password','').strip() == EDITOR_PASSWORD):
            session['editor'] = True
            return redirect(url_for('editor_dashboard'))
        flash('error:ತಪ್ಪಾದ ಫೋನ್ ನಂಬರ್ ಅಥವಾ ಪಾಸ್‌ವರ್ಡ್')
    return render_template('editor_login.html')

@app.route('/editor/logout')
def editor_logout():
    session.pop('editor', None)
    return redirect(url_for('home'))

@app.route('/editor')
def editor_dashboard():
    if not session.get('editor'):
        return redirect(url_for('editor_login'))
    conn = get_db()
    news = conn.execute('SELECT * FROM news ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('editor_dashboard.html', news=news, categories=CATEGORIES)

@app.route('/editor/post', methods=['GET','POST'])
def editor_post():
    if not session.get('editor'):
        return redirect(url_for('editor_login'))
    if request.method == 'POST':
        title         = request.form.get('title','').strip()
        category      = request.form.get('category','ಸ್ಥಳೀಯ')
        breaking_news = 1 if request.form.get('breaking_news') else 0
        hero_img = None
        f = request.files.get('hero_image')
        if f and f.filename and allowed_file(f.filename):
            hero_img = save_uploaded_image(f)
        if not title:
            flash('error:ಶೀರ್ಷಿಕೆ ಬರೆಯಿರಿ')
            return render_template('editor_post.html', categories=CATEGORIES)
        now = metadata_service.now()
        conn = get_db()
        conn.execute('INSERT INTO news (title,category,image,views,created_at,updated_at,breaking_news) VALUES (?,?,?,0,?,?,?)',
                     (title, category, hero_img, now, now, breaking_news))
        nid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        save_blocks(conn, nid, request.form, request.files)
        conn.commit()
        conn.close()
        flash('success:ಸುದ್ದಿ ಯಶಸ್ವಿಯಾಗಿ ಪ್ರಕಟವಾಗಿದೆ!')
        return redirect(url_for('editor_dashboard'))
    return render_template('editor_post.html', categories=CATEGORIES)

@app.route('/editor/edit/<int:nid>', methods=['GET','POST'])
def editor_edit(nid):
    if not session.get('editor'):
        return redirect(url_for('editor_login'))
    conn = get_db()
    article = conn.execute('SELECT * FROM news WHERE id=?',(nid,)).fetchone()
    if not article:
        conn.close(); abort(404)
    if request.method == 'POST':
        title         = request.form.get('title','').strip()
        category      = request.form.get('category','ಸ್ಥಳೀಯ')
        breaking_news = 1 if request.form.get('breaking_news') else 0
        # Handle hero image — keep old if no new uploaded
        hero_img = normalize_image_path(article['image'])
        f = request.files.get('hero_image')
        if f and f.filename and allowed_file(f.filename):
            old_hero = upload_abs_path(hero_img)
            hero_img = save_uploaded_image(f)
            if old_hero and os.path.exists(old_hero):
                os.remove(old_hero)
        if not title:
            flash('error:ಶೀರ್ಷಿಕೆ ಬರೆಯಿರಿ')
            blocks = conn.execute('SELECT * FROM content_blocks WHERE news_id=? ORDER BY position',(nid,)).fetchall()
            conn.close()
            return render_template('editor_edit.html', article=article, blocks=blocks, categories=CATEGORIES)
        now = metadata_service.now()
        conn.execute('UPDATE news SET title=?,category=?,image=?,updated_at=?,breaking_news=? WHERE id=?',
                     (title, category, hero_img, now, breaking_news, nid))
        # Delete old blocks and re-save
        old_imgs = {
            normalize_image_path(oi['content'])
            for oi in conn.execute('SELECT content FROM content_blocks WHERE news_id=? AND type=?',(nid,'image')).fetchall()
        }
        conn.execute('DELETE FROM content_blocks WHERE news_id=?',(nid,))
        used_imgs = save_blocks(conn, nid, request.form, request.files)
        for old_img in old_imgs - used_imgs:
            p = upload_abs_path(old_img)
            if p and os.path.exists(p): os.remove(p)
        conn.commit()
        conn.close()
        flash('success:ಸುದ್ದಿ ಯಶಸ್ವಿಯಾಗಿ ಅಪ್ಡೇಟ್ ಆಗಿದೆ!')
        return redirect(url_for('editor_dashboard'))
    blocks = conn.execute('SELECT * FROM content_blocks WHERE news_id=? ORDER BY position',(nid,)).fetchall()
    conn.close()
    return render_template('editor_edit.html', article=article, blocks=blocks, categories=CATEGORIES)

@app.route('/editor/delete/<int:nid>')
def editor_delete(nid):
    if not session.get('editor'):
        return redirect(url_for('editor_login'))
    conn = get_db()
    row = conn.execute('SELECT image FROM news WHERE id=?',(nid,)).fetchone()
    if row and row['image']:
        p = upload_abs_path(row['image'])
        if p and os.path.exists(p): os.remove(p)
    imgs = conn.execute('SELECT content FROM content_blocks WHERE news_id=? AND type=?',(nid,'image')).fetchall()
    for i in imgs:
        p = upload_abs_path(i['content'])
        if p and os.path.exists(p): os.remove(p)
    conn.execute('DELETE FROM content_blocks WHERE news_id=?',(nid,))
    conn.execute('DELETE FROM news WHERE id=?',(nid,))
    conn.commit()
    conn.close()
    flash('success:ಸುದ್ದಿ ಅಳಿಸಲಾಗಿದೆ')
    return redirect(url_for('editor_dashboard'))

@app.route('/editor/upload-logo', methods=['POST'])
def upload_logo():
    if not session.get('editor'):
        return redirect(url_for('editor_login'))
    f = request.files.get('logo')
    if f and f.filename and allowed_file(f.filename):
        dest = os.path.join(STATIC_DIR, 'logo.png')
        if os.path.exists(dest): os.remove(dest)
        f.save(dest)
        flash('success:ಲೋಗೋ ಅಪ್ಲೋಡ್ ಆಗಿದೆ! Web tab -> Reload ಮಾಡಿ.')
    else:
        flash('error:ದಯವಿಟ್ಟು JPG/PNG ಆಯ್ಕೆ ಮಾಡಿ')
    return redirect(url_for('editor_dashboard'))

# ── INIT ─────────────────────────────────────────────────────────────────────
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
