# 이미지 아이콘 적용본

2026-10-03 통합본의 frontend를 기준으로 만든 변경본입니다.
백엔드 수정이나 DB 변경 없이 프론트 파일만 적용합니다.

## 저장 구조

- `design/icons/originals/`: 투명 PNG 원본 21종. Git에 보관하며 배포하지 않음.
- `public/icons/welfare/`: 실제 브라우저에서 사용하는 최대 256px WebP 21종.
- `src/assets/iconNames.js`: 사용 가능한 아이콘 이름.
- `src/assets/legacyIcons.js`: 이전 이모지 값의 이미지 키 변환.
- `src/components/AppIcon.jsx`: URL, 크기, 접근성, 오류 처리를 통일한 컴포넌트.
- `scripts/prepare-icons.py`: 원본에서 WebP 재생성.

## 적용 방법

기존 frontend를 백업하고 이 폴더의 파일을 같은 경로에 복사하세요.
이 압축파일에는 `.env`, `node_modules`, `dist`가 없습니다.
기존 frontend/.env는 그대로 유지하세요. 프로젝트가 통합본 이후 변경되었다면
수정된 컴포넌트를 비교하여 병합하세요. 현재 PC의 최신 코드를 확인한 결과는 아닙니다.

```bash
npm ci
npm run dev
```

배포 검증은 `npm test`와 `npm run build`로 실행합니다.

## 변경된 화면

Header, HomeScreen, ChatArea, BottomNav, WelfareCard, ChatList,
SettingsPage, SearchSettings, NotificationsPanel, SubscriptionsPanel.
policyMapper는 이모지 대신 의미를 가진 이름을 반환합니다.
기존 이모지 값이 들어온 카드도 AppIcon의 호환 매핑으로 표시합니다.
굵은 글씨의 B, 앱 정보의 ⓘ, 체크 및 닫기 기호와
음성 입력/전송의 기존 SVG는 해당 기능을 표시하는 코드 형태로 유지합니다.

## 예제

```jsx
import AppIcon from './AppIcon'

// 홈 추천 카드 안
<AppIcon name="home" size={38} />
// 상단 챗봇 아이콘
<AppIcon name="robot" size={34} />
// 정책 카드 (policyMapper가 icon 키를 반환)
<AppIcon name={icon} size={44} />
```

BASE_URL을 사용하므로 Vite base가 하위 경로여도 아이콘 경로가 함께 맞춰집니다.
잘못된 키와 이미지 로딩 오류는 general-welfare 아이콘으로 대체하며,
대체 이미지까지 실패하면 깨진 이미지 대신 해당 이미지를 숨깁니다.
원본과 화면용 파일을 함께 Git에 올려야 다른 PC에서도 같은 이미지가 나타납니다.
AI 생성 시안 중 recommendation/general-welfare는 로봇을 포함한 복합 이미지이므로
20px에서는 세부 표현이 작아집니다. 추후 단순 시안으로 같은 파일만 교체할 수 있습니다.
