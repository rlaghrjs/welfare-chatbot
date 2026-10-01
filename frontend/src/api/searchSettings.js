export const REGIONS = ['서울특별시', '부산광역시', '대구광역시', '인천광역시', '광주광역시', '대전광역시', '울산광역시', '세종특별자치시', '경기도', '강원특별자치도', '충청북도', '충청남도', '전북특별자치도', '전라남도', '경상북도', '경상남도', '제주특별자치도']
export const LIFE = [['001','영유아'],['002','아동'],['003','청소년'],['004','청년'],['005','중장년'],['006','노년'],['007','임신·출산']]
export const TARGETS = [['010','다문화·탈북민'],['020','다자녀'],['030','보훈대상자'],['040','장애인'],['050','저소득'],['060','한부모·조손']]
export const THEMES = [['010','신체건강'],['020','정신건강'],['030','생활지원'],['040','주거'],['050','일자리'],['060','문화·여가'],['070','안전·위기'],['080','임신·출산'],['090','보육'],['100','교육'],['110','입양·위탁'],['120','보호·돌봄'],['130','서민금융'],['140','법률'],['150','관계개선'],['160','에너지']]

export function readSearchSettings() {
  let profile = {}
  try { profile = JSON.parse(localStorage.getItem('welfareProfile') || '{}') || {} } catch { /* use defaults */ }
  return { region: localStorage.getItem('ctpvNm') || '', useProfile: localStorage.getItem('useWelfareProfile') === 'true', profile }
}

export function searchPayload() {
  const { region, useProfile, profile } = readSearchSettings()
  const clean = {}
  if (profile.age !== '' && profile.age != null && Number.isInteger(Number(profile.age))) clean.age = Number(profile.age)
  for (const key of ['lifeArray', 'trgterIndvdlArray', 'intrsThemaArray']) if (profile[key]) clean[key] = profile[key]
  return { ctpvNm: region || null, useProfile, profile: useProfile ? clean : null }
}
