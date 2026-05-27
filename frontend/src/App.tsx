import { useEffect, useState } from "react";

interface Policy {
  serv_id?: string | null;
  serv_nm?: string | null;
  serv_dgst?: string | null;
  serv_dtl_link?: string | null;
}

interface ChatMessage {
  id?: string;
  role: "user" | "assistant";
  content: string | null;
  message_type?: "text" | "welfare_cards" | "system";
  message_metadata?: {
    policies?: Policy[];
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

  useEffect(() => {
    loadSessions();
  }, []);

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

  const sendMessage = async () => {
    if (!sessionId || !message.trim()) return;

    const userMessage = message.trim();

    setChatList((prev) => [
      ...prev,
      { role: "user", content: userMessage, message_type: "text" },
    ]);

    setMessage("");
    setLoading(true);

    const res = await fetch(`${API_BASE_URL}/api/chat/session/${sessionId}/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMessage }),
    });

    const data = await res.json();

    setChatList((prev) => [
      ...prev,
      { role: "assistant", content: data.answer, message_type: "text" },
    ]);

    if (data.policies?.length > 0) {
      setChatList((prev) => [
        ...prev,
        {
          role: "assistant",
          content: null,
          message_type: "welfare_cards",
          message_metadata: { policies: data.policies },
        },
      ]);
    }

    setLoading(false);
    await loadSessions();
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

        const response = await fetch("http://127.0.0.1:8000/api/stt/transcribe", {
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

  const renderPolicies = (policies: Policy[]) => (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {policies.map((p, i) => (
        <div
          key={`${p.serv_id}-${i}`}
          style={{
            background: "#f8fafc",
            border: "1px solid #dbeafe",
            borderRadius: 12,
            padding: 12,
          }}
        >
          <strong style={{ color: "#1e3a8a" }}>{p.serv_nm || "제도명 없음"}</strong>
          <p style={{ lineHeight: 1.5 }}>{p.serv_dgst || "요약 정보 없음"}</p>
          {p.serv_dtl_link && (
            <a href={p.serv_dtl_link} target="_blank" rel="noreferrer">
              상세보기 →
            </a>
          )}
        </div>
      ))}
    </div>
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
      </div>

      <section style={{ flex: 1, padding: 18, overflowY: "auto" }}>
        {chatList.map((chat, index) => {
          const isUser = chat.role === "user";
          const isCards = chat.message_type === "welfare_cards";

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
                  maxWidth: "78%",
                  background: isUser ? "#bcd0ff" : "white",
                  borderRadius: 16,
                  padding: 14,
                  border: isUser ? "none" : "1px solid #dbeafe",
                }}
              >
                {isCards
                  ? renderPolicies(chat.message_metadata?.policies ?? [])
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
      <div style={{ background: "white", padding: 18, borderRadius: 16 }}>
        <h3>설정</h3>
        <p>프로필 수정</p>
        <p>비밀번호 변경</p>
        <p>언어: 한국어</p>
        <p>라이트모드</p>
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