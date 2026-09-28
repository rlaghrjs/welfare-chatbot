"""Build frozen migration SQL and the reviewable ERD from the implemented metadata."""
import os
from pathlib import Path

# No credentials or database connection are needed to compile metadata.
os.environ.update(DATABASE_URL="sqlite://", WELFARE_API_URL="https://example.com", WELFARE_API_KEY="test",
                  LOCAL_WELFARE_API_URL="https://example.com", LOCAL_WELFARE_API_KEY="test", OPENAI_API_KEY="test")
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql
from app.db.database import Base
import app.models

root = Path(__file__).resolve().parents[1]
tables = [t for t in Base.metadata.sorted_tables if t.name not in {"chat_sessions", "chat_messages", "welfare_api_results"}]
sql = []
for table in tables:
    sql.append(str(CreateTable(table).compile(dialect=postgresql.dialect())).strip() + ";")
    sql.extend(str(CreateIndex(i).compile(dialect=postgresql.dialect())).strip() + ";" for i in sorted(table.indexes, key=lambda i: i.name))
target = root / "migrations/versions/0002_tables.sql"
if not target.exists():
    target.write_text("\n\n".join(sql) + "\n", encoding="utf-8")

active = [t for t in Base.metadata.sorted_tables if t.name != "welfare_api_results"]
lines = ["erDiagram"]
for table in active:
    lines.append(f"    {table.name.upper()} {{")
    for c in table.columns:
        kind = str(c.type).split('(')[0].replace(' ', '_').lower()
        key = " PK" if c.primary_key else " FK" if c.foreign_keys else ""
        lines.append(f"        {kind} {c.name}{key}")
    lines.append("    }")
    for fk in table.foreign_keys:
        parent = fk.column.table.name.upper()
        optional = "o|" if fk.parent.nullable else "||"
        lines.append(f'    {parent} {optional}--o{{ {table.name.upper()} : "{fk.parent.name}"')
(root / "artifacts/welfare_erd_v2.mmd").write_text("\n".join(lines), encoding="utf-8")

from PIL import Image, ImageDraw, ImageFont
im = Image.new("RGB", (4000, 3350), "white")
d = ImageDraw.Draw(im)
def txt(x,y,s,size=28,bold=False):
    f=ImageFont.truetype("C:/Windows/Fonts/"+("malgunbd.ttf" if bold else "malgun.ttf"), size)
    d.text((x,y),s,font=f,fill="black")
txt(100,45,"복지 챗봇 ERD · 익명 설치와 조건 구독",54,True)
txt(100,120,"회원 계정 없음  |  첫 메시지에서 채팅 생성  |  기록 삭제와 구독 해제 분리",30)

# Relationship overview, kept separate from field cards for readable routing.
nodes = {
 'app_installations':(100,220), 'profiles':(1050,220), 'condition_subscriptions':(2000,220),
 'chat_sessions':(100,425), 'chat_messages':(1050,425), 'notification_matches':(2000,425),
 'chat_search_results':(1050,630), 'notifications':(2000,630),
 'welfare_policies':(100,835), 'welfare_policy_versions':(1050,835),
 'policy_eligibility_rules':(2000,835), 'sync_runs':(2950,835),
}
nw,nh=800,90
def link(a,b,route=None):
    ax,ay=nodes[a]; bx,by=nodes[b]
    if ax==bx:
        p=(ax+nw/2,ay+nh if by>ay else ay); q=(bx+nw/2,by if by>ay else by+nh)
    elif ay==by:
        p=(ax+nw if bx>ax else ax,ay+nh/2); q=(bx if bx>ax else bx+nw,by+nh/2)
    else:
        p=(ax+nw,ay+nh/2); q=(bx,by+nh/2)
    pts=[p,*(route or []),q]
    d.line(pts,fill='black',width=3)
    ex,ey=q; sx,sy=pts[-2]; length=((sx-ex)**2+(sy-ey)**2)**0.5
    ux,uy=(sx-ex)/length,(sy-ey)/length
    d.polygon([(ex,ey),(ex+ux*20-uy*9,ey+uy*20+ux*9),(ex+ux*20+uy*9,ey+uy*20-ux*9)],fill='black')
link('app_installations','profiles'); link('profiles','condition_subscriptions')
link('app_installations','chat_sessions'); link('chat_sessions','chat_messages')
link('chat_messages','chat_search_results'); link('condition_subscriptions','notification_matches')
link('notifications','notification_matches'); link('welfare_policies','welfare_policy_versions')
link('welfare_policy_versions','chat_search_results'); link('welfare_policy_versions','policy_eligibility_rules')
d.line([(3350,925),(3350,1000),(1450,1000),(1450,925)],fill='black',width=3)
d.polygon([(1450,925),(1441,945),(1459,945)],fill='black')
link('welfare_policy_versions','notifications',[(1900,880),(1900,675)])
for name,(x,y) in nodes.items():
    d.rounded_rectangle((x,y,x+nw,y+nh),radius=8,fill='#f1f3f5',outline='black',width=3)
    txt(x+20,y+24,name.upper(),29,True)
txt(2950,240,'관계: 부모 → 자식 (1:N)',29,True)
txt(2950,300,'설치 → 구독, 설치 → 알림도 연결',25)
txt(2950,350,'프로필 참조는 선택 사항',25)
txt(2950,400,'구독 삭제 후에도 알림 근거 보존',25)
txt(2950,450,'제도·버전은 채팅 삭제와 무관',25)
txt(2950,500,'아래 카드: 구현된 컬럼 전체',25)
txt(2950,550,'PK 기본키 / FK 외래키 / ? 선택',25)

order = ['app_installations','profiles','condition_subscriptions','notifications',
         'chat_sessions','chat_messages','chat_search_results','notification_matches',
         'welfare_policies','welfare_policy_versions','policy_eligibility_rules','sync_runs']
labels=['익명 앱 설치','선택 프로필','조건 구독','알림','채팅 기록','메시지','검색 결과 연결','알림 일치 근거','제도 최신 정보','제도 변경 이력','공식 대상 조건','수집 실행 기록']
for n,name in enumerate(order):
    x=100+(n%4)*960; y=1060+(n//4)*690; w=900; h=650
    d.rectangle((x,y,x+w,y+h),fill='white',outline='black',width=3)
    d.rectangle((x+2,y+2,x+w-2,y+97),fill='#f1f3f5')
    txt(x+20,y+10,name.upper(),29,True); txt(x+20,y+53,labels[n],27)
    columns = sorted(Base.metadata.tables[name].columns, key=lambda c: not c.primary_key)
    for i,c in enumerate(columns):
        key='PK' if c.primary_key else 'FK' if c.foreign_keys else '  '
        kind=str(c.type).split('(')[0].lower().replace('datetime','timestamp')
        txt(x+20,y+115+i*37,f'{key}  {c.name}{" ?" if c.nullable else ""} : {kind}',25)
txt(100,3160,'고유 제약: 제도(source, external_id) · 버전(policy_id, version_no) · 검색 결과(message_id, policy_version_id)',27)
txt(100,3205,'알림(installation_id, policy_version_id, channel) · 알림 근거(notification_id, subscription_id)',27)
txt(100,3250,'이행기 예외: 소유자 미확인 과거 채팅은 installation_id=NULL로 보존. 기존 검색 응답 테이블은 별도 보존.',26)
txt(100,3290,'기존 status/ended_at는 legacy 컬럼으로 보존하며 신규 채팅 흐름에서는 사용하지 않습니다.',26)
im.save(root/'artifacts/welfare_erd_v2.png')
print('Created frozen migration SQL, Mermaid source and ERD PNG.')
