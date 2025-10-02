import json
from pathlib import Path

from src.api.main import app

def generate_openapi_spec():
    """Generate and save OpenAPI specification"""
    # Get the OpenAPI schema with all routes and documentation
    openapi_schema = app.openapi()

    # Enhance the schema with additional metadata
    openapi_schema.update({
        "info": {
            "title": "JIRA-Confluence Integration API",
            "description": """
            RESTful API for integrating JIRA and Confluence services.
            Provides endpoints for:
            - User authentication and management
            - JIRA issue tracking and management
            - Confluence page creation and management
            - OAuth2 integration with Atlassian services
            """,
            "version": "1.0.0",
            "contact": {
                "name": "API Support",
                "email": "support@example.com"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "security": [
            {"bearerAuth": []}
        ]
    })

    # Add security scheme
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # Ensure output directory exists
    output_dir = Path("interfaces")
    output_dir.mkdir(exist_ok=True)
    
    # Write specification to file
    output_path = output_dir / "openapi.json"
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)

if __name__ == "__main__":
    generate_openapi_spec()
