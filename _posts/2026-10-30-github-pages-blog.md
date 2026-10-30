---
title: "GitHub Pages와 Jekyll로 나만의 블로그 만들기"
description: GitHub Pages의 개념부터 username.github.io 블로그를 직접 만들고 배포하기까지의 과정을 정리했습니다.
date: 2026-10-30 20:00:00 +0900
category: dev
tags: [github-pages, jekyll]
---

이 블로그를 만들면서 알게 된 GitHub Pages의 개념과 사용 방법을 정리합니다.

## GitHub Pages란?

**GitHub Pages**는 GitHub 저장소에 올린 HTML·CSS·JS 파일을 그대로 웹사이트로 호스팅해 주는 **정적 사이트 호스팅 서비스**입니다.

- 별도의 서버 없이 `git push`만으로 사이트가 배포됩니다.
- 공개 저장소라면 무료로 사용할 수 있습니다.
- 서버 측 코드(PHP, DB 등)는 실행할 수 없고, **정적 파일만** 제공합니다.
- 기본적으로 **Jekyll**이라는 정적 사이트 생성기가 내장되어 있어서, 마크다운으로 글을 쓰면 HTML로 변환해 줍니다.

### 사이트 종류

| 종류 | 저장소 이름 | 주소 |
| --- | --- | --- |
| 사용자 사이트 | `<username>.github.io` | `https://<username>.github.io` |
| 프로젝트 사이트 | 아무 이름 (예: `my-project`) | `https://<username>.github.io/my-project` |

개인 블로그는 보통 **사용자 사이트**로 만듭니다. 저장소 이름을 반드시 `아이디.github.io` 형태로 지어야 합니다.

## Jekyll은 어떻게 동작할까?

Jekyll은 정해진 폴더 구조를 읽어서 완성된 HTML 사이트(`_site/`)를 만들어 냅니다.

```text
.
├── _config.yml        # 사이트 전체 설정 (제목, URL, 플러그인 등)
├── _data/             # YAML 데이터 (이 블로그는 카테고리 목록을 여기에 둠)
├── _includes/         # 여러 페이지에서 재사용하는 HTML 조각
├── _layouts/          # 페이지 뼈대 (default, post, category ...)
├── _posts/            # 블로그 글 (YYYY-MM-DD-제목.md)
├── assets/            # CSS, JS, 이미지
└── index.html         # 메인 페이지
```

글 파일 맨 위에는 **front matter**라고 부르는 YAML 블록을 넣어 제목·날짜·카테고리 같은 정보를 적습니다.

```yaml
---
title: "글 제목"
date: 2026-10-30 20:00:00 +0900
category: ctf-wargame
tags: [pwnable, bof]
---
```

## 블로그를 만든 과정

1. GitHub에 `아이디.github.io` 이름으로 **Public** 저장소를 만든다.
2. Jekyll 사이트 파일을 작성한다. 기본 테마 대신 레이아웃과 CSS를 직접 짜서 터미널 느낌의 디자인으로 꾸몄다.
3. 6개 카테고리(개발, CTF/Wargame, Bug Bounty, 블로그/기술문서, 논문/컨퍼런스, 공모전/자격증)를 `_data/categories.yml`에 정의하고, 카테고리별 페이지를 만들었다.
4. 저장소에 push 한다.

```bash
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/<username>/<username>.github.io.git
git push -u origin main
```

5. 저장소의 **Settings → Pages**에서 배포 소스가 `main` 브랜치 `/ (root)`인지 확인한다.
6. 1~2분 뒤 `https://<username>.github.io`에 접속하면 끝!

## 새 글 쓰는 법

`_posts/` 폴더에 `2026-11-01-my-first-writeup.md` 같은 이름으로 파일을 만들고, front matter의 `category`에 아래 값 중 하나를 넣으면 해당 카테고리에 자동으로 분류됩니다.

| category 값 | 카테고리 |
| --- | --- |
| `dev` | 개발 |
| `ctf-wargame` | CTF/Wargame |
| `bug-bounty` | Bug Bounty |
| `tech-docs` | 블로그/기술문서 |
| `paper-conference` | 논문/컨퍼런스 |
| `contest-cert` | 공모전/자격증 |

## 알아두면 좋은 점

- 사이트 용량은 **1GB** 이하를 권장하고, 빌드는 시간당 횟수 제한(soft limit)이 있습니다.
- GitHub Pages가 지원하는 플러그인만 쓸 수 있습니다. (이 블로그는 `jekyll-feed`, `jekyll-seo-tag`, `jekyll-sitemap` 사용)
- 공개 저장소이므로 **API 키나 개인정보를 커밋하지 않도록** 주의해야 합니다. 보안 공부하는 사람이 가장 먼저 지켜야 할 것!
