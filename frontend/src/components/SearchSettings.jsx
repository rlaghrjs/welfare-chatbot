import { useState } from 'react'
import { REGIONS, LIFE, TARGETS, THEMES, readSearchSettings } from '../api/searchSettings'

export default function SearchSettings() {
  const [settings, setSettings] = useState(readSearchSettings)
  const [saved, setSaved] = useState(false)
  const update = (patch) => { setSettings(s => ({ ...s, ...patch })); setSaved(false) }
  const profile = (key, value) => update({ profile: { ...settings.profile, [key]: value } })
  const save = (e) => {
    e.preventDefault()
    localStorage.setItem('ctpvNm', settings.region)
    localStorage.setItem('useWelfareProfile', String(settings.useProfile))
    localStorage.setItem('welfareProfile', JSON.stringify(settings.profile))
    setSaved(true)
  }
  return <details className="settings-card mx-[14px] mb-[8px]">
    <summary className="cursor-pointer px-[16px] py-[14px]">🔎 <span className="ml-2">복지 검색 설정</span></summary>
    <form onSubmit={save} className="px-[16px] pb-[16px] grid gap-[12px] text-[0.9em]">
      <label>검색 지역<select className="settings-input" value={settings.region} onChange={e => update({ region: e.target.value })}><option value="">전국 / 지역 제한 없음</option>{REGIONS.map(r => <option key={r}>{r}</option>)}</select></label>
      <label className="flex items-center gap-2"><input type="checkbox" checked={settings.useProfile} onChange={e => update({ useProfile: e.target.checked })} />내 조건을 검색에 반영</label>
      <label>만 나이<input className="settings-input" type="number" min="0" max="120" value={settings.profile.age ?? ''} onChange={e => profile('age', e.target.value === '' ? '' : Number(e.target.value))} /></label>
      {[["lifeArray", "생애주기", LIFE], ["trgterIndvdlArray", "가구상황", TARGETS], ["intrsThemaArray", "관심 분야", THEMES]].map(([key, label, options]) => <label key={key}>{label}<select className="settings-input" value={settings.profile[key] || ''} onChange={e => profile(key, e.target.value)}><option value="">선택 안 함</option>{options.map(([code, title]) => <option key={code} value={code}>{title}</option>)}</select></label>)}
      <button className="settings-primary">검색 설정 저장</button>
      {saved && <p role="status" className="text-[#4A7FFF]">저장했어요. 다음 질문부터 반영됩니다.</p>}
    </form>
  </details>
}
