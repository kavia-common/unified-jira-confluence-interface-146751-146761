#!/bin/bash
cd /home/kavia/workspace/code-generation/unified-jira-confluence-interface-146751-146761/integration_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

