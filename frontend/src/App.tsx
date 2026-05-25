import { useState } from "react";

interface Policy {
  serv_id: string | null;
  serv_nm: string | null;
  serv_dgst: string | null;
  serv_dtl_link: string | null;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  policies?: Policy[];
}

export default function App() {
  const [sessionId, setSessionId] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [chatList, setChatList] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const API_BASE_URL = "http://127.0.0.1:8000";

  const createSession = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/session`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("세션 생성 실패");
      }

      const data = await response.json();

      setSessionId(data.session_id);

      setChatList([
        {
          role: "assistant",
          content: "채팅 세션이 시작되었습니다. 궁금한 복지제도를 입력해주세요.",
        },
      ]);
    } catch (error) {
      console.error(error);
      alert("세션 생성 중 오류가 발생했습니다.");
    }
  };

  const sendMessage = async () => {
    if (!sessionId) {
      alert("먼저 세션을 생성하세요.");
      return;
    }

    if (!message.trim()) return;

    const userMessage = message.trim();

    setChatList((prev) => [
      ...prev,
      {
        role: "user",
        content: userMessage,
      },
    ]);

    setMessage("");
    setLoading(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/chat/session/${sessionId}/message`,
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

      if (!response.ok) {
        throw new Error("메시지 전송 실패");
      }

      const data = await response.json();

      setChatList((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          policies: data.policies ?? [],
        },
      ]);
    } catch (error) {
      console.error(error);
      alert("메시지 처리 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const endSession = async () => {
    if (!sessionId) {
      alert("종료할 세션이 없습니다.");
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/chat/session/${sessionId}/end`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error("세션 종료 실패");
      }

      const data = await response.json();

      setChatList((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `세션이 종료되었습니다. 상태: ${data.status}`,
        },
      ]);

      setSessionId("");
    } catch (error) {
      console.error(error);
      alert("세션 종료 중 오류가 발생했습니다.");
    }
  };

  return (
    <div
      style={{
        maxWidth: 900,
        margin: "0 auto",
        padding: 24,
        fontFamily: "Arial",
      }}
    >
      <h1>복지 챗봇 테스트</h1>

      <div
        style={{
          display: "flex",
          gap: 8,
          marginBottom: 16,
        }}
      >
        <button onClick={createSession}>세션 생성</button>

        <button onClick={endSession} disabled={!sessionId}>
          세션 종료
        </button>
      </div>

      <div style={{ marginBottom: 16 }}>
        <strong>현재 세션 ID:</strong>

        <div
          style={{
            wordBreak: "break-all",
            color: "#2563eb",
            marginTop: 4,
          }}
        >
          {sessionId || "없음"}
        </div>
      </div>

      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 12,
          overflow: "hidden",
          background: "#ffffff",
        }}
      >
        <div
          style={{
            height: 560,
            overflowY: "auto",
            padding: 16,
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
                marginBottom: 14,
              }}
            >
              <div
                style={{
                  maxWidth: chat.role === "user" ? "70%" : "82%",
                  padding: "12px 14px",
                  borderRadius: 16,
                  background: chat.role === "user" ? "#2563eb" : "#ffffff",
                  color: chat.role === "user" ? "#ffffff" : "#111827",
                  border:
                    chat.role === "user" ? "none" : "1px solid #e5e7eb",
                  lineHeight: 1.5,
                }}
              >
                <div>{chat.content}</div>

                {chat.policies && chat.policies.length > 0 && (
                  <div
                    style={{
                      marginTop: 12,
                      display: "flex",
                      flexDirection: "column",
                      gap: 10,
                    }}
                  >
                    {chat.policies.map((policy, policyIndex) => (
                      <div
                        key={`${policy.serv_id}-${policyIndex}`}
                        style={{
                          background: "#f8fafc",
                          border: "1px solid #dbeafe",
                          borderRadius: 12,
                          padding: 12,
                        }}
                      >
                        <div
                          style={{
                            fontWeight: 700,
                            marginBottom: 8,
                            color: "#1e3a8a",
                          }}
                        >
                          {policy.serv_nm || "제도명 없음"}
                        </div>

                        <div
                          style={{
                            fontSize: 14,
                            lineHeight: 1.5,
                            color: "#374151",
                            marginBottom: 10,
                          }}
                        >
                          {policy.serv_dgst || "요약 정보 없음"}
                        </div>

                        {policy.serv_dtl_link && (
                          <a
                            href={policy.serv_dtl_link}
                            target="_blank"
                            rel="noreferrer"
                            style={{
                              color: "#2563eb",
                              fontSize: 14,
                              textDecoration: "none",
                              fontWeight: 600,
                            }}
                          >
                            상세보기 →
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <p style={{ color: "#64748b", marginTop: 8 }}>
              복지 정보를 검색하는 중...
            </p>
          )}
        </div>

        <div
          style={{
            display: "flex",
            gap: 8,
            padding: 16,
            borderTop: "1px solid #e5e7eb",
            background: "#ffffff",
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
              border: "1px solid #ddd",
              borderRadius: 8,
            }}
          />

          <button onClick={sendMessage} disabled={!sessionId || loading}>
            전송
          </button>
        </div>
      </section>
    </div>
  );
}