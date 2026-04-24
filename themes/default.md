# {{ basics.name }}
**{{ basics.label }}**

`{{ basics.email }}` | `{{ basics.phone }}` | [Website]({{ basics.url }}){% if basics.profiles %} | {% for profile in basics.profiles %}[{{ profile.network }}]({{ profile.url }}){% if not loop.last %} | {% endif %}{% endfor %}{% endif %}
{{ basics.location.city }}, {{ basics.location.region }}, {{ basics.location.countryCode }}

{% if basics.summary -%}
## Profile
{{ basics.summary }}
{% endif -%}

{% if skills -%}
## Core Strengths
{% for skill in skills -%}
- **{{ skill.name }}:** {{ skill.keywords | join(", ") }}
{% endfor -%}
{% endif -%}

{% if projects -%}
## Selected Projects
Projects selected to foreground AI, frontend, and product delivery work.

{% for project in projects -%}
### {% if project.url %}[{{ project.name }}]({{ project.url }}){% else %}{{ project.name }}{% endif %}
**Timeline:** {{ project.startDate }} - {{ project.endDate }}

{{ project.description }}
{% if project.highlights -%}
{% for highlight in project.highlights -%}
- {{ highlight }}
{% endfor -%}
{% endif -%}

{% endfor -%}
{% endif -%}

{% if work -%}
## Experience

{% for job in work -%}
### {{ job.position }} | **{{ job.name }}**
{{ job.startDate }} - {{ job.endDate }}{% if job.url %} | [Company]({{ job.url }}){% endif %}

{{ job.summary }}
{% if job.highlights -%}
{% for highlight in job.highlights -%}
- {{ highlight }}
{% endfor -%}
{% endif -%}

{% endfor -%}
{% endif -%}

{% if education -%}
## Education

{% for edu in education -%}
### {% if edu.url %}[{{ edu.institution }}]({{ edu.url }}){% else %}{{ edu.institution }}{% endif %}
**{{ edu.studyType }} in {{ edu.area }}**
{{ edu.startDate }} - {{ edu.endDate }}{% if edu.score %} | GPA/Score: {{ edu.score }}{% endif %}
{% if edu.courses -%}
Relevant coursework: {{ edu.courses | join(", ") }}
{% endif -%}

{% endfor -%}
{% endif %}
