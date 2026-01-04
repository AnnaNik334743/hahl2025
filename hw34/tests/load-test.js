import http from 'k6/http';


export const options = {
  scenarios: {
    constant_1000: {
      executor: 'constant-arrival-rate',
      rate: 1000,
      timeUnit: '1s',
      duration: '2m',
      preAllocatedVUs: 200,
      maxVUs: 500,
    }
  },
  thresholds: {
    http_req_duration: ['p(95)<500'],
  },
};

const BASE_URL = 'http://localhost:8080';

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
}