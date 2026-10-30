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

- 이름·소개·GitHub 아이디: `_config.yml`의 `author`
- 메인 터미널 소개 문구: `_layouts/home.html`
- 카테고리 이름·설명·색상: `_data/categories.yml`
- About 페이지: `about.md`
- 색상·폰트: `assets/css/style.css` 맨 위 변수

## 로컬 미리보기 (Docker)

```bash
docker run --rm -p 4000:4000 -v "$PWD:/srv/jekyll" jekyll/jekyll:4 jekyll serve --force_polling
```
