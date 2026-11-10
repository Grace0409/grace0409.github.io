---
layout: null
sitemap: false
---
// Jekyll이 빌드할 때 채우는 데이터. 직접 고치지 말고 _data/categories.yml과 _posts를 고칩니다.
{%- assign n_papers = 0 -%}
{%- for g in site.data.papers %}{% for x in g.items %}{% if x.status != 'wip' %}{% assign n_papers = n_papers | plus: 1 %}{% endif %}{% endfor %}{% endfor %}
window.OVAN_DATA={
  base:{{ site.baseurl | jsonify }},
  papers:{{ n_papers }},
  cats:[{% for c in site.data.categories %}{k:{{ c.slug | jsonify }},en:{{ c.en | jsonify }},ko:{{ c.ko | jsonify }},type:{{ c.type | jsonify }},desc:{{ c.desc | jsonify }}}{% unless forloop.last %},{% endunless %}{% endfor %}],
  posts:[
{%- for p in site.posts %}
    [{{ p.date | date: "%Y-%m-%d" | jsonify }},{{ p.url | relative_url | jsonify }},{{ p.category | jsonify }},{{ p.title | jsonify }},{{ p.description | jsonify }}]{% unless forloop.last %},{% endunless %}
{%- endfor %}
  ]
};
