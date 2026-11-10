# OVAN.log

김가영(OVAN)의 보안 학습 & 활동 기록 블로그입니다. GitHub Pages + Jekyll로 만들었고, 테마 없이 레이아웃과 CSS를 직접 작성했습니다.

## 새 글 쓰기

`_posts/YYYY-MM-DD-영문-제목.md` 파일을 만들고 맨 위에 아래 내용을 넣습니다.

```yaml
---
title: "글 제목"
description: 목록에 보일 한 줄 요약 (선택)
date: 2026-11-01 20:00:00 +0900
category: ctf-wargame
tags: [pwnable, writeup]
---
```

| `category` 값 | 카테고리 |
| --- | --- |
| `dev` | 개발 |
| `ctf-wargame` | CTF/Wargame |
| `bug-bounty` | Bug Bounty |
| `tech-docs` | 블로그/기술문서 |
| `paper-conference` | 논문/컨퍼런스 |
| `contest-cert` | 공모전/자격증 |

이미지는 `assets/img/` 아래에 두고 `![설명](/assets/img/파일.png)` 로 넣습니다.

## 자주 고치는 곳

- 이름, 소개, GitHub 아이디: `_config.yml`의 `author`
- 카테고리 이름, 설명, 홈 메뉴 순서: `_data/categories.yml`
- About 페이지 본문과 숫자(PAPERS, NEXT MISSION 등): `about.md`
- 색상, 폰트: `assets/css/style.css` 맨 위 변수 (페이지별 스타일은 `assets/css/<레이아웃>.css`)

## 디자인 구조

게임 UI 느낌(일시정지 메뉴 + 영웅 선택 카드)으로 만든 다크 테마입니다. 포인트 컬러는 핑크(`#ff2e88`) 하나입니다.

| 파일 | 하는 일 |
| --- | --- |
| `_layouts/home.html`, `assets/js/home.js` | 타이틀 화면(PRESS ANY KEY), 메뉴, 카드, 브리핑 창 |
| `_layouts/post.html`, `assets/js/post.js` | 글 머리, 목차, 내비 말풍선, 이전/다음 글 |
| `_layouts/category.html`, `_layouts/archive.html`, `_layouts/about.html` | 카테고리, 달별 아카이브, 프로필 |
| `assets/js/ovan-data.js` | 빌드할 때 글 목록을 채우는 데이터 파일 |
| `assets/js/ovan.js` | 아이콘, 픽셀 그림(여우, UFO), 페이지 전환 |
| `assets/js/eggs.js` | 숨은 장치들 |

타이틀 화면은 브라우저 창마다 한 번만 뜹니다. 다시 보려면 주소 뒤에 `?title=1`을 붙입니다.

## 로컬 미리보기 (Docker)

```bash
docker run --rm -p 4000:4000 -v "$PWD:/srv/jekyll" jekyll/jekyll:4 jekyll serve --force_polling
```
