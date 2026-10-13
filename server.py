"""Local CMS: Python standard library, SQLite, authenticated sessions."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import sqlite3,json,secrets,hashlib,time,os
from urllib.parse import urlparse,parse_qs,unquote
ROOT=Path(__file__).resolve().parent
STATE=Path(os.environ.get('BREASTCARE_STATE',str(ROOT/'private')));STATE.mkdir(exist_ok=True)
PRODUCTION=os.environ.get('BREASTCARE_PRODUCTION')=='1'
PUBLIC_ORIGIN=os.environ.get('PUBLIC_ORIGIN','').rstrip('/')
DB=STATE/'cms.sqlite3';sessions={};attempts={}
def conn():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def init():
 with conn() as c:
  c.executescript('CREATE TABLE IF NOT EXISTS admin(id INTEGER PRIMARY KEY,password TEXT,salt TEXT); CREATE TABLE IF NOT EXISTS entries(id TEXT PRIMARY KEY,kind TEXT,data TEXT,updated REAL); CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,action TEXT,entry_id TEXT,created REAL);')
 if PRODUCTION:
  if not PUBLIC_ORIGIN.startswith('https://'):raise RuntimeError('Set PUBLIC_ORIGIN to your HTTPS site URL')
  with conn() as c:
   if not c.execute('SELECT 1 FROM admin').fetchone():
    initial=os.environ.get('ADMIN_INITIAL_PASSWORD','')
    if len(initial)<16:raise RuntimeError('Set ADMIN_INITIAL_PASSWORD (at least 16 characters)')
    salt=secrets.token_hex(16);c.execute('INSERT INTO admin(password,salt) VALUES(?,?)',(password(initial,salt),salt))
def password(p,s):return hashlib.pbkdf2_hmac('sha256',p.encode(),bytes.fromhex(s),300000).hex()
def valid(kind,d):
 if kind not in ('courses','resources','certificates'):raise ValueError('未知資料類型')
 if not isinstance(d,dict):raise ValueError('資料格式錯誤')
 allowed={'courses':['title','category','format','content','date','location','fee','status'],'resources':['title','content','youtube','status'],'certificates':['number','name','course','issued','expires','status','public','cities']}[kind]
 raw=d
 d={k:str(d.get(k,'')).strip() for k in allowed if k!='cities'}
 if kind=='courses':
  d['format']=d.get('format') or 'pending'
  if d['format'] not in ('pending','online','in-person','hybrid'):raise ValueError('上課方式不正確')
 if kind=='certificates':
  cities=raw.get('cities',[])
  taiwan=['臺北市','新北市','桃園市','臺中市','臺南市','高雄市','基隆市','新竹市','新竹縣','苗栗縣','彰化縣','南投縣','雲林縣','嘉義市','嘉義縣','屏東縣','宜蘭縣','花蓮縣','臺東縣','澎湖縣','金門縣','連江縣']
  if not isinstance(cities,list) or any(x not in taiwan for x in cities):raise ValueError('請選擇有效的台灣服務縣市')
  d['cities']=list(dict.fromkeys(cities))
 if any(len(v)>15000 for v in d.values() if isinstance(v,str)):raise ValueError('內容過長')
 key='number' if kind=='certificates' else 'title'
 if not d[key]:raise ValueError('請填寫'+('證書編號' if kind=='certificates' else '標題'))
 statuses=['issued','revoked','expired'] if kind=='certificates' else ['draft','published','archived']
 if d['status'] not in statuses:raise ValueError('狀態錯誤')
 if kind=='certificates' and (not d['name'] or not d['issued']):raise ValueError('請填寫姓名與核發日期')
 from datetime import date
 for key in ('issued','expires','date'):
  if d.get(key):
   try:date.fromisoformat(d[key])
   except ValueError:raise ValueError('日期格式不正確')
 if d.get('expires') and d.get('issued') and d['expires']<d['issued']:raise ValueError('有效期限不可早於核發日期')
 if d.get('youtube'):
  u=urlparse(d['youtube']);host=u.hostname or ''
  if u.scheme!='https' or host not in ('youtube.com','www.youtube.com','m.youtube.com','youtu.be') or u.username:raise ValueError('請填入 https YouTube 影片連結')
 return d
class H(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def end_headers(self):
  self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.send_header('Referrer-Policy','strict-origin-when-cross-origin')
  if PRODUCTION:self.send_header('Strict-Transport-Security','max-age=31536000')
  super().end_headers()
 def reply(self,n,d):
  b=json.dumps(d,ensure_ascii=False).encode();self.send_response(n);self.send_header('Content-Type','application/json;charset=utf-8');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
 def session(self):
  cookie=self.headers.get('Cookie','');token=next((x.strip().split('=',1)[1] for x in cookie.split(';') if x.strip().startswith('cms=')),None)
  s=sessions.get(token)
  return s if s and s['until']>time.time() else None
 def do_GET(self):
  path=unquote(urlparse(self.path).path)
  if path=='/api/status':
   with conn() as c:setup=c.execute('SELECT count(*) FROM admin').fetchone()[0]==0
   return self.reply(200,{'setup':setup,'authenticated':bool(self.session()),'csrf':self.session()['csrf'] if self.session() else ''})
  if path=='/api/admin/entries':
   if not self.session():return self.reply(401,{'error':'請先登入'})
   with conn() as c:rows=c.execute('SELECT * FROM entries ORDER BY updated DESC').fetchall()
   return self.reply(200,[{'id':r['id'],'kind':r['kind'],**json.loads(r['data'])} for r in rows])
  if path=='/api/public':
   with conn() as c:rows=c.execute("SELECT * FROM entries WHERE kind!='certificates' ORDER BY updated DESC").fetchall()
   return self.reply(200,[{'id':r['id'],'kind':r['kind'],**json.loads(r['data'])} for r in rows if json.loads(r['data']).get('status')=='published'])
  if path.startswith('/api/'):return self.reply(404,{'error':'找不到此 API'})
  if not (path=='/' or (path.count('/')==1 and path.endswith('.html')) or path.startswith('/assets/')) or '..' in path:return self.reply(403,{'error':'禁止存取'})
  return super().do_GET()
 def do_POST(self):
  # Same-origin writes; browsers send Origin. Non-browser local clients may omit it.
  origin=self.headers.get('Origin')
  if origin and origin!=(PUBLIC_ORIGIN if PRODUCTION else 'http://'+self.headers.get('Host','')):return self.reply(403,{'error':'來源驗證失敗'})
  try:
   size=int(self.headers.get('Content-Length','0'))
   if size<0 or size>100000:raise ValueError('內容過長')
   body=json.loads(self.rfile.read(size));path=urlparse(self.path).path
   if not isinstance(body,dict):raise ValueError('資料格式錯誤')
   if path in ('/api/login','/api/setup','/api/verify'):
    key=(self.client_address[0],path);now=time.time();recent=[t for t in attempts.get(key,[]) if now-t<60]
    if len(recent)>= (5 if path!='/api/verify' else 30):return self.reply(429,{'error':'操作過於頻繁，請稍後再試'})
    attempts[key]=recent+[now]
   if PRODUCTION and path=='/api/setup':return self.reply(403,{'error':'公開服務不開放帳號初始化'})
   if path in ('/api/setup','/api/login'):
    p=str(body.get('password',''))
    with conn() as c:
     r=c.execute('SELECT * FROM admin').fetchone()
     if path=='/api/setup':
      if r:return self.reply(409,{'error':'管理員已設定，請登入'})
      if len(p)<12:raise ValueError('密碼至少需要 12 個字元')
      salt=secrets.token_hex(16);c.execute('INSERT INTO admin(password,salt) VALUES(?,?)',(password(p,salt),salt))
     elif not r or not secrets.compare_digest(password(p,r['salt']),r['password']):return self.reply(401,{'error':'密碼不正確'})
    token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(32);sessions[token]={'csrf':csrf,'until':time.time()+28800}
    self.send_response(200);self.send_header('Set-Cookie',f'cms={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800'+('; Secure' if PRODUCTION else ''));self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps({'csrf':csrf}).encode());return
   if path=='/api/verify':
    number=str(body.get('number','')).strip()
    with conn() as c:rows=c.execute("SELECT data FROM entries WHERE kind='certificates'").fetchall()
    d=next((json.loads(r['data']) for r in rows if json.loads(r['data']).get('number')==number and json.loads(r['data']).get('public')=='yes'),None)
    if not d:return self.reply(200,{'message':'查無已開放公開查詢的紀錄，請向協會確認。此結果不代表證書無效。'})
    from datetime import date
    expired=bool(d.get('expires') and d['expires']<date.today().isoformat())
    status='expired' if d['status']=='issued' and expired else d['status']
    return self.reply(200,{'number':d['number'],'course':d['course'],'issued':d['issued'],'expires':d['expires'],'status':status,'cities':d.get('cities',[])})
   s=self.session()
   if not s:return self.reply(401,{'error':'請先登入'})
   if self.headers.get('X-CSRF-Token')!=s['csrf']:return self.reply(403,{'error':'登入驗證已失效，請重新登入'})
   if path=='/api/logout':
    s['until']=0;return self.reply(200,{'ok':True})
   if path=='/api/save':
    kind=body.get('kind');d=valid(kind,body.get('data'));id=body.get('id') or secrets.token_hex(12)
    with conn() as c:
     existing=c.execute('SELECT kind FROM entries WHERE id=?',(id,)).fetchone()
     if existing and existing['kind']!=kind:raise ValueError('不能變更資料類型')
     if kind=='certificates':
      for r in c.execute("SELECT id,data FROM entries WHERE kind='certificates'"):
       if r['id']!=id and json.loads(r['data'])['number']==d['number']:raise ValueError('證書編號已存在')
     c.execute('INSERT INTO entries VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data,updated=excluded.updated',(id,kind,json.dumps(d,ensure_ascii=False),time.time()))
     c.execute('INSERT INTO audit(action,entry_id,created) VALUES(?,?,?)',('save:'+kind,id,time.time()))
    return self.reply(200,{'ok':True,'id':id})
   return self.reply(404,{'error':'找不到此 API'})
  except (ValueError,TypeError,KeyError) as e:return self.reply(400,{'error':str(e)})
 def do_HEAD(self):
  path=unquote(urlparse(self.path).path)
  if '..' in path or not (path=='/' or (path.count('/')==1 and path.endswith('.html')) or path.startswith('/assets/')):return self.reply(403,{'error':'禁止存取'})
  super().do_HEAD()
 def list_directory(self,path):return self.reply(403,{'error':'禁止目錄瀏覽'})
if __name__=='__main__':
 init();host='0.0.0.0' if PRODUCTION else '127.0.0.1';port=int(os.environ.get('PORT','8080'));print('Website service started',flush=True);ThreadingHTTPServer((host,port),H).serve_forever()
