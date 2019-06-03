#!/bin/bash

case ${AGENT_JOBSTATUS} in
    *Succeeded*)
        BUILD_MESSAGE=":tada: HELICS-Examples integration test passed (${BUILD_BUILDURI})"
    ;;
    *Failed*)
        BUILD_MESSAGE=":confused: HELICS-Examples integration test had issues (${BUILD_BUILDURI})"
    ;;
esac

# Report build status to PR
if [[ "${BUILD_MESSAGE}" != "" ]]; then
    body='{"body": "'${BUILD_MESSAGE}'"}'

    curl -s -X POST \
        -H "User-Agent: HELICS-bot" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -H "Authorization: token ${HELICSBOT_GH_TOKEN}" \
        -d "$body" \
        https://api.github.com/repos/${HELICS_PR_SLUG}/issues/${HELICS_PR_NUM}/comments
fi
