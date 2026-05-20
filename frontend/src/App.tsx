import { useState } from "react";

interface Policy {
  serv_id: string;
  serv_nm: string | null;
  serv_dgst: string | null;
  serv_dtl_link: string | null;
}

export default function App() {
  const [message, setMessage] = useState("");
  const [requestUrl, setRequestUrl] = useState("");
  const [intent, setIntent] = useState<any>(null);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!message.trim()) return;

    setLoading(true);

    const response = await fetch("http://127.0.0.1:8000/api/chat/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();

    setIntent(data.intent);
    setRequestUrl(data.request_url);
    setPolicies(data.policies);

    setLoading(false);
  };

  return (
    <div style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
      <h1>복지제도 NLP 검색 테스트</h1>

      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="예: 청년 월세 지원 알려줘"
          style={{ flex: 1, padding: 12 }}
        />

        <button onClick={handleSearch} disabled={loading}>
          {loading ? "검색 중..." : "검색"}
        </button>
      </div>

      {intent && (
        <section style={{ marginTop: 24 }}>
          <h2>NLP 분석 결과</h2>
          <pre>{JSON.stringify(intent, null, 2)}</pre>
        </section>
      )}

      {requestUrl && (
        <section style={{ marginTop: 24 }}>
          <h2>생성된 API 요청 URL</h2>
          <div style={{ wordBreak: "break-all", background: "#f3f4f6", padding: 12 }}>
            {requestUrl}
          </div>
        </section>
      )}

      <section style={{ marginTop: 24 }}>
        <h2>조회 결과</h2>

        {policies.length === 0 ? (
          <p>조회 결과가 없습니다.</p>
        ) : (
          policies.map((policy) => (
            <div
              key={policy.serv_id}
              style={{
                border: "1px solid #ddd",
                borderRadius: 12,
                padding: 16,
                marginBottom: 12,
              }}
            >
              <h3>{policy.serv_nm}</h3>
              <p>{policy.serv_dgst}</p>

              {policy.serv_dtl_link && (
                <a href={policy.serv_dtl_link} target="_blank">
                  상세보기
                </a>
              )}
            </div>
          ))
        )}
      </section>
    </div>
  );
}