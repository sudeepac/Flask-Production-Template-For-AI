# Static Files Directory

This directory contains static assets for the Flask application.

## Structure

```
static/
├── css/           # Stylesheets
├── js/            # JavaScript files
├── img/           # Images
├── fonts/         # Font files
├── favicon.ico    # Favicon
└── robots.txt     # Robots.txt file
```

## Guidelines

1. **CSS Files**: Place all stylesheets in the `css/` directory
2. **JavaScript**: Place all JavaScript files in the `js/` directory
3. **Images**: Place all images in the `img/` directory
4. **Fonts**: Place all font files in the `fonts/` directory
5. **Optimization**: Minify CSS and JS files for production
6. **Versioning**: Use cache-busting techniques for updated assets

## Usage

In templates, reference static files using Flask's `url_for()` function:

```html
<!-- CSS -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">

<!-- JavaScript -->
<script src="{{ url_for('static', filename='js/app.js') }}"></script>

<!-- Images -->
<img src="{{ url_for('static', filename='img/logo.png') }}" alt="Logo">
```

## Development vs Production

- **Development**: Use unminified files for easier debugging
- **Production**: Use minified and compressed files for better performance
- **CDN**: Consider using a CDN for static assets in production

See AI_INSTRUCTIONS.md for more details on static file management.
