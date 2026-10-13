from pathlib import Path
import sqlite3,os
from datetime import datetime,timezone
state=Path(os.environ.get('BREASTCARE_STATE',str(Path(__file__).parent/'private')))
source=state/'cms.sqlite3'
if not source.is_file():raise SystemExit('Database not found')
target=state/'backups';target.mkdir(exist_ok=True)
with sqlite3.connect(source) as a,sqlite3.connect(target/('cms-'+datetime.now(timezone.utc).strftime('%Y-%m-%d')+'.sqlite3')) as b:a.backup(b)
print('Backup completed')
