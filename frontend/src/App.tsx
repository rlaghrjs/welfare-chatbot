import { useEffect, useMemo, useState } from "react";

interface Policy {
  serv_id?: string | null;
  serv_nm?: string | null;
  serv_dgst?: string | null;
  serv_dtl_link?: string | null;
  ctpv_nm?: string | null;
  sgg_nm?: string | null;
  biz_chr_dept_nm?: string | null;
  aply_mtd_nm?: string | null;
  intrs_thema_nm_array?: string | null;
  last_mod_ymd?: string | null;
}

interface WelfareGroup {
  request_url?: string | null;
  saved_count?: number;
  policies?: Policy[];
}

interface ChatResponse {
  answer: string;
  intent?: Record<string, unknown>;
  policies?: Policy[];
  results?: {
    central?: WelfareGroup;
    local?: WelfareGroup;
  };
}

interface ChatMessage {
  id?: string;
  role: "user" | "assistant";
  content: string | null;
  message_type?: "text" | "welfare_cards" | "system" | "debug";
  message_metadata?: {
    policies?: Policy[];
    title?: string;
    request_url?: string | null;
  } | null;
}

interface ChatSession {
  session_id: string;
  title: string | null;
  status: string;
  created_at: string;
  ended_at: string | null;
}

interface SessionDetailResponse {
  session: ChatSession;
  messages: ChatMessage[];
}

type Page = "home" | "chat" | "settings";

type RegionMap = Record<string, string[]>;

const REGION_MAP: RegionMap = {
  "서울특별시": [
    "강남구",
    "강동구",
    "강북구",
    "강서구",
    "관악구",
    "광진구",
    "구로구",
    "금천구",
    "노원구",
    "도봉구",
    "동대문구",
    "동작구",
    "마포구",
    "서대문구",
    "서초구",
    "성동구",
    "성북구",
    "송파구",
    "양천구",
    "영등포구",
    "용산구",
    "은평구",
    "종로구",
    "중구",
    "중랑구",
  ],
  "인천광역시": [
    "강화군",
    "계양구",
    "남동구",
    "동구",
    "미추홀구",
    "부평구",
    "서구",
    "연수구",
    "옹진군",
    "중구",
  ],
  "경기도": [
    "가평군",
    "고양시",
    "과천시",
    "광명시",
    "광주시",
    "구리시",
    "군포시",
    "김포시",
    "남양주시",
    "동두천시",
    "부천시",
    "성남시",
    "수원시",
    "시흥시",
    "안산시",
    "안성시",
    "안양시",
    "양주시",
    "양평군",
    "여주시",
    "연천군",
    "오산시",
    "용인시",
    "의왕시",
    "의정부시",
    "이천시",
    "파주시",
    "평택시",
    "포천시",
    "하남시",
    "화성시",
  ],
  "부산광역시": ["강서구", "금정구", "기장군", "남구", "동구", "동래구", "부산진구", "북구", "사상구", "사하구", "서구", "수영구", "연제구", "영도구", "중구", "해운대구"],
  "대구광역시": ["군위군", "남구", "달서구", "달성군", "동구", "북구", "서구", "수성구", "중구"],
  "광주광역시": ["광산구", "남구", "동구", "북구", "서구"],
  "대전광역시": ["대덕구", "동구", "서구", "유성구", "중구"],
  "울산광역시": ["남구", "동구", "북구", "울주군", "중구"],
  "세종특별자치시": ["세종특별자치시"],
  "강원특별자치도": ["강릉시", "고성군", "동해시", "삼척시", "속초시", "양구군", "양양군", "영월군", "원주시", "인제군", "정선군", "철원군", "춘천시", "태백시", "평창군", "홍천군", "화천군", "횡성군"],
  "충청북도": ["괴산군", "단양군", "보은군", "영동군", "옥천군", "음성군", "제천시", "증평군", "진천군", "청주시", "충주시"],
  "충청남도": ["계룡시", "공주시", "금산군", "논산시", "당진시", "보령시", "부여군", "서산시", "서천군", "아산시", "예산군", "천안시", "청양군", "태안군", "홍성군"],
  "전북특별자치도": ["고창군", "군산시", "김제시", "남원시", "무주군", "부안군", "순창군", "완주군", "익산시", "임실군", "장수군", "전주시", "정읍시", "진안군"],
  "전라남도": ["강진군", "고흥군", "곡성군", "광양시", "구례군", "나주시", "담양군", "목포시", "무안군", "보성군", "순천시", "신안군", "여수시", "영광군", "영암군", "완도군", "장성군", "장흥군", "진도군", "함평군", "해남군", "화순군"],
  "경상북도": ["경산시", "경주시", "고령군", "구미시", "김천시", "문경시", "봉화군", "상주시", "성주군", "안동시", "영덕군", "영양군", "영주시", "영천시", "예천군", "울릉군", "울진군", "의성군", "청도군", "청송군", "칠곡군", "포항시"],
  "경상남도": ["거제시", "거창군", "고성군", "김해시", "남해군", "밀양시", "사천시", "산청군", "양산시", "의령군", "진주시", "창녕군", "창원시", "통영시", "하동군", "함안군", "함양군", "합천군"],
  "제주특별자치도": ["서귀포시", "제주시"],
};

