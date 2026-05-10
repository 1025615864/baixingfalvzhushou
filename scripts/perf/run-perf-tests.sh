#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/results"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BASE_URL="${BASE_URL:-http://localhost:8000}"
TEST_USERNAME="${TEST_USERNAME:-admin}"
TEST_PASSWORD="${TEST_PASSWORD:-admin123}"

mkdir -p "${RESULTS_DIR}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

check_k6() {
  if ! command -v k6 &>/dev/null; then
    log_error "k6 is not installed"
    log_info "Install: https://k6.io/docs/get-started/installation/"
    exit 1
  fi
  log_info "k6 version: $(k6 version)"
}

run_smoke_test() {
  local smoke_output="${RESULTS_DIR}/smoke_${TIMESTAMP}.json"
  local smoke_summary="${RESULTS_DIR}/smoke_${TIMESTAMP}_summary.txt"

  log_info "Running smoke test (10 VUs, 1m)..."
  k6 run \
    --env BASE_URL="${BASE_URL}" \
    --env TEST_USERNAME="${TEST_USERNAME}" \
    --env TEST_PASSWORD="${TEST_PASSWORD}" \
    --out json="${smoke_output}" \
    --summary-export="${RESULTS_DIR}/smoke_summary_${TIMESTAMP}.json" \
    "${SCRIPT_DIR}/k6-smoke-test.js" 2>&1 | tee "${smoke_summary}"

  if [ ${PIPESTATUS[0]} -eq 0 ]; then
    log_info "Smoke test PASSED"
  else
    log_error "Smoke test FAILED"
    return 1
  fi
}

run_load_test() {
  local load_output="${RESULTS_DIR}/load_${TIMESTAMP}.json"
  local load_summary="${RESULTS_DIR}/load_${TIMESTAMP}_summary.txt"

  log_info "Running load test (10->100->500 VUs, 5m30s)..."
  k6 run \
    --env BASE_URL="${BASE_URL}" \
    --env TEST_USERNAME="${TEST_USERNAME}" \
    --env TEST_PASSWORD="${TEST_PASSWORD}" \
    --out json="${load_output}" \
    --summary-export="${RESULTS_DIR}/load_summary_${TIMESTAMP}.json" \
    "${SCRIPT_DIR}/k6-load-test.js" 2>&1 | tee "${load_summary}"

  if [ ${PIPESTATUS[0]} -eq 0 ]; then
    log_info "Load test PASSED"
  else
    log_error "Load test FAILED"
    return 1
  fi
}

print_summary() {
  local load_summary_json="${RESULTS_DIR}/load_summary_${TIMESTAMP}.json"

  echo ""
  echo "=========================================="
  echo "       Performance Test Summary"
  echo "=========================================="
  echo "  Timestamp:  ${TIMESTAMP}"
  echo "  Base URL:   ${BASE_URL}"
  echo "  Results:    ${RESULTS_DIR}/"
  echo ""

  if [ -f "${load_summary_json}" ]; then
    log_info "Load test metrics:"
    python3 -c "
import json, sys
with open('${load_summary_json}') as f:
    data = json.load(f)
metrics = data.get('metrics', {})
for name in ['http_req_duration', 'errors', 'health_latency', 'login_latency',
             'home_latency', 'lawyers_latency', 'forum_posts_latency',
             'news_latency', 'knowledge_latency']:
    m = metrics.get(name, {})
    avg = m.get('avg', 'N/A')
    p95 = m.get('values', {}).get('p(95)', 'N/A')
    p99 = m.get('values', {}).get('p(99)', 'N/A')
    if isinstance(avg, (int, float)):
        avg = f'{avg:.2f}ms'
    if isinstance(p95, (int, float)):
        p95 = f'{p95:.2f}ms'
    if isinstance(p99, (int, float)):
        p99 = f'{p99:.2f}ms'
    print(f'  {name:30s} avg={avg:>10s}  p95={p95:>10s}  p99={p99:>10s}')
" 2>/dev/null || log_warn "Could not parse summary JSON"
  fi

  echo "=========================================="
}

cleanup_old_results() {
  local count
  count=$(find "${RESULTS_DIR}" -name "*.json" -type f 2>/dev/null | wc -l)
  if [ "${count}" -gt 100 ]; then
    log_info "Cleaning up old results (keeping latest 50 sets)..."
    ls -t "${RESULTS_DIR}"/*.json 2>/dev/null | tail -n +101 | xargs -r rm -f
  fi
}

main() {
  log_info "Performance test runner"
  log_info "Target: ${BASE_URL}"

  check_k6

  if ! run_smoke_test; then
    log_error "Smoke test failed, skipping load test"
    print_summary
    exit 1
  fi

  if ! run_load_test; then
    log_error "Load test failed"
    print_summary
    exit 1
  fi

  print_summary
  cleanup_old_results

  log_info "All performance tests completed successfully"
}

main "$@"
