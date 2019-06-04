#!/bin/bash
case ${AGENT_JOBSTATUS} in
    *Succeeded*)
        BUILD_MESSAGE=":tada: **HELICS-Examples** integration test passed: [[build log]](https://dev.azure.com/HELICS-test/HELICS-Examples/_build/results?buildId=${BUILD_BUILDID}) [[commit]](https://github.com/GMLC-TDC/HELICS-src/commit/${HELICS_COMMITISH})"
    ;;
    *Failed*)
        BUILD_MESSAGE=":confused: **HELICS-Examples** integration test had some problems: [[build log]](https://dev.azure.com/HELICS-test/HELICS-Examples/_build/results?buildId=${BUILD_BUILDID})  [[commit]](https://github.com/GMLC-TDC/HELICS-src/commit/${HELICS_COMMITISH})"
    ;;
esac

# Report build status to PR
if [[ "${BUILD_MESSAGE}" != "" ]]; then
    echo "Reporting build status $AGENT_JOBSTATUS to github.com/${HELICS_PR_SLUG}/issues/${HELICS_PR_NUM}"
    body='{"body": "'${BUILD_MESSAGE}'"}'
    curl -s -X POST \
        -H "User-Agent: HELICS-bot" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -H "Authorization: token ${HELICSBOT_GH_TOKEN}" \
        -d "$body" \
        https://api.github.com/repos/${HELICS_PR_SLUG}/issues/${HELICS_PR_NUM}/comments
fi
