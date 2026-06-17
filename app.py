from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
import sqlite3, os, uuid
from datetime import datetime
import pytz
from werkzeug.utils import secure_filename
from PIL import Image

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

def save_compressed_image(file, folder, filename, max_size=(800, 600)):
    """Save and compress image for WhatsApp preview optimization."""
    img = Image.open(file)
    # Convert to RGB if necessary (to save as JPEG)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    # Resize if larger than max_size while maintaining aspect ratio
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Save with optimization
    path = os.path.join(folder, filename)
    img.save(path, "JPEG", optimize=True, quality=85)
    return filename

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
    if 'content' in cols:
        rows = conn.execute('SELECT id,content FROM news WHERE content IS NOT NULL').fetchall()
        for r in rows:
            ex = conn.execute('SELECT id FROM content_blocks WHERE news_id=?',(r['id'],)).fetchone()
            if not ex:
                conn.execute('INSERT INTO content_blocks (news_id,position,type,content) VALUES (?,0,?,?)',
                             (r['id'],'text',r['content']))
        conn.commit()
    # migrate: add caption column
    cols = [r[1] for r in conn.execute("PRAGMA table_info(content_blocks)").fetchall()]
    if 'caption' not in cols:
        conn.execute("ALTER TABLE content_blocks ADD COLUMN caption TEXT DEFAULT ''")
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
            conn.execute('INSERT INTO news (title,category,image,views,created_at,breaking_news) VALUES (?,?,?,?,?,?)', s[:6])
            nid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            conn.execute('INSERT INTO content_blocks (news_id,position,type,content) VALUES (?,0,?,?)',(nid,'text',s[6]))
        conn.commit()
    conn.close()

def save_blocks(conn, nid, form, files):
    """Save content blocks from editor form for a given news id."""
    position = 0
    idx = 0
    while True:
        text_key   = 'content_{}'.format(idx)
        image_key  = 'block_image_{}'.format(idx)
        caption_key = 'caption_{}'.format(idx)
        has_text  = text_key in form
        has_image = image_key in files
        if not has_text and not has_image:
            break
        if has_text:
            txt = form.get(text_key,'').strip()
            if txt:
                conn.execute('INSERT INTO content_blocks (news_id,position,type,content) VALUES (?,?,?,?)',
                             (nid, position, 'text', txt))
                position += 1
        if has_image:
            imgf = files.get(image_key)
            if imgf and imgf.filename and allowed_file(imgf.filename):
                fname = uuid.uuid4().hex + '.jpg'
                save_compressed_image(imgf, UPLOAD_DIR, fname)
                caption = form.get(caption_key, '').strip()
                conn.execute('INSERT INTO content_blocks (news_id,position,type,content,caption) VALUES (?,?,?,?,?)',
                             (nid, position, 'image', fname, caption))
                position += 1
        idx += 1

def media_url(filename):
    if filename:
        return url_for('static', filename='uploads/' + filename)
    return url_for('static', filename='logo.png')
app.jinja_env.globals['media_url'] = media_url

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
    og_image = SITE_URL + ('/static/uploads/'+article['image'] if article['image'] else '/static/logo.png')
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
            hero_img = uuid.uuid4().hex + '.jpg'
            save_compressed_image(f, UPLOAD_DIR, hero_img)
        if not title:
            flash('error:ಶೀರ್ಷಿಕೆ ಬರೆಯಿರಿ')
            return render_template('editor_post.html', categories=CATEGORIES)
        # Set timezone to Asia/Kolkata (IST)
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist).strftime('%d-%m-%Y %I:%M %p')
        conn = get_db()
        conn.execute('INSERT INTO news (title,category,image,views,created_at,breaking_news) VALUES (?,?,?,0,?,?)',
                     (title, category, hero_img, now, breaking_news))
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
        hero_img = article['image']
        f = request.files.get('hero_image')
        if f and f.filename and allowed_file(f.filename):
            # delete old hero
            if hero_img:
                old = os.path.join(UPLOAD_DIR, hero_img)
                if os.path.exists(old): os.remove(old)
            hero_img = uuid.uuid4().hex + '.jpg'
            save_compressed_image(f, UPLOAD_DIR, hero_img)
        if not title:
            flash('error:ಶೀರ್ಷಿಕೆ ಬರೆಯಿರಿ')
            blocks = conn.execute('SELECT * FROM content_blocks WHERE news_id=? ORDER BY position',(nid,)).fetchall()
            conn.close()
            return render_template('editor_edit.html', article=article, blocks=blocks, categories=CATEGORIES)
        
        conn.execute('UPDATE news SET title=?,category=?,image=?,breaking_news=? WHERE id=?',
                     (title, category, hero_img, breaking_news, nid))

        # Get existing blocks to handle images
        existing_blocks = conn.execute('SELECT * FROM content_blocks WHERE news_id=? ORDER BY position', (nid,)).fetchall()
        
        # We will delete and re-save, but keep existing image filenames if no new file provided
        conn.execute('DELETE FROM content_blocks WHERE news_id=?', (nid,))
        
        position = 0
        idx = 0
        while True:
            text_key    = 'content_{}'.format(idx)
            image_key   = 'block_image_{}'.format(idx)
            caption_key = 'caption_{}'.format(idx)
            # Check if this block index exists in the submitted form
            if text_key not in request.form and image_key not in request.files:
                # Also check if it was an existing block that might only have an image
                if idx >= len(existing_blocks):
                    break
            
            txt = request.form.get(text_key, '').strip()
            imgf = request.files.get(image_key)
            caption = request.form.get(caption_key, '').strip()
            
            # Logic for image:
            # 1. New file uploaded -> save it
            # 2. No new file, but was an existing image block -> keep old filename
            # 3. No new file, no old image -> no image
            
            saved_image = None
            if imgf and imgf.filename and allowed_file(imgf.filename):
                saved_image = uuid.uuid4().hex + '.jpg'
                save_compressed_image(imgf, UPLOAD_DIR, saved_image)
            elif idx < len(existing_blocks) and existing_blocks[idx]['type'] == 'image':
                saved_image = existing_blocks[idx]['content']
                # Preserve existing caption if no new caption submitted
                if not caption:
                    caption = existing_blocks[idx]['caption'] or ''

            if txt:
                conn.execute('INSERT INTO content_blocks (news_id,position,type,content) VALUES (?,?,?,?)',
                             (nid, position, 'text', txt))
                position += 1
            
            if saved_image:
                conn.execute('INSERT INTO content_blocks (news_id,position,type,content,caption) VALUES (?,?,?,?,?)',
                             (nid, position, 'image', saved_image, caption))
                position += 1
                
            idx += 1

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
        p = os.path.join(UPLOAD_DIR, row['image'])
        if os.path.exists(p): os.remove(p)
    imgs = conn.execute('SELECT content FROM content_blocks WHERE news_id=? AND type=?',(nid,'image')).fetchall()
    for i in imgs:
        p = os.path.join(UPLOAD_DIR, i['content'])
        if os.path.exists(p): os.remove(p)
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