export default function App() {
  const API_BASE_URL = "http://127.0.0.1:8000";

  const [page, setPage] = useState<Page>("home");
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [sessionTitle, setSessionTitle] = useState("");
  const [message, setMessage] = useState("");
  const [chatList, setChatList] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [recording, setRecording] = useState(false);
  const [ctpvNm, setCtpvNm] = useState(() => localStorage.getItem("ctpvNm") || "서울특별시");
  const [sggNm, setSggNm] = useState(() => localStorage.getItem("sggNm") || "강남구");
  const [showDebug, setShowDebug] = useState(false);

  const sggOptions = useMemo(() => REGION_MAP[ctpvNm] ?? [], [ctpvNm]);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    localStorage.setItem("ctpvNm", ctpvNm);
  }, [ctpvNm]);

  useEffect(() => {
    localStorage.setItem("sggNm", sggNm);
  }, [sggNm]);

  const handleCtpvChange = (value: string) => {
    const nextSgg = REGION_MAP[value]?.[0] || "";
    setCtpvNm(value);
    setSggNm(nextSgg);
  };

  const loadSessions = async () => {
    const res = await fetch(`${API_BASE_URL}/api/chat/sessions`);
    const data = await res.json();
    setSessions(data);
  };

  const createSession = async () => {
    const res = await fetch(`${API_BASE_URL}/api/chat/session`, {
      method: "POST",
    });
    const data = await res.json();

    setSessionId(data.session_id);
    setSessionTitle(data.title || "새 채팅");
    setChatList([
      {
        role: "assistant",
        content: `채팅 세션이 시작되었습니다. 현재 지역 설정은 ${ctpvNm} ${sggNm}입니다. 궁금한 복지제도를 입력해주세요.`,
        message_type: "text",
      },
    ]);

    await loadSessions();
    setPage("chat");
  };

  const loadSessionDetail = async (targetSessionId: string) => {
    const res = await fetch(`${API_BASE_URL}/api/chat/session/${targetSessionId}`);
    const data: SessionDetailResponse = await res.json();

    setSessionId(data.session.session_id);
    setSessionTitle(data.session.title || "제목 없음");
    setChatList(data.messages);
    setPage("chat");
  };

  const sendMessage = async () => {
    if (!sessionId || !message.trim()) return;

    const userMessage = message.trim();

    setChatList((prev) => [
      ...prev,
      { role: "user", content: userMessage, message_type: "text" },
    ]);

    setMessage("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat/session/${sessionId}/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage,
          ctpvNm,
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data: ChatResponse = await res.json();

      setChatList((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, message_type: "text" },
      ]);

      const central = data.results?.central;
      const local = data.results?.local;

      if (central?.policies?.length) {
        setChatList((prev) => [
          ...prev,
          {
            role: "assistant",
            content: null,
            message_type: "welfare_cards",
            message_metadata: {
              title: "중앙 복지제도",
              request_url: central.request_url,
              policies: central.policies,
            },
          },
        ]);
      }

      if (local?.policies?.length) {
        setChatList((prev) => [
          ...prev,
          {
            role: "assistant",
            content: null,
            message_type: "welfare_cards",
            message_metadata: {
              title: `${ctpvNm} ${sggNm} 지자체 복지제도`,
              request_url: local.request_url,
              policies: local.policies,
            },
          },
        ]);
      }

      if (!data.results && data.policies?.length) {
        setChatList((prev) => [
          ...prev,
          {
            role: "assistant",
            content: null,
            message_type: "welfare_cards",
            message_metadata: { title: "복지제도", policies: data.policies },
          },
        ]);
      }

      if (showDebug) {
        setChatList((prev) => [
          ...prev,
          {
            role: "assistant",
            content: JSON.stringify(
              {
                requestBody: { message: userMessage, ctpvNm, sggNm },
                intent: data.intent,
                centralUrl: central?.request_url,
                localUrl: local?.request_url,
              },
              null,
              2,
            ),
            message_type: "debug",
          },
        ]);
      }
    } catch (error) {
      console.error(error);
      setChatList((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "요청 처리 중 오류가 발생했습니다. 백엔드 서버와 API 응답 구조를 확인해주세요.",
          message_type: "text",
        },
      ]);
    } finally {
      setLoading(false);
      await loadSessions();
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: BlobPart[] = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: "audio/webm" });

        const formData = new FormData();
        formData.append("file", audioBlob, "recording.webm");

        const response = await fetch(`${API_BASE_URL}/api/stt/transcribe`, {
          method: "POST",
          body: formData,
        });

        const data = await response.json();
        setMessage(data.text);

        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setRecording(true);
    } catch (error) {
      console.error(error);
      alert("마이크 권한을 확인해주세요.");
    }
  };

  const stopRecording = () => {
    if (!mediaRecorder) return;

    mediaRecorder.stop();
    setRecording(false);
    setMediaRecorder(null);
  };

  const endSession = async () => {
    if (!sessionId) return;

    await fetch(`${API_BASE_URL}/api/chat/session/${sessionId}/end`, {
      method: "POST",
    });

    setSessionId("");
    setSessionTitle("");
    await loadSessions();
    setPage("home");
  };

  const formatDate = (value: string | null) => {
    if (!value) return "";
    return new Date(value).toLocaleString("ko-KR", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const renderPolicies = (policies: Policy[], title?: string, requestUrl?: string | null) => (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {title && (
        <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
          <strong style={{ color: "#0f172a" }}>{title}</strong>
          <span style={{ color: "#64748b", fontSize: 12 }}>{policies.length}건</span>
        </div>
      )}

      {showDebug && requestUrl && (
        <details style={{ fontSize: 12, color: "#64748b", wordBreak: "break-all" }}>
          <summary>요청 URL 확인</summary>
          {requestUrl}
        </details>
      )}

      {policies.map((p, i) => (
        <div
          key={`${p.serv_id}-${i}`}
          style={{
            background: "#f8fafc",
            border: "1px solid #dbeafe",
            borderRadius: 12,
            padding: 12,
            textAlign: "left",
          }}
        >
          <strong style={{ color: "#1e3a8a" }}>{p.serv_nm || "제도명 없음"}</strong>
          {(p.ctpv_nm || p.sgg_nm || p.biz_chr_dept_nm) && (
            <p style={{ color: "#64748b", fontSize: 12, marginTop: 4 }}>
              {[p.ctpv_nm, p.sgg_nm, p.biz_chr_dept_nm].filter(Boolean).join(" · ")}
            </p>
          )}
          <p style={{ lineHeight: 1.5, marginTop: 8 }}>{p.serv_dgst || "요약 정보 없음"}</p>
          {(p.aply_mtd_nm || p.intrs_thema_nm_array || p.last_mod_ymd) && (
            <p style={{ color: "#64748b", fontSize: 12, marginTop: 8 }}>
              {[p.aply_mtd_nm && `신청: ${p.aply_mtd_nm}`, p.intrs_thema_nm_array && `주제: ${p.intrs_thema_nm_array}`, p.last_mod_ymd && `수정일: ${p.last_mod_ymd}`]
                .filter(Boolean)
                .join(" / ")}
            </p>
          )}
          {p.serv_dtl_link && (
            <a href={p.serv_dtl_link} target="_blank" rel="noreferrer">
              상세보기 →
            </a>
          )}
        </div>
      ))}
    </div>
  );

  const RegionSelector = () => (
    <div
      style={{
        background: "white",
        border: "1px solid #dbeafe",
        borderRadius: 16,
        padding: 14,
        marginBottom: 14,
        textAlign: "left",
      }}
    >
      <strong style={{ display: "block", marginBottom: 10, color: "#0f172a" }}>
        지역 설정
      </strong>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        <select
          value={ctpvNm}
          onChange={(e) => handleCtpvChange(e.target.value)}
          style={{ padding: 10, borderRadius: 10, border: "1px solid #dbeafe" }}
        >
          {Object.keys(REGION_MAP).map((city) => (
            <option key={city} value={city}>
              {city}
            </option>
          ))}
        </select>

        <select
          value={sggNm}
          onChange={(e) => setSggNm(e.target.value)}
          style={{ padding: 10, borderRadius: 10, border: "1px solid #dbeafe" }}
        >
          {sggOptions.map((district) => (
            <option key={district} value={district}>
              {district}
            </option>
          ))}
        </select>
      </div>
      <p style={{ color: "#64748b", fontSize: 12, marginTop: 8 }}>
        채팅 요청 시 message와 별도로 ctpvNm, sggNm이 함께 전송됩니다.
      </p>
    </div>
  );

  const HomePage = () => (
    <main style={{ flex: 1, padding: 20, background: "#eef3ff", overflowY: "auto" }}>
      <RegionSelector />

      <button
        onClick={createSession}
        style={{
          width: "100%",
          padding: 14,
          borderRadius: 14,
          border: "none",
          background: "#2563eb",
          color: "white",
          fontWeight: 700,
          marginBottom: 18,
        }}
      >
        새 채팅 시작
      </button>

      <input
        placeholder="채팅 검색..."
        style={{
          width: "100%",
          padding: 14,
          borderRadius: 16,
          border: "1px solid #dbeafe",
          marginBottom: 18,
          boxSizing: "border-box",
        }}
      />

      {sessions.map((session) => (
        <button
          key={session.session_id}
          onClick={() => loadSessionDetail(session.session_id)}
          style={{
            width: "100%",
            textAlign: "left",
            background: "white",
            border: "1px solid #dbeafe",
            borderRadius: 16,
            padding: 16,
            marginBottom: 12,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <strong>{session.title || "제목 없음"}</strong>
            <span style={{ color: "#94a3b8", fontSize: 12 }}>
              {formatDate(session.created_at)}
            </span>
          </div>
          <p style={{ color: "#64748b", marginBottom: 0 }}>{session.status}</p>
        </button>
      ))}
    </main>
  );

  const ChatPage = () => (
    <main style={{ flex: 1, display: "flex", flexDirection: "column", background: "#eef3ff" }}>
      <div style={{ padding: 16, background: "white", borderBottom: "1px solid #e5e7eb" }}>
        <strong>{sessionTitle || "복지 챗봇"}</strong>
        <button onClick={endSession} style={{ float: "right" }} disabled={!sessionId}>
          종료
        </button>
        <p style={{ color: "#64748b", fontSize: 12, marginTop: 4 }}>
          현재 지역: {ctpvNm} {sggNm}
        </p>
      </div>

      <section style={{ flex: 1, padding: 18, overflowY: "auto" }}>
        {chatList.map((chat, index) => {
          const isUser = chat.role === "user";
          const isCards = chat.message_type === "welfare_cards";
          const isDebug = chat.message_type === "debug";

          return (
            <div
              key={chat.id || index}
              style={{
                display: "flex",
                justifyContent: isUser ? "flex-end" : "flex-start",
                marginBottom: 14,
              }}
            >
              <div
                style={{
                  maxWidth: isDebug ? "92%" : "78%",
                  background: isUser ? "#bcd0ff" : "white",
                  borderRadius: 16,
                  padding: 14,
                  border: isUser ? "none" : "1px solid #dbeafe",
                  whiteSpace: isDebug ? "pre-wrap" : "normal",
                  textAlign: "left",
                  fontSize: isDebug ? 12 : undefined,
                  overflowX: "auto",
                }}
              >
                {isCards
                  ? renderPolicies(
                      chat.message_metadata?.policies ?? [],
                      chat.message_metadata?.title,
                      chat.message_metadata?.request_url,
                    )
                  : chat.content}
              </div>
            </div>
          );
        })}
        {loading && <p>복지 정보를 검색하는 중...</p>}
      </section>

      <footer style={{ display: "flex", gap: 8, padding: 14, background: "white" }}>
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="궁금한 복지제도를 입력해보세요..."
          disabled={!sessionId || loading}
          style={{
            flex: 1,
            padding: 12,
            borderRadius: 20,
            border: "1px solid #dbeafe",
          }}
        />
        <button
          onClick={recording ? stopRecording : startRecording}
          disabled={!sessionId || loading}
        >
          {recording ? "⏹️" : "🎤"}
        </button>
        <button onClick={sendMessage} disabled={!sessionId || loading}>
          전송
        </button>
      </footer>
    </main>
  );

  const SettingsPage = () => (
    <main style={{ flex: 1, padding: 20, background: "#eef3ff" }}>
      <RegionSelector />

      <div style={{ background: "white", padding: 18, borderRadius: 16, textAlign: "left" }}>
        <h3 style={{ marginTop: 0 }}>설정</h3>
        <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            type="checkbox"
            checked={showDebug}
            onChange={(e) => setShowDebug(e.target.checked)}
          />
          API 테스트 정보 표시
        </label>
        <p style={{ color: "#64748b", fontSize: 13, marginTop: 10 }}>
          켜면 채팅 응답에 요청 body, intent, 중앙/지자체 요청 URL이 함께 표시됩니다.
        </p>
      </div>
    </main>
  );

  return (
    <div
      style={{
        maxWidth: 390,
        height: "100vh",
        margin: "0 auto",
        display: "flex",
        flexDirection: "column",
        border: "1px solid #e5e7eb",
      }}
    >
      <header
        style={{
          height: 64,
          padding: "0 16px",
          display: "flex",
          alignItems: "center",
          background: "white",
          borderBottom: "1px solid #e5e7eb",
          fontWeight: 800,
        }}
      >
        🤖 &nbsp; 복지제도 안내 챗봇
      </header>

      {page === "home" && <HomePage />}
      {page === "chat" && <ChatPage />}
      {page === "settings" && <SettingsPage />}

      <nav
        style={{
          height: 72,
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          background: "white",
          borderTop: "1px solid #e5e7eb",
        }}
      >
        <button onClick={() => setPage("home")}>
          🏠
          <br />홈
        </button>
        <button onClick={() => setPage("chat")}>
          💬
          <br />채팅
        </button>
        <button onClick={() => setPage("settings")}>
          ⚙️
          <br />설정
        </button>
      </nav>
    </div>
  );
}
