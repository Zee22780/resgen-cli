# {{ basics.name }}
**{{ basics.label }}**

Email: {{ basics.email }} | Phone: {{ basics.phone }} | Website: {{ basics.url }}
Location: {{ basics.location.city }}, {{ basics.location.region }}, {{ basics.location.countryCode }}

{% if basics.summary %}
## Summary
{{ basics.summary }}
{% endif %}

{% if work %}
## Experience

{% for job in work %}
### {{ job.position }} at {{ job.name }}
*{{ job.startDate }} - {{ job.endDate }}*

{{ job.summary }}
{% if job.highlights %}
* {% for highlight in job.highlights %}{{ highlight }}{% if not loop.last %}
* {% endif %}{% endfor %}
{% endif %}
{% endfor %}
{% endif %}

{% if education %}
## Education

{% for edu in education %}
### {{ edu.institution }}
**{{ edu.studyType }} in {{ edu.area }}**
*{{ edu.startDate }} - {{ edu.endDate }}*
{% endfor %}
{% endif %}

{% if skills %}
## Skills

{% for skill in skills %}
* **{{ skill.name }}**: {{ skill.keywords | join(', ') }}
{% endfor %}
{% endif %}

{% if projects %}
## Projects

{% for project in projects %}
### {{ project.name }}
*{{ project.startDate }} - {{ project.endDate }}* | [Link]({{ project.url }})

{{ project.description }}
{% if project.highlights %}
* {% for highlight in project.highlights %}{{ highlight }}{% if not loop.last %}
* {% endif %}{% endfor %}
{% endif %}
{% endfor %}
{% endif %}
