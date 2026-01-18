import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 },
    { duration: '1m', target: 50 },
    { duration: '2m', target: 100 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
  },
};

export default function () {
  const syncRes = http.post('http://localhost/producer/sync');
  check(syncRes, {
    'Sync status is done': (r) => r.json().status === 'done',
  });

  const asyncRes = http.post('http://localhost/producer/async');
  check(asyncRes, {
    'Async status is message sent': (r) => r.json().status === 'message sent',
  });

  sleep(1);
}
