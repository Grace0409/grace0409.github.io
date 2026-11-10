---
layout: null
sitemap: false
---
// Jekyll이 빌드할 때 채우는 데이터. 직접 고치지 말고 _data/categories.yml과 _posts를 고칩니다.
window.OVAN_DATA={
  base:{{ site.baseurl | jsonify }},
  cats:[{% for c in site.data.categories %}{k:{{ c.slug | jsonify }},en:{{ c.en | jsonify }},ko:{{ c.ko | jsonify }},type:{{ c.type | jsonify }},desc:{{ c.desc | jsonify }}}{% unless forloop.last %},{% endunless %}{% endfor %}],
  posts:[
{%- for p in site.posts %}
    [{{ p.date | date: "%Y-%m-%d" | jsonify }},{{ p.url | relative_url | jsonify }},{{ p.category | jsonify }},{{ p.title | jsonify }},{{ p.description | jsonify }}]{% unless forloop.last %},{% endunless %}
{%- endfor %}
  ]
};
