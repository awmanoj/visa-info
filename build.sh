#!/usr/bin/bash
set -euo pipefail

. .env

IMAGE_NAME="${IMAGE_NAME:-visa-info}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DOCKERHUB_USER="${DOCKERHUB_USER:-}"

PUSH=0
for arg in "$@"; do
  case "$arg" in
    --push) PUSH=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 1 ;;
  esac
done

LOCAL_REF="${IMAGE_NAME}:${IMAGE_TAG}"
docker build --platform linux/amd64 -t "${LOCAL_REF}" "$(dirname "$0")"

if [[ "${PUSH}" -eq 1 ]]; then
  if [[ -z "${DOCKERHUB_USER}" ]]; then
    echo "DOCKERHUB_USER must be set when using --push" >&2
    exit 1
  fi
  REMOTE_REF="docker.io/${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
  docker tag "${LOCAL_REF}" "${REMOTE_REF}"
  docker push "${REMOTE_REF}"
  echo "Pushed ${REMOTE_REF}"
fi
