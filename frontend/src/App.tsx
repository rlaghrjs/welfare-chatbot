import { useEffect, useState } from "react";

interface Policy {
  serv_id?: string | null;
  serv_nm?: string | null;
  serv_dgst?: string | null;
  serv_dtl_link?: string | null;
  ctpv_nm?: string | null;
  biz_chr_dept_nm?: string | null;
  aply_mtd_nm?: string | null;
  srv_pvsn_nm?: string | null;
}

interface WelfareResultGroup {
  request_url?: string | null;
  saved_count?: number;
  policies?: Policy[];
}

interface ChatApiResponse {
  answer: string;
  intent?: Record<string, unknown>;
  results?: {
    central?: WelfareResultGroup;
    local?: WelfareResultGroup;
  };
  policies?: Policy[];
  request_url?: string | null;
}

interface ChatMessage {
  id?: string;
  role: "user" | "assistant";
  content: string | null;
  message_type?: "text" | "welfare_cards" | "system" | "debug";
  message_metadata?: {
    policies?: Policy[];
    title?: string;
    requestUrl?: string | null;
    intent?: Record<string, unknown>;
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

interface WelfareProfile {
  age?: number | "";
  lifeArray?: string;
  trgterIndvdlArray?: string;
  intrsThemaArray?: string;
}

type Page = "home" | "chat" | "settings";

const API_BASE_URL = "http://127.0.0.1:8000";

const CTPV_OPTIONS = [
  "서울특별시",
  "부산광역시",
  "대구광역시",
  "인천광역시",
  "광주광역시",
  "대전광역시",
  "울산광역시",
  "세종특별자치시",
  "경기도",
  "강원특별자치도",
  "충청북도",
  "충청남도",
  "전북특별자치도",
  "전라남도",
  "경상북도",
  "경상남도",
  "제주특별자치도",
];

const LIFE_OPTIONS = [
  { code: "", name: "선택 안 함" },
  { code: "001", name: "영유아" },
  { code: "002", name: "아동" },
  { code: "003", name: "청소년" },
  { code: "004", name: "청년" },
  { code: "005", name: "중장년" },
  { code: "006", name: "노년" },
  { code: "007", name: "임신·출산" },
];

const TARGET_OPTIONS = [
  { code: "", name: "선택 안 함" },
  { code: "010", name: "다문화·탈북민" },
  { code: "020", name: "다자녀" },
  { code: "030", name: "보훈대상자" },
  { code: "040", name: "장애인" },
  { code: "050", name: "저소득" },
  { code: "060", name: "한부모·조손" },
];

const THEME_OPTIONS = [
  { code: "", name: "선택 안 함" },
  { code: "010", name: "신체건강" },
  { code: "020", name: "정신건강" },
  { code: "030", name: "생활지원" },
  { code: "040", name: "주거" },
  { code: "050", name: "일자리" },
  { code: "060", name: "문화·여가" },
  { code: "070", name: "안전·위기" },
  { code: "080", name: "임신·출산" },
  { code: "090", name: "보육" },
  { code: "100", name: "교육" },
  { code: "120", name: "보호·돌봄" },
  { code: "130", name: "서민금융" },
  { code: "140", name: "법률" },
  { code: "160", name: "에너지" },
];

const DEFAULT_PROFILE: WelfareProfile = {
  age: "",
  lifeArray: "",
  trgterIndvdlArray: "",
  intrsThemaArray: "",
};

export default function App() {
  const [page, setPage] = useState<Page>("home");
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [sessionTitle, setSessionTitle] = useState("");
  const [message, setMessage] = useState("");
  const [chatList, setChatList] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [recording, setRecording] = useState(false);

  // 지역은 일반 검색/프로필 맞춤 검색 모두에 적용되는 공통 검색 지역
  const [ctpvNm, setCtpvNm] = useState("서울특별시");

  // 프로필은 맞춤 검색일 때만 적용
  const [useProfile, setUseProfile] = useState(false);
  const [showDebug, setShowDebug] = useState(true);
  const [profile, setProfile] = useState<WelfareProfile>(DEFAULT_PROFILE);

  useEffect(() => {
    loadSessions();
    loadSettings();
  }, []);

  const loadSettings = () => {
    const savedProfile = localStorage.getItem("welfareProfile");
    const savedUseProfile = localStorage.getItem("useWelfareProfile");
    const savedDebug = localStorage.getItem("showWelfareDebug");
    const savedCtpvNm = localStorage.getItem("ctpvNm");

    if (savedProfile) {
      try {
        setProfile({ ...DEFAULT_PROFILE, ...JSON.parse(savedProfile) });
      } catch {
        setProfile(DEFAULT_PROFILE);
      }
    }

    if (savedCtpvNm) {
      setCtpvNm(savedCtpvNm);
    }

    if (savedUseProfile) {
      setUseProfile(savedUseProfile === "true");
    }

    if (savedDebug) {
      setShowDebug(savedDebug === "true");
    }
  };

  const saveSettings = () => {
    localStorage.setItem("welfareProfile", JSON.stringify(profile));
    localStorage.setItem("ctpvNm", ctpvNm);
    localStorage.setItem("useWelfareProfile", String(useProfile));
    localStorage.setItem("showWelfareDebug", String(showDebug));
    alert("설정이 저장되었습니다.");
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
        content: "채팅 세션이 시작되었습니다. 궁금한 복지제도를 입력해주세요.",
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

  const buildRequestProfile = () => {
    const requestProfile: WelfareProfile = {};

    if (profile.age !== "" && profile.age !== undefined) {
      requestProfile.age = Number(profile.age);
    }

    if (profile.lifeArray) {
      requestProfile.lifeArray = profile.lifeArray;
    }

    if (profile.trgterIndvdlArray) {
      requestProfile.trgterIndvdlArray = profile.trgterIndvdlArray;
    }

    if (profile.intrsThemaArray) {
      requestProfile.intrsThemaArray = profile.intrsThemaArray;
    }

    return requestProfile;
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
      const body = {
        message: userMessage,
        ctpvNm,
        useProfile,
        profile: useProfile ? buildRequestProfile() : null,
      };

      const res = await fetch(`${API_BASE_URL}/api/chat/session/${sessionId}/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data: ChatApiResponse = await res.json();

      if (!res.ok) {
        throw new Error(data?.answer || "서버 오류가 발생했습니다.");
      }

      setChatList((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, message_type: "text" },
      ]);

      const centralPolicies = data.results?.central?.policies ?? [];
      const localPolicies = data.results?.local?.policies ?? [];

      if (centralPolicies.length > 0) {
        setChatList((prev) => [
          ...prev,
          {
            role: "assistant",
            content: null,
            message_type: "welfare_cards",
            message_metadata: {
              title: "중앙 복지제도",
              policies: centralPolicies,
              requestUrl: data.results?.central?.request_url,
            },
          },
        ]);
      }

      if (localPolicies.length > 0) {
        setChatList((prev) => [
          ...prev,
          {
            role: "assistant",
            content: null,
            message_type: "welfare_cards",
            message_metadata: {
              title: "지자체 복지제도",
              policies: localPolicies,
              requestUrl: data.results?.local?.request_url,
            },
          },
        ]);
      }

      if (showDebug) {
        setChatList((prev) => [
          ...prev,
          {
            role: "assistant",
            content: null,
            message_type: "debug",
            message_metadata: {
              requestUrl:
                `중앙 요청 URL:\n${data.results?.central?.request_url || "없음"}\n\n` +
                `지자체 요청 URL:\n${data.results?.local?.request_url || "없음"}`,
              intent: data.intent,
            },
          },
        ]);
      }

      // 구버전 백엔드 호환
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
    } catch (error) {
      console.error(error);
      setChatList((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "요청 처리 중 오류가 발생했습니다. 백엔드 로그를 확인해주세요.",
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

  const selectStyle: React.CSSProperties = {
    width: "100%",
    padding: 12,
    borderRadius: 12,
    border: "1px solid #dbeafe",
    boxSizing: "border-box",
    background: "white",
  };

  const inputStyle: React.CSSProperties = {
    width: "100%",
    padding: 12,
    borderRadius: 12,
    border: "1px solid #dbeafe",
    boxSizing: "border-box",
    background: "white",
  };

  const labelStyle: React.CSSProperties = {
    display: "block",
    fontSize: 13,
    color: "#475569",
    marginBottom: 6,
    fontWeight: 700,
  };

  const renderPolicies = (policies: Policy[], title?: string, requestUrl?: string | null) => (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {title && (
        <div style={{ fontWeight: 800, color: "#0f172a", marginBottom: 4 }}>
          {title} ({policies.length}건)
        </div>
      )}

      {showDebug && requestUrl && (
        <details
          style={{
            fontSize: 11,
            color: "#64748b",
            background: "#f8fafc",
            border: "1px dashed #cbd5e1",
            borderRadius: 10,
            padding: 8,
          }}
        >
          <summary>요청 URL 보기</summary>
          <div style={{ wordBreak: "break-all", marginTop: 6 }}>{requestUrl}</div>
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

          {(p.ctpv_nm || p.biz_chr_dept_nm || p.srv_pvsn_nm) && (
            <p style={{ fontSize: 12, color: "#64748b", margin: "6px 0" }}>
              {p.ctpv_nm ? `지역: ${p.ctpv_nm}` : ""}
              {p.ctpv_nm && p.srv_pvsn_nm ? " · " : ""}
              {p.srv_pvsn_nm ? `제공유형: ${p.srv_pvsn_nm}` : ""}
            </p>
          )}

          <p style={{ lineHeight: 1.5, marginTop: 8 }}>
            {p.serv_dgst || "요약 정보 없음"}
          </p>

          {p.aply_mtd_nm && (
            <p style={{ fontSize: 12, color: "#475569", marginTop: 8 }}>
              신청방법: {p.aply_mtd_nm}
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

  const renderDebug = (chat: ChatMessage) => (
    <details
      style={{
        fontSize: 12,
        textAlign: "left",
        color: "#475569",
        whiteSpace: "pre-wrap",
      }}
    >
      <summary>디버그 정보</summary>
      <div style={{ marginTop: 8, wordBreak: "break-all" }}>
        {chat.message_metadata?.requestUrl}
      </div>
      {chat.message_metadata?.intent && (
        <pre
          style={{
            marginTop: 8,
            padding: 10,
            background: "#f1f5f9",
            borderRadius: 8,
            overflowX: "auto",
          }}
        >
          {JSON.stringify(chat.message_metadata.intent, null, 2)}
        </pre>
      )}
    </details>
  );

  const HomePage = () => (
    <main style={{ flex: 1, padding: 20, background: "#eef3ff", overflowY: "auto" }}>
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

      <div
        style={{
          background: "white",
          border: "1px solid #dbeafe",
          borderRadius: 16,
          padding: 14,
          marginBottom: 18,
          textAlign: "left",
        }}
      >
        <strong>현재 검색 설정</strong>
        <p style={{ color: "#64748b", marginTop: 6 }}>
          지역: {ctpvNm} · {useProfile ? "프로필 맞춤 검색" : "일반 검색"}
        </p>
        <button
          onClick={() => setPage("settings")}
          style={{
            marginTop: 10,
            padding: "8px 12px",
            borderRadius: 10,
            border: "1px solid #bfdbfe",
            background: "#eff6ff",
          }}
        >
          검색 설정하기
        </button>
      </div>

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
          <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
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

        <div
          style={{
            marginTop: 12,
            background: "#f8fafc",
            borderRadius: 14,
            padding: 8,
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 8,
          }}
        >
          <button
            onClick={() => {
              setUseProfile(false);
              localStorage.setItem("useWelfareProfile", "false");
            }}
            style={{
              padding: 10,
              borderRadius: 12,
              border: "none",
              background: !useProfile ? "#2563eb" : "white",
              color: !useProfile ? "white" : "#334155",
              fontWeight: 700,
            }}
          >
            일반 검색
          </button>
          <button
            onClick={() => {
              setUseProfile(true);
              localStorage.setItem("useWelfareProfile", "true");
            }}
            style={{
              padding: 10,
              borderRadius: 12,
              border: "none",
              background: useProfile ? "#2563eb" : "white",
              color: useProfile ? "white" : "#334155",
              fontWeight: 700,
            }}
          >
            프로필 맞춤
          </button>
        </div>

        <p style={{ fontSize: 12, color: "#64748b", marginTop: 8, textAlign: "left" }}>
          검색 지역: {ctpvNm}
          {useProfile && profile.age ? ` · ${profile.age}세` : ""}
          {useProfile && profile.lifeArray
            ? ` · ${LIFE_OPTIONS.find((x) => x.code === profile.lifeArray)?.name}`
            : ""}
          {useProfile && profile.intrsThemaArray
            ? ` · ${THEME_OPTIONS.find((x) => x.code === profile.intrsThemaArray)?.name}`
            : ""}
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
                  maxWidth: isCards || isDebug ? "92%" : "78%",
                  background: isUser ? "#bcd0ff" : "white",
                  borderRadius: 16,
                  padding: 14,
                  border: isUser ? "none" : "1px solid #dbeafe",
                  textAlign: "left",
                }}
              >
                {isCards
                  ? renderPolicies(
                      chat.message_metadata?.policies ?? [],
                      chat.message_metadata?.title,
                      chat.message_metadata?.requestUrl
                    )
                  : isDebug
                    ? renderDebug(chat)
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
          placeholder={
            useProfile
              ? "프로필 기준으로 궁금한 복지제도를 입력해보세요..."
              : "궁금한 복지제도를 입력해보세요..."
          }
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
    <main style={{ flex: 1, padding: 20, background: "#eef3ff", overflowY: "auto" }}>
      <div style={{ background: "white", padding: 18, borderRadius: 16, textAlign: "left" }}>
        <h3 style={{ marginTop: 0 }}>검색 설정</h3>
        <p style={{ color: "#64748b", fontSize: 13, marginBottom: 18 }}>
          지역은 일반 검색과 프로필 맞춤 검색 모두에 적용됩니다. 나이, 생애주기, 가구상황,
          관심주제는 프로필 맞춤 검색에서만 적용됩니다.
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <label style={labelStyle}>검색 지역</label>
            <select
              value={ctpvNm}
              onChange={(e) => setCtpvNm(e.target.value)}
              style={selectStyle}
            >
              {CTPV_OPTIONS.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={labelStyle}>검색 방식</label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <button
                onClick={() => setUseProfile(false)}
                style={{
                  padding: 12,
                  borderRadius: 12,
                  border: "1px solid #bfdbfe",
                  background: !useProfile ? "#2563eb" : "white",
                  color: !useProfile ? "white" : "#334155",
                  fontWeight: 700,
                }}
              >
                일반 검색
              </button>
              <button
                onClick={() => setUseProfile(true)}
                style={{
                  padding: 12,
                  borderRadius: 12,
                  border: "1px solid #bfdbfe",
                  background: useProfile ? "#2563eb" : "white",
                  color: useProfile ? "white" : "#334155",
                  fontWeight: 700,
                }}
              >
                프로필 맞춤
              </button>
            </div>
          </div>

          <div>
            <label style={labelStyle}>나이</label>
            <input
              type="number"
              min={0}
              max={120}
              value={profile.age ?? ""}
              onChange={(e) =>
                setProfile((prev) => ({
                  ...prev,
                  age: e.target.value === "" ? "" : Number(e.target.value),
                }))
              }
              placeholder="예: 24"
              style={inputStyle}
            />
          </div>

          <div>
            <label style={labelStyle}>생애주기</label>
            <select
              value={profile.lifeArray || ""}
              onChange={(e) =>
                setProfile((prev) => ({
                  ...prev,
                  lifeArray: e.target.value,
                }))
              }
              style={selectStyle}
            >
              {LIFE_OPTIONS.map((item) => (
                <option key={item.code} value={item.code}>
                  {item.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={labelStyle}>가구상황</label>
            <select
              value={profile.trgterIndvdlArray || ""}
              onChange={(e) =>
                setProfile((prev) => ({
                  ...prev,
                  trgterIndvdlArray: e.target.value,
                }))
              }
              style={selectStyle}
            >
              {TARGET_OPTIONS.map((item) => (
                <option key={item.code} value={item.code}>
                  {item.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={labelStyle}>관심주제</label>
            <select
              value={profile.intrsThemaArray || ""}
              onChange={(e) =>
                setProfile((prev) => ({
                  ...prev,
                  intrsThemaArray: e.target.value,
                }))
              }
              style={selectStyle}
            >
              {THEME_OPTIONS.map((item) => (
                <option key={item.code} value={item.code}>
                  {item.name}
                </option>
              ))}
            </select>
          </div>

          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              color: "#475569",
              fontSize: 14,
            }}
          >
            <input
              type="checkbox"
              checked={showDebug}
              onChange={(e) => setShowDebug(e.target.checked)}
            />
            요청 URL / intent 디버그 표시
          </label>

          <button
            onClick={saveSettings}
            style={{
              padding: 14,
              borderRadius: 14,
              border: "none",
              background: "#2563eb",
              color: "white",
              fontWeight: 800,
              marginTop: 8,
            }}
          >
            저장하기
          </button>
        </div>
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
        <button onClick={() => setPage("home")}>🏠<br />홈</button>
        <button onClick={() => setPage("chat")}>💬<br />채팅</button>
        <button onClick={() => setPage("settings")}>⚙️<br />설정</button>
      </nav>
    </div>
  );
}
