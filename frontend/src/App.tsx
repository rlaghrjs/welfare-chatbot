import { useState } from "react";

interface Policy {
  serv_id: string;
  serv_nm: string | null;
  serv_dgst: string | null;
  serv_dtl_link: string | null;
}

interface ChatResponse {
  answer: string;
  intent: any;
  request_url: string;
  saved_count: number;
  skipped_count: number;
  policies: Policy[];
}

interface ChatBubble {
  role: "user" | "assistant";
  content: string;
}

export default function App() {
  const [sessionKey, setSessionKey] = useState("");
  const [message, setMessage] = useState("");
  const [chatList, setChatList] = useState<ChatBubble[]>([]);

  const [intent, setIntent] = useState<any>(null);
  const [requestUrl, setRequestUrl] = useState("");
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(false);

  const createSession = async () => {
    const response = await fetch("http://127.0.0.1:8000/api/chat/session", {
      method: "POST",
    });

    const data = await response.json();
    setSessionKey(data.session_key);
    setChatList([
      {
        role: "assistant",
        content: "채팅 세션이 시작되었습니다. 궁금한 복지제도를 입력해주세요.",
      },
    ]);
  };

  const sendMessage = async () => {
    if (!sessionKey) {
      alert("먼저 세션을 생성하세요.");
      return;
    }

    if (!message.trim()) return;

    const userMessage = message;

    setChatList((prev) => [
      ...prev,
      {
        role: "user",
        content: userMessage,
      },
    ]);

    setMessage("");
    setLoading(true);

    const response = await fetch(
      `http://127.0.0.1:8000/api/chat/session/${sessionKey}/message`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userMessage,
        }),
      }
    );

    const data: ChatResponse = await response.json();

    setChatList((prev) => [
      ...prev,
      {
        role: "assistant",
        content: data.answer,
      },
    ]);

    setIntent(data.intent);
    setRequestUrl(data.request_url);
    setPolicies(data.policies);
    setLoading(false);
  };

  const endSession = async () => {
    if (!sessionKey) return;

    const response = await fetch(
      `http://127.0.0.1:8000/api/chat/session/${sessionKey}/end`,
      {
        method: "POST",
      }
    );

    const data = await response.json();

    setChatList((prev) => [
      ...prev,
      {
        role: "assistant",
        content: `세션이 종료되었습니다. 요약: ${data.summary}`,
      },
    ]);

    setSessionKey("");
  };

  return (
    <div
      style={{
        maxWidth: 1100,
        margin: "0 auto",
        padding: 24,
        fontFamily: "Arial",
        display: "grid",
        gridTemplateColumns: "1.2fr 1fr",
        gap: 24,
      }}
    >
      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 16,
          overflow: "hidden",
          background: "#fff",
        }}
      >
        <div
          style={{
            padding: 16,
            borderBottom: "1px solid #eee",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <h2 style={{ margin: 0 }}>복지 챗봇</h2>
            <small>{sessionKey ? `세션: ${sessionKey}` : "세션 없음"}</small>
          </div>

          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={createSession}>세션 생성</button>
            <button onClick={endSession} disabled={!sessionKey}>
              세션 종료
            </button>
          </div>
        </div>

        <div
          style={{
            height: 520,
            padding: 16,
            overflowY: "auto",
            background: "#f8fafc",
          }}
        >
          {chatList.length === 0 && (
            <p style={{ color: "#64748b" }}>
              세션을 생성한 뒤 질문을 입력하세요.
            </p>
          )}

          {chatList.map((chat, index) => (
            <div
              key={index}
              style={{
                display: "flex",
                justifyContent:
                  chat.role === "user" ? "flex-end" : "flex-start",
                marginBottom: 12,
              }}
            >
              <div
                style={{
                  maxWidth: "75%",
                  padding: "12px 14px",
                  borderRadius: 16,
                  background: chat.role === "user" ? "#2563eb" : "#ffffff",
                  color: chat.role === "user" ? "#ffffff" : "#111827",
                  border:
                    chat.role === "user" ? "none" : "1px solid #e5e7eb",
                  lineHeight: 1.5,
                }}
              >
                {chat.content}
              </div>
            </div>
          ))}

          {loading && (
            <div style={{ color: "#64748b", marginTop: 8 }}>
              챗봇이 복지 정보를 찾는 중...
            </div>
          )}
        </div>

        <div
          style={{
            padding: 16,
            borderTop: "1px solid #eee",
            display: "flex",
            gap: 8,
          }}
        >
          <input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") sendMessage();
            }}
            placeholder="예: 청년 월세 지원 알려줘"
            style={{
              flex: 1,
              padding: 12,
              borderRadius: 10,
              border: "1px solid #ddd",
            }}
          />

          <button onClick={sendMessage} disabled={loading || !sessionKey}>
            전송
          </button>
        </div>
      </section>

      <section>
        <div
          style={{
            border: "1px solid #ddd",
            borderRadius: 16,
            padding: 16,
            marginBottom: 16,
            background: "#fff",
          }}
        >
          <h3>NLP 분석 결과</h3>

          {intent ? (
            <pre
              style={{
                background: "#111827",
                color: "#f9fafb",
                padding: 12,
                borderRadius: 10,
                overflowX: "auto",
                fontSize: 12,
              }}
            >
              {JSON.stringify(intent, null, 2)}
            </pre>
          ) : (
            <p style={{ color: "#64748b" }}>아직 분석 결과 없음</p>
          )}
        </div>

        <div
          style={{
            border: "1px solid #ddd",
            borderRadius: 16,
            padding: 16,
            marginBottom: 16,
            background: "#fff",
          }}
        >
          <h3>생성된 OpenAPI URL</h3>

          {requestUrl ? (
            <div
              style={{
                wordBreak: "break-all",
                background: "#f3f4f6",
                padding: 12,
                borderRadius: 10,
                fontSize: 13,
              }}
            >
              {requestUrl}
            </div>
          ) : (
            <p style={{ color: "#64748b" }}>아직 요청 URL 없음</p>
          )}
        </div>

        <div
          style={{
            border: "1px solid #ddd",
            borderRadius: 16,
            padding: 16,
            background: "#fff",
          }}
        >
          <h3>복지 검색 결과</h3>

          {policies.length === 0 ? (
            <p style={{ color: "#64748b" }}>조회 결과 없음</p>
          ) : (
            policies.map((policy) => (
              <div
                key={policy.serv_id}
                style={{
                  border: "1px solid #e5e7eb",
                  borderRadius: 12,
                  padding: 12,
                  marginBottom: 12,
                }}
              >
                <strong>{policy.serv_nm}</strong>
                <p style={{ lineHeight: 1.5 }}>{policy.serv_dgst}</p>

                {policy.serv_dtl_link && (
                  <a
                    href={policy.serv_dtl_link}
                    target="_blank"
                    rel="noreferrer"
                  >
                    상세보기
                  </a>
                )}
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}