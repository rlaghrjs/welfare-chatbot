from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUT = Path(__file__).resolve().parent
im = Image.new('RGB', (3000, 2830), 'white')
d = ImageDraw.Draw(im)
font_path = 'C:/Windows/Fonts/malgun.ttf'
bold_path = 'C:/Windows/Fonts/malgunbd.ttf'
def font(size, bold=False):
    return ImageFont.truetype(bold_path if bold else font_path, size)
def text(x,y,s,size=27,bold=False):
    d.text((x,y),s,font=font(size,bold),fill='black')

tables = [
('USERS','사용자',0,0, ['PK  id : uuid','UK  email : string (선택)','created_at : datetime']),
('CHAT_SESSIONS','채팅 세션',1,0,['PK  id : uuid','FK  user_id : uuid (비회원 NULL)','title : string','status : string','created_at : datetime','ended_at : datetime']),
('CHAT_MESSAGES','채팅 메시지',2,0,['PK  id : uuid','FK  session_id : uuid','role : string','content : text','message_type : string','message_metadata : jsonb','created_at : datetime']),
('POLICY_SUBSCRIPTIONS','관심 제도 구독',0,1,['PK  id : uuid','FK  user_id : uuid','FK  policy_id : uuid','notifications_enabled : boolean','created_at : datetime']),
('WELFARE_POLICIES','제도 최신 정보',1,1,['PK  id : uuid','source : string','external_id : string','name : string / summary : text','search_attributes : jsonb','availability_status : string','content_hash : string','raw_data : jsonb','first_seen_at : datetime','last_seen_at : datetime','content_updated_at : datetime']),
('CHAT_SEARCH_RESULTS','채팅 검색 결과',2,1,['PK  id : uuid','FK  message_id : uuid','FK  policy_version_id : uuid','rank : int (표시 순서)']),
('NOTIFICATIONS','사용자 알림',0,2,['PK  id : uuid','FK  user_id : uuid','FK  policy_version_id : uuid','channel : string','title : text / body : text','delivery_status : string','attempt_count : int','next_attempt_at : datetime','sent_at : datetime','read_at : datetime','created_at : datetime']),
('WELFARE_POLICY_VERSIONS','제도 변경 이력',1,2,['PK  id : uuid','FK  policy_id : uuid','FK  sync_run_id : uuid','version_no : int','change_type : string','snapshot : jsonb','changes : jsonb','detected_at : datetime']),
('SYNC_RUNS','API 수집 실행 기록',2,2,['PK  id : uuid','source : string','status : string','checkpoint : jsonb','fetched_count : int','created_count : int','updated_count : int','failed_count : int','error_summary : text','started_at : datetime','finished_at : datetime']),
]
W,H=780,650
boxes={name:(180+col*930,190+row*810) for name,_,col,row,_ in tables}
def point(name,side):
    x,y=boxes[name]
    return {'l':(x,y+H/2),'r':(x+W,y+H/2),'t':(x+W/2,y),'b':(x+W/2,y+H)}[side]
def edge(a,sa,b,sb,n,via=()):
    p,q=point(a,sa),point(b,sb)
    pts=[p,*via,q]
    d.line(pts,fill='black',width=3)
    # Crow's foot at child; single bar at parent.
    for endpoint,near,many in [(p,pts[1],False),(q,pts[-2],True)]:
        x,y=endpoint; dx=near[0]-x; dy=near[1]-y
        length=(dx*dx+dy*dy)**0.5; ux,uy=dx/length,dy/length
        vx,vy=-uy,ux
        if many:
            tip=(x+ux*25,y+uy*25)
            for s in [-1,0,1]:
                d.line([tip,(x+vx*s*13,y+vy*s*13)],fill='black',width=3)
        else:
            cx,cy=x+ux*19,y+uy*19
            d.line([(cx+vx*12,cy+vy*12),(cx-vx*12,cy-vy*12)],fill='black',width=3)
    mid=pts[len(pts)//2] if via else ((p[0]+q[0])/2,(p[1]+q[1])/2)
    x,y=mid
    d.ellipse((x-22,y-22,x+22,y+22),fill='white',outline='black',width=2)
    label=str(n); bb=d.textbbox((0,0),label,font=font(23,True))
    text(x-(bb[2]-bb[0])/2,y-17,label,23,True)

text(180,35,'복지 챗봇 데이터베이스 ERD',49,True)
text(180,105,'검토용 초안  |  최신 제도 · 변경 이력 · 정기 수집 · 구독 알림',29)
edge('USERS','r','CHAT_SESSIONS','l',1)
edge('CHAT_SESSIONS','r','CHAT_MESSAGES','l',2)
edge('CHAT_MESSAGES','b','CHAT_SEARCH_RESULTS','t',3)
edge('USERS','b','POLICY_SUBSCRIPTIONS','t',4)
edge('WELFARE_POLICIES','l','POLICY_SUBSCRIPTIONS','r',5)
edge('WELFARE_POLICIES','b','WELFARE_POLICY_VERSIONS','t',6)
edge('SYNC_RUNS','l','WELFARE_POLICY_VERSIONS','r',7)
edge('WELFARE_POLICY_VERSIONS','l','NOTIFICATIONS','r',8)
edge('USERS','l','NOTIFICATIONS','l',9,[(85,515),(85,2135)])
edge('WELFARE_POLICY_VERSIONS','r','CHAT_SEARCH_RESULTS','b',10,[(1960,2135),(1960,1725),(2430,1725)])

for name,kr,col,row,fields in tables:
    x,y=boxes[name]
    d.rounded_rectangle((x,y,x+W,y+H),radius=12,fill='white',outline='black',width=3)
    d.rectangle((x+2,y+2,x+W-2,y+107),fill='#eef2f5')
    d.line((x,y+108,x+W,y+108),fill='black',width=2)
    text(x+24,y+14,name,29,True)
    text(x+24,y+57,kr,27)
    for i,f in enumerate(fields): text(x+24,y+126+i*44,f,26)

text(180,2490,'관계 설명',30,True)
text(180,2540,'① 사용자–세션   ② 세션–메시지   ③ 메시지–검색 결과   ④ 사용자–구독   ⑤ 제도–구독',27)
text(180,2585,'⑥ 제도–버전   ⑦ 수집–버전   ⑧ 버전–알림   ⑨ 사용자–알림   ⑩ 버전–검색 결과',27)
text(180,2645,'연결선: 단일 막대 = 1 / 갈라진 끝 = N. 제도는 버전 1개 이상, 그 외 자식 레코드는 0개 이상.',25)
text(180,2690,'PK: 기본키  ·  FK: 외래키  ·  UK: 고유값  |  비회원 세션의 사용자 연결은 선택 사항',25)
text(180,2735,'초안 범위: 관심 제도 변경 알림. 조건별 신규 제도 알림과 사용자 상세 프로필은 추후 확장.',25)
im.save(OUT/'welfare_erd.png')
print(OUT/'welfare_erd.png')
