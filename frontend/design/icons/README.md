# 복지챗봇 이미지 아이콘

`originals/*.png`는 생성 당시의 투명 배경 원본 21종입니다. Git에 함께 커밋하여 보존하세요.
`../../public/icons/welfare/*.webp`는 실제 화면에서 사용하는 최대 256px 이미지입니다.
원본은 public 밖에 두므로 Vite 배포 결과에 포함되지 않습니다.
현재 PNG 원본은 편집 가능한 벡터 파일이 아니라 래스터 이미지입니다.

아이콘을 교체하려면 같은 이름의 원본 PNG를 바꾼 후 다음 명령을 실행합니다.

```bash
python -m pip install Pillow
python scripts/prepare-icons.py
```

새 아이콘을 추가할 때는 원본 파일, 화면용 WebP, `src/assets/iconNames.js`의 이름을 함께 추가합니다.
화면에서 쓸 때는 `<AppIcon name="home" size={32} />`와 같이 지정합니다.
텍스트나 버튼의 이름이 아이콘의 의미를 설명하면 alt는 생략합니다.
이미지 자체만 의미를 전달할 때는 `alt="주거 지원"`을 지정합니다.
색상과 광택을 유지해야 하므로 WebP 이미지에 CSS fill은 적용하지 않습니다.
