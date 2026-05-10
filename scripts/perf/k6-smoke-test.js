import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TEST_USERNAME = __ENV.TEST_USERNAME || 'admin';
const TEST_PASSWORD = __ENV.TEST_PASSWORD || 'admin123';

export const options = {
  vus: 10,
  duration: '1m',
  thresholds: {
    http_req_failed: ['rate<0.5'],
  },
  noConnectionReuse: false,
  userAgent: 'k6-smoke-test/1.0',
};

export default function () {
  const res1 = http.get(`${BASE_URL}/health`, { timeout: '5s' });
  check(res1, { 'health responds': (r) => r.status === 200 });

  const res2 = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ username: TEST_USERNAME, password: TEST_PASSWORD }),
    { headers: { 'Content-Type': 'application/json' }, timeout: '10s' }
  );
  check(res2, { 'login responds': (r) => r.status === 200 || r.status === 401 || r.status === 403 });

  const res3 = http.get(`${BASE_URL}/api/v1/home`, { timeout: '10s' });
  check(res3, { 'home responds': (r) => r.status === 200 || r.status === 401 || r.status === 403 });

  const res4 = http.get(`${BASE_URL}/api/v1/lawyers`, { timeout: '10s' });
  check(res4, { 'lawyers responds': (r) => r.status === 200 || r.status === 401 || r.status === 403 });

  const res5 = http.get(`${BASE_URL}/api/v1/forum/posts`, { timeout: '10s' });
  check(res5, { 'forum posts responds': (r) => r.status === 200 || r.status === 401 || r.status === 403 });

  const res6 = http.get(`${BASE_URL}/api/v1/news`, { timeout: '10s' });
  check(res6, { 'news responds': (r) => r.status === 200 || r.status === 401 || r.status === 403 });

  const res7 = http.get(`${BASE_URL}/api/v1/knowledge`, { timeout: '10s' });
  check(res7, { 'knowledge responds': (r) => r.status === 200 || r.status === 401 || r.status === 403 });

  sleep(1);
}
