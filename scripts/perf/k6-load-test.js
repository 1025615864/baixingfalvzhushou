import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const healthLatency = new Trend('health_latency');
const loginLatency = new Trend('login_latency');
const homeLatency = new Trend('home_latency');
const lawyersLatency = new Trend('lawyers_latency');
const forumPostsLatency = new Trend('forum_posts_latency');
const newsLatency = new Trend('news_latency');
const knowledgeLatency = new Trend('knowledge_latency');

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TEST_USERNAME = __ENV.TEST_USERNAME || 'admin';
const TEST_PASSWORD = __ENV.TEST_PASSWORD || 'admin123';

export const options = {
  stages: [
    { duration: '1m', target: 10 },
    { duration: '2m', target: 100 },
    { duration: '2m', target: 500 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    errors: ['rate<0.05'],
    health_latency: ['p(95)<200'],
    login_latency: ['p(95)<500'],
    home_latency: ['p(95)<500'],
    lawyers_latency: ['p(95)<500'],
    forum_posts_latency: ['p(95)<500'],
    news_latency: ['p(95)<500'],
    knowledge_latency: ['p(95)<500'],
  },
  noConnectionReuse: false,
  userAgent: 'k6-load-test/1.0',
};

function authenticate() {
  const res = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ username: TEST_USERNAME, password: TEST_PASSWORD }),
    { headers: { 'Content-Type': 'application/json' }, timeout: '10s' }
  );
  const success = check(res, {
    'login status 200': (r) => r.status === 200,
    'has token': (r) => {
      try {
        const body = JSON.parse(r.body);
        return !!(body.data?.access_token || body.access_token || body.data?.token?.access_token);
      } catch {
        return false;
      }
    },
  });
  if (!success) {
    errorRate.add(1);
    return null;
  }
  const body = JSON.parse(res.body);
  return body.data?.access_token || body.access_token || body.data?.token?.access_token || null;
}

export default function () {
  const res1 = http.get(`${BASE_URL}/health`, { timeout: '5s' });
  healthLatency.add(res1.timings.duration);
  check(res1, { 'health status 200': (r) => r.status === 200 }) || errorRate.add(1);

  const token = authenticate();
  loginLatency.add(token ? 0 : 9999);

  if (!token) {
    sleep(1);
    return;
  }

  const authHeaders = {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    timeout: '10s',
  };

  const res2 = http.get(`${BASE_URL}/api/v1/home`, authHeaders);
  homeLatency.add(res2.timings.duration);
  check(res2, { 'home status ok': (r) => r.status >= 200 && r.status < 300 }) || errorRate.add(1);

  const res3 = http.get(`${BASE_URL}/api/v1/lawyers`, authHeaders);
  lawyersLatency.add(res3.timings.duration);
  check(res3, { 'lawyers status ok': (r) => r.status >= 200 && r.status < 300 }) || errorRate.add(1);

  const res4 = http.get(`${BASE_URL}/api/v1/forum/posts`, authHeaders);
  forumPostsLatency.add(res4.timings.duration);
  check(res4, { 'forum posts status ok': (r) => r.status >= 200 && r.status < 300 }) || errorRate.add(1);

  const res5 = http.get(`${BASE_URL}/api/v1/news`, authHeaders);
  newsLatency.add(res5.timings.duration);
  check(res5, { 'news status ok': (r) => r.status >= 200 && r.status < 300 }) || errorRate.add(1);

  const res6 = http.get(`${BASE_URL}/api/v1/knowledge`, authHeaders);
  knowledgeLatency.add(res6.timings.duration);
  check(res6, { 'knowledge status ok': (r) => r.status >= 200 && r.status < 300 }) || errorRate.add(1);

  sleep(Math.random() * 2 + 0.5);
}
