import AppIcon from './components/AppIcon'
import { useEffect, useState } from "react";
import { apiFetch } from "./api";

type Subscription = {
  id: string; name: string; enabled: boolean; profile_id: string | null;
  conditions: { regions: string[]; themes: string[]; age: number | null; include_keywords: string[]; exclude_keywords: string[] };
  event_types: string[]; unknown_condition_policy: string;
};

export function SubscriptionsPanel({ isActive = true }: { isActive?: boolean }) {
  const [items, setItems] = useState<Subscription[]>([]);
  const [name, setName] = useState("");
  const [region, setRegion] = useState("");
  const [theme, setTheme] = useState("");
  const [keywords, setKeywords] = useState("");
  const [age, setAge] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const load = async () => setItems(await (await apiFetch("/api/subscriptions")).json());
  useEffect(() => {
    let active = true;
    if (isActive) apiFetch("/api/subscriptions").then((r) => r.json()).then((data) => {
      if (active) setItems(data);
    }).catch((e) => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [isActive]);

  const change = async (action: () => Promise<unknown>) => {
    if (busy) return;
    setBusy(true); setError("");
    try { await action(); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : "설정을 저장하지 못했습니다."); }
    finally { setBusy(false); }
  };
  const add = async () => {
    await apiFetch("/api/subscriptions", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name, conditions: {
          regions: region.trim() ? [region.trim()] : [], themes: theme ? [theme] : [],
          age: age === "" ? null : Number(age),
          include_keywords: keywords.split(",").map((s) => s.trim()).filter(Boolean),
        }, event_types: ["new", "updated"], unknown_condition_policy: "include", enabled: true,
      }),
    });
    setName(""); setRegion(""); setTheme(""); setKeywords(""); setAge("");
  };
  return <details className="settings-card mx-[14px] mb-[8px]">
    <summary className="cursor-pointer px-[16px] py-[14px]"><AppIcon name="notification" size={20} /> <span className="ml-2">관심 조건 관리</span></summary>
    <div className="px-[16px] pb-[16px] text-[0.9em]">
    <p className="mb-3 text-[0.85em] text-[#8899BB]">관심 조건을 저장하면 수집된 신규·변경 정책을 상단 알림에서 확인할 수 있어요.</p>
    <form onSubmit={(e) => { e.preventDefault(); void change(add); }} className="grid gap-[12px]">
      <label>구독 이름<input className="settings-input" required maxLength={100} value={name} onChange={(e) => setName(e.target.value)} placeholder="예: 내 주거 지원" /></label>
      <label>지역<input className="settings-input" maxLength={100} value={region} onChange={(e) => setRegion(e.target.value)} placeholder="예: 서울특별시" /></label>
      <label>관심 분야<select className="settings-input" value={theme} onChange={(e) => setTheme(e.target.value)}>
        <option value="">제한 없음</option>
        <option value="040">주거</option><option value="030">생활지원</option>
        <option value="050">일자리</option><option value="100">교육</option>
        <option value="010">신체건강</option><option value="090">보육</option>
        <option value="120">보호·돌봄</option>
      </select></label>
      <label>만 나이<input className="settings-input" type="number" min={0} max={120} value={age} onChange={(e) => setAge(e.target.value)} /></label>
      <label>키워드<input className="settings-input" value={keywords} onChange={(e) => setKeywords(e.target.value)} placeholder="예: 월세, 임차료 (선택)" /></label>
      <small>조건 항목 사이는 모두 충족, 여러 키워드는 하나 이상 일치 기준입니다. 상세 정보가 부족한 제도도 확인 후보에 포함합니다.</small>
      <button className="settings-primary" disabled={busy}>관심 조건 저장</button>
    </form>
    {error && <p role="alert" className="mt-2">{error}</p>}
    {items.map((item) => <div key={item.id} className="border-t border-[#E2E8F0] dark:border-[#2A3050] pt-3 mt-3">
      <strong>{item.name}</strong> · {item.enabled ? "활성" : "일시 정지"}
      <div>
        <button className="text-[#4A7FFF] mr-3 py-2 disabled:opacity-40" disabled={busy} onClick={() => void change(async () => {
          const { id, ...body } = item;
          await apiFetch(`/api/subscriptions/${id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...body, enabled: !item.enabled }) });
        })}>{item.enabled ? "일시 정지" : "다시 활성화"}</button>
        <button className="text-[#8899BB] py-2 disabled:opacity-40" disabled={busy} onClick={() => {
          if (window.confirm("이 구독 조건을 삭제할까요?")) void change(() => apiFetch(`/api/subscriptions/${item.id}`, { method: "DELETE" }));
        }}>삭제</button>
      </div>
    </div>)}
    </div>
  </details>;
}
