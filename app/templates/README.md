# Templates Directory

This directory contains Jinja2 templates for the Flask application.

## Structure

```
templates/
├── base.html          # Base template with common layout
├── layouts/           # Layout templates
│   ├── admin.html     # Admin layout
│   ├── api.html       # API documentation layout
│   └── public.html    # Public pages layout
├── components/        # Reusable template components
│   ├── navbar.html    # Navigation bar
│   ├── footer.html    # Footer
│   ├── alerts.html    # Alert messages
│   └── forms.html     # Form components
├── pages/             # Page templates
│   ├── home.html      # Home page
│   ├── about.html     # About page
│   └── contact.html   # Contact page
├── errors/            # Error page templates
│   ├── 404.html       # Not found
│   ├── 500.html       # Server error
│   └── 403.html       # Forbidden
└── emails/            # Email templates
    ├── welcome.html   # Welcome email
    └── reset.html     # Password reset email
```

## Guidelines

1. **Base Template**: All templates should extend `base.html`
2. **Blocks**: Use consistent block names across templates
3. **Components**: Create reusable components for common elements
4. **Responsive**: Ensure all templates are mobile-responsive
5. **Accessibility**: Follow accessibility best practices
6. **Security**: Always escape user input in templates

## Template Inheritance

```html
<!-- base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{% endblock %} - App Name</title>
    {% block styles %}{% endblock %}
</head>
<body>
    {% block navbar %}{% endblock %}
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    {% block footer %}{% endblock %}
    {% block scripts %}{% endblock %}
</body>
</html>

<!-- page.html -->
{% extends "base.html" %}

{% block title %}Page Title{% endblock %}

{% block content %}
<h1>Page Content</h1>
{% endblock %}
```

## Common Blocks

- `title`: Page title
- `styles`: Additional CSS files
- `navbar`: Navigation bar
- `content`: Main page content
- `footer`: Footer content
- `scripts`: Additional JavaScript files

## Jinja2 Features

### Variables
```html
<h1>{{ page_title }}</h1>
<p>Welcome, {{ user.name }}!</p>
```

### Filters
```html
<p>{{ content|truncate(100) }}</p>
<p>{{ date|strftime('%Y-%m-%d') }}</p>
```

### Control Structures
```html
{% if user.is_authenticated %}
    <p>Welcome back!</p>
{% else %}
    <p>Please log in.</p>
{% endif %}

{% for item in items %}
    <li>{{ item.name }}</li>
{% endfor %}
```

### Includes
```html
{% include 'components/navbar.html' %}
```

### Macros
```html
{% macro render_field(field) %}
    <div class="form-group">
        {{ field.label(class="form-label") }}
        {{ field(class="form-control") }}
        {% if field.errors %}
            <div class="form-errors">
                {% for error in field.errors %}
                    <span class="error">{{ error }}</span>
                {% endfor %}
            </div>
        {% endif %}
    </div>
{% endmacro %}
```

## Security Considerations

1. **Auto-escaping**: Jinja2 auto-escapes by default
2. **Safe Filter**: Use `|safe` only for trusted content
3. **CSRF Protection**: Include CSRF tokens in forms
4. **Content Security Policy**: Set appropriate CSP headers

## Performance Tips

1. **Template Caching**: Enable template caching in production
2. **Minimize Includes**: Avoid excessive template includes
3. **Optimize Loops**: Use efficient loop constructs
4. **Asset Bundling**: Bundle and minify CSS/JS assets

See AI_INSTRUCTIONS.md for more details on template development.