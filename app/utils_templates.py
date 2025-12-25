"""Template utility functions for Jinja2 templates.

This module provides helper functions for working with templates,
including version information and common context variables.
"""

from fastapi import Request

from app.__version__ import __version__


def get_template_context(request: Request, **kwargs) -> dict:
    """Get template context with version included.

    This function ensures that version information is available
    in all templates throughout the application.

    Args:
        request: FastAPI request object
        **kwargs: Additional context variables to include

    Returns:
        dict: Template context dictionary with version included

    Example:
        ```python
        return templates.TemplateResponse(
            "dashboard.html",
            get_template_context(request, user=user, wishlists=wishlists)
        )
        ```
    """
    context = {"request": request, "version": __version__}
    context.update(kwargs)
    return context

