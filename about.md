---
layout: about
title: About
nav: about
description: 분산 시스템과 AI 에이전트 보안을 연구하는 김가영(OVAN)입니다.
permalink: /about/
stats:
  - { label: PAPERS, value: 12 }
  - { label: KCI JOURNAL, value: 1 }
  - { label: AWARDS, value: 3 }
mission: { text: "MobiSec 2026 구두발표", when: "2026.12", progress: 80 }
---

<section class="sec prose" markdown="1">

## 안녕하세요, OVAN입니다!

김가영(OVAN)입니다! OVAN은 좋아하는 프로게이머가 추천해 준 닉네임입니다 :) 성신여자대학교 융합보안공학과에 다니고 있습니다. 2025년 2월부터 학부연구생으로 연구하고 있고, 지금은 SSS Lab에 있습니다.

고정된 규칙에 기대는 보안 기법은 규칙을 배운 공격자에게 뚫립니다. 저는 그 지점을 주로 파고듭니다. 게임이론이나 이상 탐지 같은 수학적 모델로, 방어 판단이 상황에 맞춰 바뀌게 만드는 연구를 합니다. 연구 밖에서는 웹, 모바일, 바이너리를 직접 뜯어 보면서 공부합니다.

</section>

<section class="sec">
  <h2 class="h">Research <small>연구 분야</small></h2>
  <ul class="rows">
    <li><i>DISTRIBUTED</i><div><b>적응형 이상 노드 탐지</b><span>AVF에서 SVF, ZT-SVF까지. Stackelberg 균형으로 검증합니다</span></div></li>
    <li><i>SYSTEM</i><div><b>동적 메모리 할당 보안</b><span>CPP-DMA를 제안하고, 뚫고, 막아서 KCI 저널까지</span></div></li>
    <li><i>AI AGENT</i><div><b>AI 에이전트, 포렌식 보안</b><span>MCP 도구 연쇄 오염, 증거 속 프롬프트 인젝션</span></div></li>
    <li><i>CPS</i><div><b>물리 계층, 제어 시스템</b><span>전원선 은닉 채널, 스마트그리드 FDIA, ICS</span></div></li>
  </ul>
</section>

{% include quest-log.html %}

<section class="sec">
  <h2 class="h">Mains <small>좋아하는 것</small></h2>
  <div class="mains">
    <div class="main"><div class="face" data-pix="fox"></div><div><div class="g">GAME</div><h3>오버워치<em>최애 키리코</em></h3><p>탱딜힐 다 하는 올라운더! 같이 하실 분? 🙋‍♀️</p></div></div>
    <div class="main"><div class="face" data-pix="ufo"></div><div><div class="g">GAME</div><h3>페르소나<em>최애 후타바</em></h3><p>멋진 캐릭터들과 감동적인 스토리, 감각적인 디자인</p></div></div>
    <div class="main"><div class="face">{% include icon.html k="ctf-wargame" %}</div><div><div class="g">STUDY</div><h3>보안</h3><p>이 규칙, 공격자가 알면 뚫리지 않을까? 그 질문을 따라가는 게 제일 재밌습니다 :)</p></div></div>
  </div>
  <p class="note">사이트 곳곳에 숨어 있는 여우와 UFO는 키리코와 후타바에게 보내는 인사입니다 :)</p>
</section>

<section class="sec">
  <h2 class="h">Log <small>활동 기록</small></h2>
  <ul class="tline">
    <li><time>2026.10</time><span><strong>OVAN.log</strong> 블로그 개설</span></li>
    <li><time>2026 ~</time><span>Dreamhack 기반 워게임 라이트업, 보안 개념 노트 연재</span></li>
    <li><time>2026.2학기 ~</time><span>캡스톤 디자인 팀 AlIce 팀장. AI 포렌식 에이전트를 노리는 프롬프트 인젝션을 막는 연구</span></li>
    <li><time>2026.2학기 ~</time><span>해킹 동아리 <strong>HASH</strong>에서 버그바운티 팀 프로젝트 팀장, 포렌식 정기세션 발표</span></li>
    <li><time>2026 여름</time><span><strong>버그헌팅마스터 3기</strong> B트랙 수료, 사이버가디언즈 보안캠프 보조멘토</span></li>
    <li><time>2026.06</time><span>KISA K-Shield Jr. 기초 2차 수료</span></li>
    <li><time>2026.04 ~</time><span>학부연구생, <strong>SSS Lab</strong> (지도 최현우 교수)</span></li>
    <li><time>2026 ~</time><span>CTF 워게임 스터디 팀장</span></li>
    <li><time>2025</time><span>해킹 동아리 <strong>I.Sly() 회장</strong>, 사이버가디언즈 보안캠프 보조멘토</span></li>
    <li><time>2025.02 ~ 2026.03</time><span>학부연구생, 이일구 교수 연구실</span></li>
    <li><time>2024.09</time><span>해킹 동아리 I.Sly() 입부 (10~12기 수료)</span></li>
  </ul>
</section>

<section class="sec prose" markdown="1">

## 기술 스택

| 분야 | 도구 |
| --- | --- |
| Web | Burp Suite, sqlmap, nuclei, ffuf, feroxbuster, dalfox |
| Mobile / Reverse | jadx, Frida, apktool, Ghidra, smali, adb |
| System / Pwn | pwntools, gdb, WSL2, Docker, Vulhub, Kali, nmap |
| Research | Python, PyTorch, 시뮬레이션 설계, MITRE ATT&CK for ICS |

## Contact

메일은 [20240925@sungshin.ac.kr](mailto:20240925@sungshin.ac.kr)로 보내 주세요. 코드는 GitHub [Grace0409](https://github.com/Grace0409)에, 연구 목록은 [Google Sites](https://sites.google.com/sungshin.ac.kr/gayeongkim/%ED%99%88)에 있습니다.

</section>
