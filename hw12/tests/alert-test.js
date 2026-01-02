import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  scenarios: {
    high_traffic: {
      executor: 'constant-arrival-rate',
      rate: 500,
      timeUnit: '1s',
      duration: '2m',
      preAllocatedVUs: 50,
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500'],
  },
};

const BASE_URL = 'http://localhost:8000';

export default function () {
  const endpoints = ['/datetime', '/date', '/time'];
  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const response = http.get(`${BASE_URL}${endpoint}`);
  sleep(0.01);
}