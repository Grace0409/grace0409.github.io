---
title: "GitHub Pages와 Jekyll로 나만의 블로그 만들기"
description: GitHub Pages가 뭔지부터 username.github.io 블로그를 만들고 배포하기까지 정리했습니다.
date: 2026-10-30 20:00:00 +0900
category: dev
tags: [github-pages, jekyll]
---

이 블로그를 만들면서 알게 된 GitHub Pages 이야기입니다.

## GitHub Pages란?

GitHub 저장소에 올린 HTML, CSS, JS 파일을 그대로 웹사이트로 띄워 주는 정적 사이트 호스팅입니다. 서버를 따로 차리지 않아도 `git push` 한 번이면 배포됩니다. 공개 저장소라면 무료입니다!

대신 PHP나 DB 같은 서버 코드는 돌릴 수 없습니다. 정적 파일만 내보냅니다. Jekyll이라는 정적 사이트 생성기가 기본으로 들어 있어서, 마크다운으로 글을 쓰면 HTML로 바꿔 줍니다.

사이트는 두 종류가 있습니다.

| 종류 | 저장소 이름 | 주소 |
| --- | --- | --- |
| 사용자 사이트 | `<username>.github.io` | `https://<username>.github.io` |
| 프로젝트 사이트 | 아무 이름 (예: `my-project`) | `https://<username>.github.io/my-project` |

개인 블로그는 보통 사용자 사이트로 만듭니다. 저장소 이름은 꼭 `아이디.github.io`여야 합니다.

## Jekyll은 어떻게 돌아갈까

정해진 폴더 구조를 읽어서 완성된 HTML 사이트(`_site/`)를 만들어 냅니다.

```text
.
├── _config.yml        # 사이트 설정 (제목, URL, 플러그인)
├── _data/             # YAML 데이터 (여기선 카테고리 목록)
├── _includes/         # 여러 페이지에서 같이 쓰는 HTML 조각
├── _layouts/          # 페이지 뼈대 (default, post, category ...)
├── _posts/            # 글 (YYYY-MM-DD-제목.md)
├── assets/            # CSS, JS, 이미지
└── index.html         # 메인 페이지
```

글 파일 맨 위에는 front matter라는 YAML 블록을 넣습니다. 제목, 날짜, 카테고리 같은 정보를 적는 곳입니다.

```yaml
---
title: "글 제목"
date: 2026-10-30 20:00:00 +0900
category: ctf-wargame
tags: [pwnable, bof]
---
```

## 이 블로그를 만든 순서

먼저 GitHub에 `아이디.github.io` 이름으로 Public 저장소를 만들었습니다.

기본 테마는 쓰지 않았습니다. 레이아웃과 CSS를 직접 짰고, 좋아하는 게임 UI 느낌을 살려서 핑크와 블랙으로 꾸몄습니다 :) 카테고리 6개는 `_data/categories.yml`에 정의하고 카테고리마다 페이지를 만들었습니다.

그다음 push 했습니다.

```bash
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/<username>/<username>.github.io.git
git push -u origin main
```

마지막으로 저장소 Settings의 Pages 메뉴에서 배포 소스가 `main` 브랜치 `/ (root)`인지 확인했습니다. 1~2분 기다렸다가 `https://<username>.github.io`에 들어가면 끝입니다!

## 새 글 쓰는 법

`_posts/` 폴더에 `2026-11-01-my-first-writeup.md` 같은 이름으로 파일을 만듭니다. front matter의 `category`에 아래 값 중 하나를 넣으면 알아서 그 카테고리로 들어갑니다.

| category 값 | 카테고리 |
| --- | --- |
| `dev` | 개발 |
| `ctf-wargame` | CTF/Wargame |
| `bug-bounty` | Bug Bounty |
| `tech-docs` | 블로그/기술문서 |
| `paper-conference` | 논문/컨퍼런스 |
| `contest-cert` | 공모전/자격증 |

## 알아 두면 좋은 것

사이트 용량은 1GB 아래를 권장합니다. 빌드도 시간당 횟수 제한이 느슨하게 걸려 있습니다. 플러그인은 GitHub Pages가 지원하는 것만 쓸 수 있고, 여기서는 `jekyll-feed`, `jekyll-seo-tag`, `jekyll-sitemap`을 씁니다.

그리고 공개 저장소이니 API 키나 개인정보는 절대 커밋하면 안 됩니다. 보안 공부하는 사람이 가장 먼저 지켜야 할 부분입니다.
