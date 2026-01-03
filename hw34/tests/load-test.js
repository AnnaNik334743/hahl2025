import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  scenarios: {
    high_traffic: {
      executor: 'constant-arrival-rate',
      rate: 300,
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

const endpoints = [
  { path: '/', weight: 1 },
  { path: '/datetime', weight: 3 },
  { path: '/date', weight: 2 },
  { path: '/time', weight: 2 },
];

function getRandomEndpoint() {
  const totalWeight = endpoints.reduce((sum, ep) => sum + ep.weight, 0);
  let random = Math.random() * totalWeight;
  
  for (const ep of endpoints) {
    random -= ep.weight;
    if (random <= 0) {
      return ep.path;
    }
  }
  return '/';
}

export default function () {
  const endpoint = getRandomEndpoint();
  const response = http.get(`${BASE_URL}${endpoint}`);
  sleep(0.01);
}