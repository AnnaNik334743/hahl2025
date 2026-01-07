import http from 'k6/http';

export const options = {
  scenarios: {
    constant_500: {
      executor: 'constant-arrival-rate',
      rate: 500,
      timeUnit: '1s',
      duration: '3m',
      preAllocatedVUs: 200,
      maxVUs: 300,
    }
  }
};

const BASE_URL = 'http://localhost:8080';

function getRandomMonth() {
  return Math.floor(Math.random() * 12) + 1;
}

function getRandomDay() {
  return Math.floor(Math.random() * 31) + 1;
}

export default function () {
  const randomMonth = getRandomMonth();
  const randomDay = getRandomDay();
  const endpoint = `/holidays/${randomMonth}/${randomDay}`;
  const response = http.get(`${BASE_URL}${endpoint}`);
}